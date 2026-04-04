"""Extract YAML frontmatter from a markdown file.

Usage:
    uv run read_frontmatter.py <file>            # all fields as JSON
    uv run read_frontmatter.py <file> <key>       # single field value
    uv run read_frontmatter.py <file> <key> <key>  # multiple fields
"""

import json
import sys
from pathlib import Path


def read_frontmatter(path: str) -> dict:
    lines: list[str] = []
    with open(path, encoding="utf-8") as f:
        first_line = f.readline()
        if first_line.strip() != "---":
            return {}
        for line in f:
            if line.strip() == "---":
                break
            lines.append(line)

    # Minimal YAML parser — handles flat scalars and simple lists.
    # Avoids requiring PyYAML as a dependency.
    result: dict = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # List item under current key
        if stripped.startswith("- ") and current_key is not None and current_list is not None:
            current_list.append(stripped[2:].strip().strip("\"'"))
            continue

        # New key
        if ":" in stripped:
            # Flush previous list
            if current_key is not None and current_list is not None:
                result[current_key] = current_list

            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()

            if value == "[]":
                result[key] = []
                current_key = None
                current_list = None
            elif value == "" or value == "":
                # Could be a list or multi-line — start collecting
                current_key = key
                current_list = []
            else:
                result[key] = value.strip("\"'")
                current_key = None
                current_list = None

    # Flush last key
    if current_key is not None and current_list is not None:
        result[current_key] = current_list

    return result


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file> [key ...]", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    if not Path(path).is_file():
        print(json.dumps({}))
        sys.exit(0)

    fm = read_frontmatter(path)

    keys = sys.argv[2:]
    if not keys:
        print(json.dumps(fm, ensure_ascii=False))
    elif len(keys) == 1:
        value = fm.get(keys[0])
        if isinstance(value, list):
            print(json.dumps(value, ensure_ascii=False))
        elif value is not None:
            print(value)
    else:
        subset = {k: fm.get(k) for k in keys if k in fm}
        print(json.dumps(subset, ensure_ascii=False))


if __name__ == "__main__":
    main()
