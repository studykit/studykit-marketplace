# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Unified validator entrypoint for an a4/ workspace.

Runs the two category validators in one process and emits a combined
report:

    validate_frontmatter           YAML schema, enum values, field types,
                                    path-reference format, wiki `type:`
                                    matches filename, `wiki_impact`
                                    targets, id uniqueness.
    validate_status_consistency    cross-file derived status
                                    (`superseded`, `promoted`, cascaded
                                    `discarded`). Workspace-only; skipped
                                    in single-file mode (same convention
                                    as `/a4:validate`).

Per-category CLI entrypoints remain available and unchanged — users
wanting a single class of check can still run `validate_frontmatter.py`
or `validate_status_consistency.py` directly.

Exit code is 2 if any category reports violations, else 0. Exit 1 for
usage errors (missing workspace, file not inside workspace).

Usage:
    uv run validate.py <a4-dir>
    uv run validate.py <a4-dir> <file>
    uv run validate.py <a4-dir> --json
    uv run validate.py <a4-dir> <file> --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import validate_frontmatter
import validate_status_consistency


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run all a4 validators (frontmatter + status consistency) in "
            "one pass."
        )
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

    target: Path | None = None
    file_rel: str | None = None
    if args.file:
        resolved = args.file.resolve()
        try:
            file_rel = str(resolved.relative_to(a4_dir))
        except ValueError:
            print(f"Error: {resolved} is not inside {a4_dir}", file=sys.stderr)
            sys.exit(1)
        target = resolved

    fm_violations, fm_scanned = validate_frontmatter.run(a4_dir, target)

    # Cross-file consistency is global — single-file mode skips it so the
    # user gets a stable workspace-scoped verdict from `/a4:validate`. A
    # --connected-component mode on the status validator exists (`--file`)
    # but is intentionally not surfaced here; run
    # `validate_status_consistency.py --file X` directly if needed.
    if target is None:
        status_mismatches = validate_status_consistency.run(a4_dir, None)
        status_skipped = False
    else:
        status_mismatches: list[validate_status_consistency.Mismatch] = []
        status_skipped = True

    total = len(fm_violations) + len(status_mismatches)
    exit_code = 2 if total else 0

    if args.json:
        out = {
            "a4_dir": str(a4_dir),
            "file": file_rel,
            "frontmatter": {
                "scanned": [str(p.relative_to(a4_dir)) for p in fm_scanned],
                "violations": [asdict(v) for v in fm_violations],
            },
            "status_consistency": {
                "skipped": status_skipped,
                "mismatches": [asdict(m) for m in status_mismatches],
            },
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        sys.exit(exit_code)

    _print_frontmatter(fm_violations, fm_scanned)
    _print_status(status_mismatches, status_skipped)

    sys.exit(exit_code)


def _print_frontmatter(
    violations: list[validate_frontmatter.Violation], scanned: list[Path]
) -> None:
    print("=== frontmatter ===")
    if not violations:
        print(f"OK — {len(scanned)} file(s) scanned, no violations.")
        return
    file_count = len({v.path for v in violations})
    print(
        f"{len(violations)} violation(s) across {file_count} file(s):",
        file=sys.stderr,
    )
    for v in violations:
        loc = v.path + (f" [{v.field}]" if v.field else "")
        print(f"  {loc} ({v.rule}): {v.message}", file=sys.stderr)


def _print_status(
    mismatches: list[validate_status_consistency.Mismatch], skipped: bool
) -> None:
    print("=== status consistency ===")
    if skipped:
        print(
            "  skipped (single-file mode; re-run without [file] for the "
            "workspace-wide check)"
        )
        return
    if not mismatches:
        print("OK — no status-consistency mismatches.")
        return
    print(
        f"{len(mismatches)} status-consistency mismatch(es):",
        file=sys.stderr,
    )
    for m in mismatches:
        print(f"  {m.path} ({m.rule}): {m.message}", file=sys.stderr)


if __name__ == "__main__":
    main()
