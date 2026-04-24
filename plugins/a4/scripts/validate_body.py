# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Validate body-level Obsidian conventions across an a4/ workspace.

Enforces the body-side rules defined in plugins/a4/references/obsidian-conventions.md:

  - footnote-format         Wiki-page footnote definitions match the canonical
                            shape `[^N]: YYYY-MM-DD — [[target]]` (em dash is
                            U+2014, single-spaced).
  - footnote-sequence       Footnote labels are integers in strict monotonic
                            order starting at 1, in file order.
  - footnote-review-payload Footnote payload wikilinks the causing issue (UC,
                            task, decision, or architecture-section heading) —
                            never a `review/*` item.
  - wikilink-broken         Every body wikilink (wiki pages, issue bodies,
                            spark files) resolves to a file in the workspace.

Narrowly scoped on purpose. `drift_detector.py` already covers close-guard,
orphan-marker, orphan-definition, and missing-wiki-page rules at the
cross-session level; `validate_frontmatter.py` covers frontmatter-path format
and other frontmatter-side rules. This script covers the remaining body-level
syntax checks. Rules that depend on git history (e.g., `updated:` bump
consistency) or are high-false-positive (e.g., detecting frontmatter-format
paths accidentally typed into body prose) are intentionally out of scope.

All violations are errors. Exit code is 2 if any violation is found, else 0.

Usage:
    uv run validate_body.py <a4-dir>              # scan whole workspace
    uv run validate_body.py <a4-dir> <file>       # validate one file
    uv run validate_body.py <a4-dir> --json       # structured JSON output
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from common import WIKI_KINDS, split_frontmatter

ISSUE_FOLDERS = ("usecase", "task", "review", "decision")

FOOTNOTE_DEF_LINE_RE = re.compile(r"^\[\^([^\]\s]+)\]:\s*(.*)$")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")

# Canonical footnote definition: label, date, em dash (U+2014), wikilink, no trailing content.
FOOTNOTE_DEF_CANONICAL_RE = re.compile(
    r"^\[\^([^\]\s]+)\]:\s+(\d{4}-\d{2}-\d{2})\s+—\s+\[\[([^\]]+)\]\]\s*$"
)


@dataclass(frozen=True)
class Violation:
    path: str
    rule: str
    line: int | None
    message: str


def discover_wiki_pages(a4_dir: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for md in sorted(a4_dir.glob("*.md")):
        parsed = split_frontmatter(md)
        if parsed.fm and parsed.fm.get("kind") in WIKI_KINDS:
            out[md.stem] = md
    return out


def discover_issues(a4_dir: Path) -> dict[str, Path]:
    """Map both `<folder>/<stem>` and bare `<stem>` forms to issue paths."""
    out: dict[str, Path] = {}
    for folder in ISSUE_FOLDERS:
        sub = a4_dir / folder
        if not sub.is_dir():
            continue
        for md in sorted(sub.glob("*.md")):
            out[f"{folder}/{md.stem}"] = md
            out.setdefault(md.stem, md)
    return out


def discover_sparks(a4_dir: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    sub = a4_dir / "spark"
    if not sub.is_dir():
        return out
    for md in sorted(sub.glob("*.md")):
        out[f"spark/{md.stem}"] = md
        out.setdefault(md.stem, md)
    return out


def resolve_link(
    link: str,
    wikis: dict[str, Path],
    issues: dict[str, Path],
    sparks: dict[str, Path],
) -> Path | None:
    link = link.strip()
    if not link:
        return None
    if link in wikis:
        return wikis[link]
    if link in issues:
        return issues[link]
    if link in sparks:
        return sparks[link]
    return None


def is_review_link(link: str, issues: dict[str, Path]) -> bool:
    link = link.strip()
    if link.startswith("review/"):
        return True
    path = issues.get(link)
    if path is None:
        return False
    return path.parent.name == "review"


def classify_file(path: Path, a4_dir: Path, fm: dict | None) -> str | None:
    try:
        rel = path.relative_to(a4_dir)
    except ValueError:
        return None
    if len(rel.parts) < 2:
        if fm and fm.get("kind") in WIKI_KINDS:
            return "wiki"
        return None
    folder = rel.parts[0]
    if folder in ISSUE_FOLDERS:
        return "issue"
    if folder == "spark":
        return "spark"
    return None


def validate_wiki_footnotes(
    rel_str: str,
    body: str,
    body_start_line: int,
    wikis: dict[str, Path],
    issues: dict[str, Path],
    sparks: dict[str, Path],
) -> tuple[list[Violation], set[int]]:
    """Run footnote rules on a wiki-page body.

    Returns (violations, footnote_def_line_numbers). The caller uses the line
    number set to skip footnote-definition lines during the later generic
    wikilink sweep (so payload wikilinks aren't reported twice).
    """
    violations: list[Violation] = []
    definitions: list[tuple[int, str, str]] = []  # (abs_line_no, label, raw_line)
    def_lines: set[int] = set()

    for i, line in enumerate(body.splitlines()):
        m = FOOTNOTE_DEF_LINE_RE.match(line)
        if not m:
            continue
        abs_line = body_start_line + i
        definitions.append((abs_line, m.group(1), line))
        def_lines.add(abs_line)

    # Rule: canonical format on each definition line.
    for abs_line, label, raw in definitions:
        if not FOOTNOTE_DEF_CANONICAL_RE.match(raw):
            violations.append(Violation(
                rel_str,
                "footnote-format",
                abs_line,
                f"footnote definition `[^{label}]:` does not match the canonical "
                "shape `[^N]: YYYY-MM-DD — [[target]]` (em dash U+2014, "
                "single-spaced, no trailing content)",
            ))

    # Rule: integer monotonicity starting at 1, in file order.
    for position, (abs_line, label, _) in enumerate(definitions, start=1):
        if not label.isdigit():
            violations.append(Violation(
                rel_str,
                "footnote-sequence",
                abs_line,
                f"footnote label `[^{label}]` is not an integer; convention "
                "requires monotonic integers starting at 1",
            ))
            continue
        actual = int(label)
        if actual != position:
            violations.append(Violation(
                rel_str,
                "footnote-sequence",
                abs_line,
                f"footnote `[^{actual}]` at position {position}; expected "
                f"`[^{position}]` (monotonic integers starting at 1, in file order)",
            ))

    # Rule: payload wikilink is not a review item, and resolves.
    for abs_line, label, raw in definitions:
        m = FOOTNOTE_DEF_CANONICAL_RE.match(raw)
        if m:
            payload_links = [m.group(3)]
        else:
            # Format already flagged above; still try best-effort extraction so
            # review-payload and broken-link rules are not silently skipped.
            payload_links = WIKILINK_RE.findall(raw)

        for link in payload_links:
            bare = link.split("|")[0].split("#")[0].strip()
            if not bare:
                continue
            if is_review_link(bare, issues):
                violations.append(Violation(
                    rel_str,
                    "footnote-review-payload",
                    abs_line,
                    f"footnote `[^{label}]` wikilinks `[[{bare}]]` which is a "
                    "review item; payload must wikilink the causing issue "
                    "(UC, task, decision, or architecture-section heading)",
                ))
            if resolve_link(bare, wikis, issues, sparks) is None:
                violations.append(Violation(
                    rel_str,
                    "wikilink-broken",
                    abs_line,
                    f"footnote `[^{label}]` wikilinks `[[{bare}]]` which does "
                    "not resolve to any file in the workspace",
                ))

    return violations, def_lines


def validate_body_wikilinks(
    rel_str: str,
    body: str,
    body_start_line: int,
    wikis: dict[str, Path],
    issues: dict[str, Path],
    sparks: dict[str, Path],
    skip_lines: set[int],
) -> list[Violation]:
    violations: list[Violation] = []
    for i, line in enumerate(body.splitlines()):
        abs_line = body_start_line + i
        if abs_line in skip_lines:
            continue
        for link in WIKILINK_RE.findall(line):
            bare = link.split("|")[0].split("#")[0].strip()
            if not bare:
                continue
            if resolve_link(bare, wikis, issues, sparks) is None:
                violations.append(Violation(
                    rel_str,
                    "wikilink-broken",
                    abs_line,
                    f"wikilink `[[{bare}]]` does not resolve to any file in the workspace",
                ))
    return violations


def validate_file(
    path: Path,
    a4_dir: Path,
    wikis: dict[str, Path],
    issues: dict[str, Path],
    sparks: dict[str, Path],
) -> list[Violation]:
    parsed = split_frontmatter(path)
    ftype = classify_file(path, a4_dir, parsed.fm)
    if ftype is None:
        return []

    rel_str = str(path.relative_to(a4_dir))
    body = parsed.body
    body_start = parsed.body_start_line
    violations: list[Violation] = []
    skip_lines: set[int] = set()

    if ftype == "wiki":
        wiki_violations, skip_lines = validate_wiki_footnotes(
            rel_str, body, body_start, wikis, issues, sparks
        )
        violations.extend(wiki_violations)

    violations.extend(
        validate_body_wikilinks(
            rel_str, body, body_start, wikis, issues, sparks, skip_lines
        )
    )
    return violations


def discover_files(a4_dir: Path) -> list[Path]:
    out: list[Path] = list(sorted(a4_dir.glob("*.md")))
    for folder in ISSUE_FOLDERS:
        sub = a4_dir / folder
        if sub.is_dir():
            out.extend(sorted(sub.glob("*.md")))
    spark = a4_dir / "spark"
    if spark.is_dir():
        out.extend(sorted(spark.glob("*.md")))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate body-level Obsidian conventions across an a4/ workspace.",
    )
    parser.add_argument("a4_dir", type=Path, help="path to the a4/ workspace")
    parser.add_argument(
        "file", type=Path, nargs="?", help="validate a single file only"
    )
    parser.add_argument(
        "--json", action="store_true", help="emit structured JSON to stdout"
    )
    args = parser.parse_args()

    a4_dir = args.a4_dir.resolve()
    if not a4_dir.is_dir():
        print(f"Error: {a4_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    wikis = discover_wiki_pages(a4_dir)
    issues = discover_issues(a4_dir)
    sparks = discover_sparks(a4_dir)

    if args.file:
        target = args.file.resolve()
        try:
            target.relative_to(a4_dir)
        except ValueError:
            print(f"Error: {target} is not inside {a4_dir}", file=sys.stderr)
            sys.exit(1)
        files = [target]
    else:
        files = discover_files(a4_dir)

    violations: list[Violation] = []
    for path in files:
        violations.extend(validate_file(path, a4_dir, wikis, issues, sparks))

    if args.json:
        out = {
            "a4_dir": str(a4_dir),
            "scanned": [str(p.relative_to(a4_dir)) for p in files],
            "violations": [asdict(v) for v in violations],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        sys.exit(2 if violations else 0)

    if not violations:
        print(f"OK — {len(files)} file(s) scanned, no body-convention violations.")
        sys.exit(0)

    file_count = len({v.path for v in violations})
    print(
        f"{len(violations)} violation(s) across {file_count} file(s):",
        file=sys.stderr,
    )
    for v in violations:
        loc = v.path
        if v.line is not None:
            loc += f":{v.line}"
        print(f"  {loc} ({v.rule}): {v.message}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
