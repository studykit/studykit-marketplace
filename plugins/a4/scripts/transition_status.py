# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Supersedes-chain recovery sweep for the a4/ workspace.

The live path for status transitions is the PostToolUse hook
(`a4_hook.py post-edit`): when an LLM edits `status:` directly, the
hook detects the pre→post transition and runs the cascade
(supersedes / discarded / revising) on related files. Cascade
primitives live in `status_cascade.py` and are shared by the hook and
this script.

This CLI is the recovery path for cases where edits bypassed the hook
— manual `git checkout`, external editors, scripts that wrote
frontmatter without going through Claude Code, etc. — so a derived
`superseded` flip never landed.

What it does: walk all live-successor files (usecase @ `shipped`,
spec @ `active`) that carry a non-empty `supersedes:` list, and run
the supersedes-chain cascade on each. Idempotent — a second run on
the same workspace produces no further changes.

Usage:
    uv run transition_status.py <a4-dir>
    uv run transition_status.py <a4-dir> --dry-run
    uv run transition_status.py <a4-dir> --json

Exit codes:
  0 — clean run (sweep applied or nothing to do).
  2 — sweep surfaced one or more errors.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

from common import iter_family
from markdown_validator.refs import RefIndex
from status_cascade import Report, apply_supersedes_chain
from status_model import SUPERSEDES_TRIGGER_STATUS


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------


def sweep(a4_dir: Path, dry_run: bool) -> list[Report]:
    """Walk all live-successor files and run the supersedes cascade.

    Covers both families that carry `supersedes:`:

      - usecase @ `shipped` → flip same-family targets `shipped → superseded`.
      - spec @ `active` → flip same-family targets
        `{active|deprecated} → superseded`.

    Idempotent.
    """
    reports: list[Report] = []
    today = date.today().isoformat()
    index = RefIndex(a4_dir)

    for family, trigger in (
        ("usecase", SUPERSEDES_TRIGGER_STATUS["usecase"]),
        ("spec", SUPERSEDES_TRIGGER_STATUS["spec"]),
    ):
        for p, fm in iter_family(a4_dir, family):
            if fm.get("status") != trigger:
                continue
            supersedes = fm.get("supersedes")
            if not isinstance(supersedes, list) or not supersedes:
                continue
            rel = f"{family}/{p.name}"
            report = Report(
                a4_dir=str(a4_dir),
                file=rel,
                family=family,
                current_status=trigger,
                target_status=trigger,
                dry_run=dry_run,
            )
            apply_supersedes_chain(
                a4_dir, family, rel, today, dry_run, report, index
            )
            report.ok = not report.errors
            if report.cascades or report.errors:
                reports.append(report)

    return reports


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _report_to_dict(report: Report) -> dict:
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


def _print_report_human(report: Report, dry_run: bool) -> None:
    prefix = "(dry-run) " if dry_run else ""
    for c in report.cascades:
        tail = f" — {c.reason}" if c.reason else ""
        print(f"{prefix}cascade: {c.path}: {c.from_status} → {c.to_status}{tail}")
    for s in report.skipped:
        print(f"  skipped: {s.get('path', '?')} ({s.get('reason', '?')})")
    for e in report.errors:
        print(f"  error: {e}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Supersedes-chain recovery sweep. Walks usecase @ shipped / "
            "spec @ active and reconciles `superseded` flips that the "
            "PostToolUse hook would otherwise materialize. Idempotent."
        )
    )
    parser.add_argument("a4_dir", type=Path, help="path to the a4/ workspace")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="report planned changes without writing",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="emit structured JSON to stdout",
    )
    args = parser.parse_args()

    a4_dir = args.a4_dir.resolve()
    if not a4_dir.is_dir():
        print(f"Error: {a4_dir} is not a directory", file=sys.stderr)
        sys.exit(2)

    reports = sweep(a4_dir, dry_run=args.dry_run)
    total_cascades = sum(len(r.cascades) for r in reports)
    total_errors = sum(len(r.errors) for r in reports)

    if args.json:
        out = {
            "a4_dir": str(a4_dir),
            "mode": "sweep",
            "dry_run": args.dry_run,
            "reports": [_report_to_dict(r) for r in reports],
            "total_cascades": total_cascades,
            "total_errors": total_errors,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        for r in reports:
            _print_report_human(r, args.dry_run)
        if not reports:
            print("OK — no supersedes cascades needed.")

    sys.exit(2 if total_errors else 0)


if __name__ == "__main__":
    main()
