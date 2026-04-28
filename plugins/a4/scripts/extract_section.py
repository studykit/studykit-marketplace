# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "xmlschema>=3.4"]
# ///
"""Read one section of an a4 markdown file without loading the whole file.

a4 bodies are sequences of column-0 ``<tag>...</tag>`` blocks (lowercase
kebab-case). For LLM-driven workflows it is often enough to read just
one section — the goal of this script.

Modes:

    extract_section.py <file> <tag>          # emit the section's body
                                             # markdown to stdout
    extract_section.py <file> --list         # list every section as
                                             # `<name>  line <N>`
    extract_section.py <file> <tag> --json   # structured object:
                                             # {name, content, open_line,
                                             #  close_line}

The scanner reused here is ``validate_body._scan_sections``; section
boundaries inside fenced code blocks are correctly ignored, matching
the validator's semantics. Exit codes:

    0 — section emitted (or list emitted, possibly empty).
    1 — invocation/IO error (file missing, conflicting flags, etc.).
    2 — section with the requested tag does not exist in the file.
    3 — file body has structural violations (stray content, unclosed
        tags, invalid tags). Stderr lists the violations; nothing on
        stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from markdown import extract_body
from validate_body import Section, _scan_sections


def _scan(path: Path) -> tuple[list[Section], list[str]]:
    body = extract_body(path)
    sections, violations = _scan_sections(
        body.content, body.line_start, str(path)
    )
    notes = [f"{v.path}:{v.line}: {v.rule}: {v.message}" for v in violations]
    return sections, notes


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


def cmd_emit(path: Path, tag: str, as_json: bool) -> int:
    sections, notes = _scan(path)
    if notes:
        for n in notes:
            sys.stderr.write(n + "\n")
        return 3
    match = next((s for s in sections if s.name == tag), None)
    if match is None:
        sys.stderr.write(
            f"ERROR: section <{tag}> not found in {path}. "
            f"Known sections: {', '.join(s.name for s in sections) or '(none)'}\n"
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
            "<file> <tag>, <file> --list, <file> <tag> --json."
        )
    )
    parser.add_argument("file", type=Path, help="path to an a4 markdown file")
    parser.add_argument(
        "tag",
        nargs="?",
        help="section tag (lowercase kebab-case). Required unless --list.",
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
        if args.tag or args.json:
            sys.stderr.write(
                "ERROR: --list is incompatible with <tag> / --json\n"
            )
            return 1
        return cmd_list(args.file)

    if not args.tag:
        sys.stderr.write("ERROR: <tag> is required (or pass --list)\n")
        return 1
    return cmd_emit(args.file, args.tag, args.json)


if __name__ == "__main__":
    sys.exit(main())
