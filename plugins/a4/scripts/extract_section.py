# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Read one section of an a4 markdown file without loading the whole file.

a4 bodies are sequences of column-0 ``## Title Case`` headings (per
``plugins/a4/references/body-conventions.md``). For LLM-driven workflows
it is often enough to read just one section — the goal of this script.

Modes:

    extract_section.py <file> <name>          # emit the section's body
                                              # markdown to stdout
    extract_section.py <file> --list          # list every section as
                                              # `<heading>  line <N>`
    extract_section.py <file> <name> --json   # structured object:
                                              # {name, content, open_line,
                                              #  close_line}

The ``<name>`` argument may be passed in any of these forms — they
are all matched case-insensitively against each section's heading
after slugifying both sides:

    "Change Logs"   "change logs"   "Change-Logs"   "change-logs"

Section detection:

    ## <Heading>   ← column-0 H2, on its own line. Title Case is the
                     authoring convention but the scanner only requires
                     the H2 marker.

H2 lines inside fenced code blocks (``` or ~~~) are ignored. Anything
above the first H2 (other than whitespace) is reported as stray content.

Exit codes:

    0 — section emitted (or list emitted, possibly empty).
    1 — invocation/IO error (file missing, conflicting flags, etc.).
    2 — section with the requested name does not exist in the file.
    3 — file body has structural violations (stray content above the
        first heading, etc.). Stderr lists the violations; nothing on
        stdout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from markdown import extract_body

H2_RE = re.compile(r"^##\s+(\S.*?)\s*$")
FENCE_RE = re.compile(r"^(`{3,}|~{3,})")


@dataclass(frozen=True)
class Section:
    name: str
    content: str
    open_line: int
    close_line: int


@dataclass(frozen=True)
class Violation:
    line: int
    message: str


def _slugify(text: str) -> str:
    """Lowercase + non-alphanumerics → ``-``; collapse runs; strip ends.

    Used to match the user-supplied section name against actual
    headings, so all of ``Change Logs`` / ``change logs`` /
    ``Change-Logs`` / ``change-logs`` resolve to the same key.
    """
    out = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return out.strip("-")


def _scan_sections(
    body_text: str, body_start_line: int
) -> tuple[list[Section], list[Violation]]:
    """Walk ``body_text`` line by line and slice it on column-0 ``## ``."""
    lines = body_text.splitlines()
    n = len(lines)

    fence: str | None = None
    starts: list[tuple[int, str]] = []  # (line_index, heading_text)
    violations: list[Violation] = []

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        fence_match = FENCE_RE.match(stripped)
        if fence is None:
            if fence_match:
                fence = fence_match.group(1)[0] * 3
                continue
            m = H2_RE.match(line)
            if m:
                starts.append((i, m.group(1).strip()))
                continue
            if line.strip() and not starts:
                preview = line.strip()
                if len(preview) > 60:
                    preview = preview[:57] + "…"
                violations.append(
                    Violation(
                        body_start_line + i,
                        f"non-whitespace text above the first `## ` "
                        f"heading: {preview!r}",
                    )
                )
        else:
            if fence_match and stripped.startswith(fence):
                fence = None

    sections: list[Section] = []
    for idx, (start_i, heading) in enumerate(starts):
        end_i = starts[idx + 1][0] if idx + 1 < len(starts) else n
        # content = lines strictly between the heading line and the
        # next heading (exclusive of both). Trailing/leading blanks
        # within the slice are preserved.
        content_lines = lines[start_i + 1 : end_i]
        # Trim a trailing blank that came from the gap before the next
        # heading, but preserve internal blank lines.
        while content_lines and not content_lines[-1].strip():
            content_lines.pop()
        sections.append(
            Section(
                name=heading,
                content="\n".join(content_lines),
                open_line=body_start_line + start_i,
                close_line=body_start_line + (end_i - 1),
            )
        )
    return sections, violations


def _scan(path: Path) -> tuple[list[Section], list[str]]:
    body = extract_body(path)
    sections, violations = _scan_sections(body.content, body.line_start)
    notes = [f"{path}:{v.line}: {v.message}" for v in violations]
    return sections, notes


def _find(sections: list[Section], query: str) -> Section | None:
    key = _slugify(query)
    if not key:
        return None
    for s in sections:
        if _slugify(s.name) == key:
            return s
    return None


def cmd_list(path: Path) -> int:
    sections, notes = _scan(path)
    if notes:
        for n in notes:
            sys.stderr.write(n + "\n")
        return 3
    if not sections:
        return 0
    pad = max(len(s.name) for s in sections)
    for s in sections:
        print(f"{s.name.ljust(pad)}  line {s.open_line}")
    return 0


def cmd_emit(path: Path, name: str, as_json: bool) -> int:
    sections, notes = _scan(path)
    if notes:
        for n in notes:
            sys.stderr.write(n + "\n")
        return 3
    match = _find(sections, name)
    if match is None:
        sys.stderr.write(
            f"ERROR: section `## {name}` not found in {path}. "
            f"Known sections: "
            f"{', '.join(s.name for s in sections) or '(none)'}\n"
        )
        return 2
    if as_json:
        json.dump(
            {
                "name": match.name,
                "content": match.content,
                "open_line": match.open_line,
                "close_line": match.close_line,
            },
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        sys.stdout.write(match.content)
        if match.content and not match.content.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract one section of an a4 markdown file. Modes: "
            "<file> <name>, <file> --list, <file> <name> --json. "
            "Section names are matched case-insensitively after "
            "slugifying both the heading and the query."
        )
    )
    parser.add_argument("file", type=Path, help="path to an a4 markdown file")
    parser.add_argument(
        "name",
        nargs="?",
        help=(
            "section name. Either the Title Case heading "
            "(e.g., `Change Logs`) or the kebab-case slug "
            "(e.g., `change-logs`). Required unless --list."
        ),
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list every section in the file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the requested section as JSON",
    )
    args = parser.parse_args()

    if not args.file.is_file():
        sys.stderr.write(f"ERROR: file not found: {args.file}\n")
        return 1

    if args.list:
        if args.name or args.json:
            sys.stderr.write(
                "ERROR: --list is incompatible with <name> / --json\n"
            )
            return 1
        return cmd_list(args.file)

    if not args.name:
        sys.stderr.write("ERROR: <name> is required (or pass --list)\n")
        return 1
    return cmd_emit(args.file, args.name, args.json)


if __name__ == "__main__":
    sys.exit(main())
