# /// script
# requires-python = ">=3.11"
# ///
"""Expand Obsidian embed directives in a markdown file with inline content.

Scans for `![[path#heading]]` (section embed) or `![[path]]` (whole-file embed)
directives and replaces each with the referenced content wrapped in HTML
comment markers for audit trail. Write-time transformation — the expanded
file is self-contained and independent of future changes in the referenced
files, preserving snapshot semantics.

Non-embed wikilinks (`[[...]]` without leading `!`) are plain references and
are left untouched.

Each injection is wrapped as:
    <!-- injected: <path>#<heading> @ <date> -->
    <content>
    <!-- /injected -->

Paths in directives are resolved against <base-dir> (default: cwd). Obsidian
wikilinks may omit the `.md` suffix; it is appended automatically when the
target has no extension.

Usage:
    uv run inject_includes.py <input-file> [--base-dir <dir>] [--date <ISO-date>]

Output is written to stdout.

Exit codes:
    0 — all directives resolved, expanded content on stdout
    1 — missing input file, missing referenced file, or missing heading
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

EMBED_RE = re.compile(r"!\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|[^\]]+)?\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def heading_of(line: str) -> tuple[int, str] | None:
    match = HEADING_RE.match(line)
    if not match:
        return None
    return len(match.group(1)), match.group(2).strip()


def extract_section(text: str, heading: str) -> str | None:
    lines = text.splitlines(keepends=True)
    start: int | None = None
    start_level = 0

    for i, line in enumerate(lines):
        parsed = heading_of(line)
        if parsed is not None and parsed[1] == heading:
            start = i
            start_level = parsed[0]
            break

    if start is None:
        return None

    end = len(lines)
    for j in range(start + 1, len(lines)):
        parsed = heading_of(lines[j])
        if parsed is not None and parsed[0] <= start_level:
            end = j
            break

    return "".join(lines[start:end])


def resolve_path(raw: str, base: Path) -> Path:
    p = Path(raw)
    if p.suffix == "":
        p = p.with_suffix(".md")
    return base / p


def inject(text: str, base_dir: Path, today: str) -> str:
    def replace(match: re.Match) -> str:
        raw_path = match.group(1).strip()
        heading = match.group(2).strip() if match.group(2) else None
        resolved = resolve_path(raw_path, base_dir)

        if not resolved.is_file():
            raise FileNotFoundError(
                f"referenced file not found: {resolved} (from directive {match.group(0)})"
            )

        content = resolved.read_text(encoding="utf-8")
        if heading is not None:
            extracted = extract_section(content, heading)
            if extracted is None:
                raise ValueError(f"heading '{heading}' not found in {resolved}")
            body = extracted.rstrip("\n")
            spec = f"{raw_path}#{heading}"
        else:
            body = content.rstrip("\n")
            spec = raw_path

        return f"<!-- injected: {spec} @ {today} -->\n{body}\n<!-- /injected -->"

    return EMBED_RE.sub(replace, text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand Obsidian embed directives.")
    parser.add_argument("input", type=Path, help="markdown file with ![[...]] directives")
    parser.add_argument("--base-dir", type=Path, default=Path.cwd(), help="base for resolving paths (default: cwd)")
    parser.add_argument("--date", default=date.today().isoformat(), help="injection date (default: today)")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Error: {args.input} is not a file", file=sys.stderr)
        sys.exit(1)

    text = args.input.read_text(encoding="utf-8")

    try:
        expanded = inject(text, args.base_dir, args.date)
    except (FileNotFoundError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)

    sys.stdout.write(expanded)


if __name__ == "__main__":
    main()
