# /// script
# requires-python = ">=3.11"
# ///
"""Extract a heading section from a markdown file.

Given a file path and a heading text, prints the section starting at that
heading and ending before the next heading of equal or higher level. The
leading heading line is included so the output is a self-contained section.

Matches the first occurrence of the heading text. Heading matching is exact
(case-sensitive, whitespace-trimmed) against the heading content only (the
text after the `#` markers).

Usage:
    uv run extract_section.py <file> <heading>

Exit codes:
    0 — section found and written to stdout
    1 — file missing, heading not found, or usage error
"""

import re
import sys
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def heading_of(line: str) -> tuple[int, str] | None:
    match = HEADING_RE.match(line)
    if not match:
        return None
    return len(match.group(1)), match.group(2).strip()


def extract(text: str, heading: str) -> str | None:
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


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <file> <heading>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    heading = sys.argv[2]

    if not path.is_file():
        print(f"Error: {path} is not a file", file=sys.stderr)
        sys.exit(1)

    result = extract(path.read_text(encoding="utf-8"), heading)

    if result is None:
        print(f"Error: heading '{heading}' not found in {path}", file=sys.stderr)
        sys.exit(1)

    sys.stdout.write(result)


if __name__ == "__main__":
    main()
