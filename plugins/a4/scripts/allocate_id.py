#!/usr/bin/env python3
"""Compute the next globally-unique id for an a4/ workspace.

Scans all issue files across the canonical issue folders (usecase/,
task/, bug/, spike/, research/, epic/, review/, spec/, idea/,
brainstorm/) for filenames of the form ``<id>-<slug>.md`` and returns
``max(id) + 1``. Filenames are the source of truth for id allocation —
the validator (`/a4:validate`) independently verifies that each file's
frontmatter ``id:`` matches its filename, so the two stay in lockstep.

No state file, always computed fresh — this is the semantic guarantee
that ids remain monotonically increasing and globally unique across
the workspace.

Usage:
    allocate_id.py <a4-dir>              # print next id
    allocate_id.py <a4-dir> --list       # list all existing ids (id\tpath)
    allocate_id.py <a4-dir> --check      # verify uniqueness; exits 1 on duplicates
"""

import re
import sys
from pathlib import Path

from common import ISSUE_FOLDERS, iter_issue_files

_ID_RE = re.compile(r"^(\d+)-")


def extract_id(path: Path) -> int | None:
    m = _ID_RE.match(path.stem)
    return int(m.group(1)) if m else None


def collect_ids(a4_dir: Path) -> list[tuple[int, Path]]:
    results: list[tuple[int, Path]] = []
    for folder in ISSUE_FOLDERS:
        for md in iter_issue_files(a4_dir, folder):
            id_value = extract_id(md)
            if id_value is not None:
                results.append((id_value, md))
    return results


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <a4-dir> [--list|--check]", file=sys.stderr)
        sys.exit(1)

    a4_dir = Path(sys.argv[1])
    if not a4_dir.is_dir():
        print(f"Error: {a4_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    ids = collect_ids(a4_dir)
    flag = sys.argv[2] if len(sys.argv) > 2 else None

    if flag == "--list":
        for id_value, path in sorted(ids):
            print(f"{id_value}\t{path.relative_to(a4_dir)}")
        return

    if flag == "--check":
        seen: dict[int, list[Path]] = {}
        for id_value, path in ids:
            seen.setdefault(id_value, []).append(path)
        duplicates = {k: v for k, v in seen.items() if len(v) > 1}
        if duplicates:
            for id_value, paths in sorted(duplicates.items()):
                joined = ", ".join(str(p.relative_to(a4_dir)) for p in paths)
                print(f"duplicate id {id_value}: {joined}", file=sys.stderr)
            sys.exit(1)
        return

    next_id = max((i for i, _ in ids), default=0) + 1
    print(next_id)


if __name__ == "__main__":
    main()
