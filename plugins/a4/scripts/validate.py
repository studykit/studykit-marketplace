# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Unified validator entrypoint for an a4/ workspace.

Runs every registered check in ``markdown_validator.registry.CHECKS``
against the workspace (or against a specific file set) and emits a
combined report. With ``--fix``, also runs the supersedes-chain
recovery sweep before reporting — recovery path for edits that
bypassed the PostToolUse cascade hook.

Selectors:

  - No flag  — run every registered check.
  - --only A,B  — run only the named checks.
  - --skip A    — run every check except those named.
  - --list-checks — list registered checks and exit.

File scope:

  - 0 files     — workspace mode for every enabled check.
  - 1+ files    — file-scope mode for checks that support it; checks
                  that do not support file scope are skipped silently.
                  Issues are deduplicated when multiple files share a
                  connected component (e.g. specs in a supersedes
                  chain).

Recovery sweep:

  - --fix       — workspace-only. Walk usecase @ ``shipped`` / spec @
                  ``active`` files carrying ``supersedes:`` and flip
                  same-family predecessors to ``superseded``.
                  Idempotent. Combine with ``--dry-run`` to preview.

Designed to be drop-in usable for a git pre-commit hook: the hook
passes the staged ``a4/**/*.md`` paths after ``<a4-dir>`` and lets the
selector flags scope the work. ``--json`` produces machine-readable
output for CI parsing.

Exit code:
  0  — all enabled checks clean (and sweep had no errors when --fix).
  1  — semantic usage error (missing workspace dir, file outside the
       workspace, missing file, --fix combined with file args).
  2  — at least one issue reported, sweep surfaced an error, or
       argparse-detected malformed CLI (unknown flag, unknown check
       name, etc.).

Usage:
    uv run validate.py <a4-dir>
    uv run validate.py <a4-dir> <file> [<file> ...]
    uv run validate.py <a4-dir> --only frontmatter
    uv run validate.py <a4-dir> --skip status --json
    uv run validate.py <a4-dir> --fix [--dry-run] [--json]
    uv run validate.py --list-checks
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

# Ensure the package is importable when run via `uv run script.py`.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from markdown_validator import CHECKS, Issue  # noqa: E402
from status_cascade import Report, apply_supersedes_sweep  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run a4 workspace validators (frontmatter + status consistency "
            "by default). With --fix, also run the supersedes-chain "
            "recovery sweep."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  validate.py path/to/a4\n"
            "  validate.py path/to/a4 path/to/a4/spec/8-x.md\n"
            "  validate.py path/to/a4 --only frontmatter\n"
            "  validate.py path/to/a4 --skip status --json\n"
            "  validate.py path/to/a4 --fix\n"
            "  validate.py path/to/a4 --fix --dry-run --json\n"
            "  validate.py --list-checks\n"
        ),
    )
    parser.add_argument(
        "a4_dir", type=Path, nargs="?", help="path to the a4/ workspace"
    )
    parser.add_argument(
        "files",
        type=Path,
        nargs="*",
        help="restrict to these files (file-scope checks only)",
    )
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help=f"comma-separated subset of {sorted(CHECKS)}",
    )
    parser.add_argument(
        "--skip",
        type=str,
        default=None,
        help=f"comma-separated subset of {sorted(CHECKS)} to skip",
    )
    parser.add_argument(
        "--list-checks",
        action="store_true",
        help="list registered checks and exit",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help=(
            "run the supersedes-chain recovery sweep (workspace-only) "
            "before reporting checks"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="with --fix, report planned sweep changes without writing",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit structured JSON to stdout"
    )
    args = parser.parse_args()

    if args.list_checks:
        for name, check in CHECKS.items():
            scope = "workspace+file" if check.supports_file_scope else "workspace-only"
            print(f"{name} [{scope}] — {check.description}")
        sys.exit(0)

    if args.a4_dir is None:
        parser.error("a4_dir is required (unless --list-checks)")

    if args.dry_run and not args.fix:
        parser.error("--dry-run requires --fix")

    a4_dir = args.a4_dir.resolve()
    if not a4_dir.is_dir():
        print(f"Error: {a4_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    files: list[Path] = []
    for raw in args.files:
        resolved = raw.resolve()
        if not resolved.is_file():
            print(f"Error: {resolved} is not a file", file=sys.stderr)
            sys.exit(1)
        try:
            resolved.relative_to(a4_dir)
        except ValueError:
            print(f"Error: {resolved} is not inside {a4_dir}", file=sys.stderr)
            sys.exit(1)
        files.append(resolved)

    if args.fix and files:
        print(
            "Error: --fix is workspace-only; remove file arguments",
            file=sys.stderr,
        )
        sys.exit(1)

    enabled = _resolve_selection(parser, args.only, args.skip)

    fix_reports: list[Report] = []
    if args.fix:
        fix_reports = apply_supersedes_sweep(a4_dir, dry_run=args.dry_run)

    file_rels = [str(f.relative_to(a4_dir)) for f in files]
    results: dict[str, list[Issue]] = {}
    skipped: list[str] = []

    for name in CHECKS:  # preserve registration order
        if name not in enabled:
            continue
        check = CHECKS[name]
        if files:
            if not check.supports_file_scope:
                skipped.append(name)
                results[name] = []
                continue
            seen: set[tuple[str, str, str | None, str]] = set()
            collected: list[Issue] = []
            for f in files:
                for issue in check.run_file(a4_dir, f):
                    key = (issue.path, issue.rule, issue.field, issue.message)
                    if key in seen:
                        continue
                    seen.add(key)
                    collected.append(issue)
            results[name] = collected
        else:
            results[name] = check.run_workspace(a4_dir)

    total = sum(len(v) for v in results.values())
    fix_errors = sum(len(r.errors) for r in fix_reports)
    exit_code = 2 if (total or fix_errors) else 0

    if args.json:
        out = {
            "a4_dir": str(a4_dir),
            "files": file_rels,
            "enabled": sorted(enabled),
            "skipped_workspace_only": skipped,
            "checks": {
                name: [asdict(i) for i in issues]
                for name, issues in results.items()
            },
        }
        if args.fix:
            out["fix"] = {
                "mode": "supersedes-sweep",
                "dry_run": args.dry_run,
                "reports": [_fix_report_to_dict(r) for r in fix_reports],
                "total_cascades": sum(len(r.cascades) for r in fix_reports),
                "total_errors": fix_errors,
            }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        sys.exit(exit_code)

    if args.fix:
        print("=== fix: supersedes-sweep ===")
        if not fix_reports:
            print("OK — no supersedes cascades needed.")
        else:
            for r in fix_reports:
                _print_fix_report_human(r, args.dry_run)

    for name in CHECKS:
        if name not in enabled:
            continue
        print(f"=== {name} ===")
        if name in skipped:
            print(
                "  skipped (workspace-only check; rerun without file args "
                "for this category)"
            )
            continue
        issues = results[name]
        if not issues:
            print("OK — no issues.")
            continue
        file_count = len({i.path for i in issues})
        print(
            f"{len(issues)} issue(s) across {file_count} file(s):",
            file=sys.stderr,
        )
        for i in issues:
            loc = i.path + (f" [{i.field}]" if i.field else "")
            print(f"  {loc} ({i.rule}): {i.message}", file=sys.stderr)

    sys.exit(exit_code)


def _fix_report_to_dict(report: Report) -> dict:
    return {
        "a4_dir": report.a4_dir,
        "file": report.file,
        "family": report.family,
        "current_status": report.current_status,
        "target_status": report.target_status,
        "primary": asdict(report.primary) if report.primary else None,
        "cascades": [asdict(c) for c in report.cascades],
        "skipped": report.skipped,
        "errors": report.errors,
        "dry_run": report.dry_run,
        "ok": report.ok,
    }


def _print_fix_report_human(report: Report, dry_run: bool) -> None:
    prefix = "(dry-run) " if dry_run else ""
    for c in report.cascades:
        tail = f" — {c.reason}" if c.reason else ""
        print(f"{prefix}cascade: {c.path}: {c.from_status} → {c.to_status}{tail}")
    for s in report.skipped:
        print(f"  skipped: {s.get('path', '?')} ({s.get('reason', '?')})")
    for e in report.errors:
        print(f"  error: {e}", file=sys.stderr)


def _resolve_selection(
    parser: argparse.ArgumentParser, only: str | None, skip: str | None
) -> set[str]:
    enabled = set(CHECKS.keys())
    if only:
        names = {x.strip() for x in only.split(",") if x.strip()}
        unknown = names - set(CHECKS)
        if unknown:
            parser.error(f"unknown check(s) in --only: {sorted(unknown)}")
        enabled = names
    if skip:
        names = {x.strip() for x in skip.split(",") if x.strip()}
        unknown = names - set(CHECKS)
        if unknown:
            parser.error(f"unknown check(s) in --skip: {sorted(unknown)}")
        enabled -= names
    if not enabled:
        parser.error("no checks enabled after applying --only / --skip")
    return enabled


if __name__ == "__main__":
    main()
