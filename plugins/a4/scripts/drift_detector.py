# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Detect drift between wiki pages and issue state in an a4/ workspace.

The drift detector implements the wiki+issues invariant that wiki page
footnotes track every substantive issue change. It scans a4/ wiki pages
and a4/{usecase,task,review,spec}/ issue files, then emits review items
with `source: drift-detector` for each detected drift.

Wiki normalization (runs before detection):
  - missing `## Changes` heading on a wiki page is auto-appended; the
    section is left empty for subsequent edits to populate.

Detection rules:
  - close-guard       Resolved review item declares a `wiki_impact` page,
                      but the named wiki page has no footnote citing the
                      causing issue (the review item's `target`).
  - stale-footnote    A footnote definition's wikilink resolves to a
                      non-existent issue or wiki page.
  - orphan-marker     Inline `[^N]` marker without a corresponding entry
                      in the `## Changes` section.
  - orphan-definition `## Changes` entry without a corresponding inline
                      `[^N]` marker.
  - missing-wiki-page A `wiki_impact` entry names a wiki page that does
                      not exist at the workspace root.
  - missing-spec-cite Architecture-only. A live `## Changes` footnote
                      records a change without citing any `spec/*`
                      spec. Resolution: cite the spec, author one, or
                      discard with rationale.

Detected drifts are deduplicated against existing review items with the
same (kind, target, cause) fingerprint when those items are still open,
in-progress, or discarded. Resolved items are not blockers — if drift is
re-detected after a resolution, that resolution did not actually fix it.

Usage:
    uv run drift_detector.py <a4-dir>             # write review items
    uv run drift_detector.py <a4-dir> --dry-run   # detect only, no writes
    uv run drift_detector.py <a4-dir> --json      # structured output
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import yaml

from common import WIKI_KINDS
from markdown import extract_body, extract_preamble

# Local ISSUE_FOLDERS diverges from `common.ISSUE_FOLDERS` (which includes
# `"idea"`). Preserved verbatim from pre-shared-module behavior — widening
# to include `idea/` changes wikilink-resolution and next-id semantics and
# belongs in a separate loud commit, not in this refactor.
ISSUE_FOLDERS = ("usecase", "task", "review", "spec")
DEDUP_BLOCKING_STATUSES = {"open", "in-progress", "discarded"}

INLINE_FOOTNOTE_RE = re.compile(r"\[\^([^\]\s]+)\](?!:)")
DEFINITION_FOOTNOTE_RE = re.compile(r"^\[\^([^\]\s]+)\]:\s*(.*)$", re.MULTILINE)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
SLUG_NON_WORD_RE = re.compile(r"[^a-z0-9]+")

KIND_TO_REVIEW_KIND = {
    "stale-footnote": "finding",
    "orphan-marker": "finding",
    "orphan-definition": "finding",
    "close-guard": "gap",
    "missing-wiki-page": "gap",
    "missing-spec-cite": "gap",
}

KIND_TO_PRIORITY = {
    "stale-footnote": "medium",
    "orphan-marker": "low",
    "orphan-definition": "low",
    "close-guard": "high",
    "missing-wiki-page": "high",
    "missing-spec-cite": "medium",
}

KIND_TO_TITLE = {
    "stale-footnote": "Stale wiki footnote",
    "orphan-marker": "Orphan footnote marker",
    "orphan-definition": "Orphan footnote definition",
    "close-guard": "Wiki close-guard violation",
    "missing-wiki-page": "Missing wiki page",
    "missing-spec-cite": "Missing spec citation",
}


@dataclass(frozen=True)
class Drift:
    kind: str
    wiki: str
    detail: str
    cause: str | None  # path-like reference to the causing issue or wiki, when known


def _fm(path: Path) -> dict:
    """Return `path`'s preamble as a dict, or `{}` on absence / parse error.

    Preserves the pre-shared-module `split_frontmatter(path)[0]` contract:
    every caller `.get()`s fields and tolerates an empty mapping.
    """
    return extract_preamble(path).fm or {}


def discover_wiki_pages(a4_dir: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for md in sorted(a4_dir.glob("*.md")):
        if _fm(md).get("kind") in WIKI_KINDS:
            out[md.stem] = md
    return out


def discover_issues(a4_dir: Path) -> dict[str, Path]:
    """Map both `<folder>/<stem>` and bare `<stem>` to issue paths."""
    out: dict[str, Path] = {}
    for folder in ISSUE_FOLDERS:
        sub = a4_dir / folder
        if not sub.is_dir():
            continue
        for md in sorted(sub.glob("*.md")):
            out[f"{folder}/{md.stem}"] = md
            out.setdefault(md.stem, md)
    return out


def parse_footnotes(text: str) -> tuple[set[str], dict[str, str]]:
    definitions: dict[str, str] = {}
    for m in DEFINITION_FOOTNOTE_RE.finditer(text):
        definitions[m.group(1)] = m.group(2).strip()

    inline: set[str] = set()
    for line in text.splitlines():
        if DEFINITION_FOOTNOTE_RE.match(line):
            continue
        for m in INLINE_FOOTNOTE_RE.finditer(line):
            inline.add(m.group(1))
    return inline, definitions


def parse_wikilinks(text: str) -> list[str]:
    return WIKILINK_RE.findall(text)


def resolve_wikilink(link: str, issues: dict[str, Path], wikis: dict[str, Path]) -> str | None:
    """Return canonical `<folder>/<stem>` or `<wiki-name>` form, or None if unresolvable."""
    link = link.strip()
    if not link:
        return None
    if link in wikis:
        return link
    if link in issues:
        path = issues[link]
        return f"{path.parent.name}/{path.stem}"
    return None


def ensure_changes_section(path: Path, dry_run: bool = False) -> bool:
    """Append a `## Changes` heading to `path` when it is missing.

    Returns True when the heading was missing (i.e., the page was — or, in
    `dry_run`, would have been — auto-fixed). The appended section is left
    empty so subsequent edits can populate it via the standard footnote
    protocol.
    """
    text = path.read_text(encoding="utf-8")
    if re.search(r"^##\s+Changes\s*$", text, re.MULTILINE):
        return False
    if not dry_run:
        path.write_text(text.rstrip() + "\n\n## Changes\n", encoding="utf-8")
    return True


def detect_wiki_drift(
    name: str,
    path: Path,
    issues: dict[str, Path],
    wikis: dict[str, Path],
) -> list[Drift]:
    drifts: list[Drift] = []
    body = extract_body(path).content

    inline, definitions = parse_footnotes(body)

    for label in sorted(inline - definitions.keys()):
        drifts.append(Drift(
            kind="orphan-marker",
            wiki=name,
            detail=f"inline footnote `[^{label}]` has no `## Changes` entry",
            cause=None,
        ))

    for label in sorted(definitions.keys() - inline):
        drifts.append(Drift(
            kind="orphan-definition",
            wiki=name,
            detail=f"`## Changes` defines `[^{label}]:` but no inline `[^{label}]` marker exists",
            cause=None,
        ))

    for label in sorted(definitions.keys() & inline):
        links = parse_wikilinks(definitions[label])
        has_spec_cite = False
        for link in links:
            resolved = resolve_wikilink(link, issues, wikis)
            if resolved is None:
                drifts.append(Drift(
                    kind="stale-footnote",
                    wiki=name,
                    detail=(
                        f"footnote `[^{label}]` references `[[{link}]]` which does "
                        "not exist in the workspace"
                    ),
                    cause=link,
                ))
            elif resolved.startswith("spec/"):
                has_spec_cite = True

        if name == "architecture" and not has_spec_cite:
            drifts.append(Drift(
                kind="missing-spec-cite",
                wiki=name,
                detail=(
                    f"`## Changes [^{label}]` records a change without citing a "
                    "`spec/*` spec."
                ),
                cause=f"footnote-{label}",
            ))

    return drifts


def detect_close_guard_drift(a4_dir: Path, wikis: dict[str, Path]) -> list[Drift]:
    drifts: list[Drift] = []
    review_dir = a4_dir / "review"
    if not review_dir.is_dir():
        return drifts

    for path in sorted(review_dir.glob("*.md")):
        fm = _fm(path)
        if fm.get("status") != "resolved":
            continue
        wiki_impact = fm.get("wiki_impact") or []
        if not isinstance(wiki_impact, list) or not wiki_impact:
            continue
        target = fm.get("target")
        if not isinstance(target, str) or not target:
            # cross-cutting review without a target — cause is ambiguous; skip
            continue
        target_basename = target.rsplit("/", 1)[-1]

        for wiki_name in wiki_impact:
            if not isinstance(wiki_name, str):
                continue

            wiki_path = wikis.get(wiki_name)
            if wiki_path is None:
                drifts.append(Drift(
                    kind="missing-wiki-page",
                    wiki=wiki_name,
                    detail=(
                        f"resolved `review/{path.stem}` declares "
                        f"`wiki_impact: [{wiki_name}]` but `{wiki_name}.md` does not exist"
                    ),
                    cause=target,
                ))
                continue

            body = extract_body(wiki_path).content
            _, definitions = parse_footnotes(body)
            cited = False
            for fbody in definitions.values():
                for link in parse_wikilinks(fbody):
                    if link == target or link == target_basename:
                        cited = True
                        break
                if cited:
                    break

            if not cited:
                drifts.append(Drift(
                    kind="close-guard",
                    wiki=wiki_name,
                    detail=(
                        f"resolved `review/{path.stem}` declares "
                        f"`wiki_impact: [{wiki_name}]` but `{wiki_name}.md` has no "
                        f"footnote citing `[[{target}]]`"
                    ),
                    cause=target,
                ))

    return drifts


def slugify(text: str) -> str:
    return SLUG_NON_WORD_RE.sub("-", text.lower()).strip("-")[:60] or "drift"


def fingerprint(drift: Drift) -> tuple[str, str, str | None]:
    cause = slugify(drift.cause) if drift.cause else None
    return (drift.kind, drift.wiki, cause)


def existing_fingerprints(a4_dir: Path) -> set[tuple[str, str, str | None]]:
    out: set[tuple[str, str, str | None]] = set()
    review_dir = a4_dir / "review"
    if not review_dir.is_dir():
        return out
    for path in review_dir.glob("*.md"):
        fm = _fm(path)
        if fm.get("source") != "drift-detector":
            continue
        if fm.get("status") not in DEDUP_BLOCKING_STATUSES:
            continue
        labels = fm.get("labels") or []
        if not isinstance(labels, list):
            continue
        drift_kind: str | None = None
        cause: str | None = None
        for label in labels:
            if not isinstance(label, str):
                continue
            if label.startswith("drift:"):
                drift_kind = label[len("drift:"):]
            elif label.startswith("drift-cause:"):
                cause = label[len("drift-cause:"):]
        target = fm.get("target")
        if drift_kind and isinstance(target, str):
            out.add((drift_kind, target, cause))
    return out


def compute_next_id(a4_dir: Path) -> int:
    max_id = 0
    for folder in ISSUE_FOLDERS:
        sub = a4_dir / folder
        if not sub.is_dir():
            continue
        for md in sub.glob("*.md"):
            raw = _fm(md).get("id")
            if isinstance(raw, int):
                max_id = max(max_id, raw)
    return max_id + 1


def build_review_item(drift: Drift, item_id: int, today: str) -> tuple[str, str]:
    """Return (filename, content) for a new review item."""
    cause_slug = slugify(drift.cause) if drift.cause else None
    slug_seed = f"drift {drift.kind} {drift.wiki}"
    if cause_slug:
        slug_seed += f" {cause_slug}"
    slug = slugify(slug_seed)
    filename = f"{item_id}-{slug}.md"

    labels = ["drift", f"drift:{drift.kind}"]
    if cause_slug:
        labels.append(f"drift-cause:{cause_slug}")

    fm = {
        "id": item_id,
        "kind": KIND_TO_REVIEW_KIND.get(drift.kind, "finding"),
        "status": "open",
        "target": drift.wiki,
        "source": "drift-detector",
        "wiki_impact": [drift.wiki],
        "priority": KIND_TO_PRIORITY.get(drift.kind, "medium"),
        "labels": labels,
        "created": today,
        "updated": today,
    }
    fm_yaml = yaml.safe_dump(
        fm, sort_keys=False, default_flow_style=None, allow_unicode=True
    ).rstrip()

    title = KIND_TO_TITLE.get(drift.kind, "Drift detected")
    body_lines = [
        f"# {title}: `{drift.wiki}`",
        "",
        "## Summary",
        "",
        drift.detail,
        "",
        "## Suggested Resolution",
        "",
    ]

    if drift.kind == "close-guard":
        body_lines += [
            f"Add a footnote in the relevant section of `{drift.wiki}.md` whose",
            f"`## Changes` payload wikilinks `[[{drift.cause}]]`. If the wiki page",
            "actually does not need updating for this resolution, switch the",
            "originating review item to `discarded` and document why in its `## Log`.",
        ]
    elif drift.kind == "missing-wiki-page":
        body_lines += [
            f"Either create `{drift.wiki}.md` (with the proper `kind:` frontmatter)",
            f"and add a footnote citing `[[{drift.cause}]]`, or amend the originating",
            "review item's `wiki_impact` field to remove this entry.",
        ]
    elif drift.kind == "stale-footnote":
        body_lines += [
            f"Footnote refers to `[[{drift.cause}]]` which no longer exists. Either",
            "re-point the footnote to the renamed/moved issue, replace the citation",
            "with the current canonical issue, or remove the footnote (and its inline",
            "marker) if the underlying claim is no longer relevant.",
        ]
    elif drift.kind == "missing-spec-cite":
        body_lines += [
            "Three resolution paths — pick one:",
            "",
            "1. **Spec already exists.** If a spec in `spec/` already records this",
            f"   change, add `[[spec/<id>-<slug>]]` to the relevant footnote in",
            f"   `{drift.wiki}.md`'s `## Changes` section, then set this review's",
            "   status to `resolved`.",
            "",
            "2. **Spec needed.** Run `/a4:spec` to author one, then cite it from",
            "   the footnote and set status to `resolved`.",
            "",
            "3. **No spec warranted.** If this change is routine (framework-mandated,",
            "   library swap with no architectural choice, post-hoc description, etc.),",
            "   set status to `discarded` and record the rationale in `## Log`. The",
            "   detector will not re-emit for the same footnote once discarded.",
        ]
    else:  # orphan-marker / orphan-definition
        body_lines += [
            f"Reconcile the footnote markers and `## Changes` definitions in `{drift.wiki}.md`.",
            "Either add the missing definition / inline marker, or delete the orphan",
            "reference.",
        ]

    body_lines += [
        "",
        "## Log",
        "",
        f"- {today} — opened by drift-detector",
        "",
    ]

    content = f"---\n{fm_yaml}\n---\n\n" + "\n".join(body_lines)
    return filename, content


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect drift between wiki pages and issue state in an a4/ workspace."
    )
    parser.add_argument("a4_dir", type=Path, help="path to the a4/ workspace")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="detect drift only; do not write review items",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit structured JSON to stdout",
    )
    args = parser.parse_args()

    a4_dir = args.a4_dir.resolve()
    if not a4_dir.is_dir():
        print(f"Error: {a4_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    wikis = discover_wiki_pages(a4_dir)
    issues = discover_issues(a4_dir)
    issue_files = {p for p in issues.values()}

    auto_fixed: list[str] = []
    for name, path in sorted(wikis.items()):
        if ensure_changes_section(path, dry_run=args.dry_run):
            auto_fixed.append(name)

    drifts: list[Drift] = []
    for name, path in sorted(wikis.items()):
        drifts.extend(detect_wiki_drift(name, path, issues, wikis))
    drifts.extend(detect_close_guard_drift(a4_dir, wikis))

    # Self-dedup within a single run.
    seen: set[tuple[str, str, str | None]] = set()
    unique: list[Drift] = []
    for d in drifts:
        fp = fingerprint(d)
        if fp in seen:
            continue
        seen.add(fp)
        unique.append(d)

    existing = existing_fingerprints(a4_dir)
    new_drifts = [d for d in unique if fingerprint(d) not in existing]

    written: list[Path] = []
    if not args.dry_run and new_drifts:
        next_id = compute_next_id(a4_dir)
        review_dir = a4_dir / "review"
        review_dir.mkdir(parents=True, exist_ok=True)
        today = date.today().isoformat()
        for d in new_drifts:
            filename, content = build_review_item(d, next_id, today)
            target = review_dir / filename
            target.write_text(content, encoding="utf-8")
            written.append(target)
            next_id += 1

    if args.json:
        out = {
            "a4_dir": str(a4_dir),
            "scanned_wikis": sorted(wikis.keys()),
            "scanned_issues": len(issue_files),
            "auto_fixed_wikis": auto_fixed,
            "all_detected": len(unique),
            "deduped_existing": len(unique) - len(new_drifts),
            "new_drifts": [asdict(d) for d in new_drifts],
            "written": [str(p.relative_to(a4_dir)) for p in written],
            "dry_run": args.dry_run,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    print(
        f"Scanned {len(wikis)} wiki page(s) and {len(issue_files)} issue file(s)."
    )
    if auto_fixed:
        verb = "would auto-fix" if args.dry_run else "auto-fixed"
        print(
            f"{verb} {len(auto_fixed)} wiki page(s) "
            f"(appended missing `## Changes` heading): {', '.join(auto_fixed)}"
        )
    print(
        f"Detected {len(unique)} drift(s); "
        f"{len(unique) - len(new_drifts)} already tracked by an existing review item."
    )

    if not new_drifts:
        print("No new drift to report.")
        return

    if args.dry_run:
        for d in new_drifts:
            cause_str = f" (cause: {d.cause})" if d.cause else ""
            print(f"  [{d.kind}] {d.wiki}{cause_str}: {d.detail}")
        return

    print(f"Wrote {len(written)} review item(s):")
    for p in written:
        print(f"  {p.relative_to(a4_dir)}")


if __name__ == "__main__":
    main()
