# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Materialize `decision.superseded` onto predecessor decision files.

**Scope: decision family only.** The usecase version of this cascade was
absorbed into `scripts/transition_status.py` in plugin version 1.10.0 —
UC `shipped → superseded` now fires during the successor's
`→ shipped` transition inside the single-writer flow, not via a
PostToolUse hook. This script handles only `decision/*.md`.

The a4 workspace treats `supersedes:` as forward-only: a newer decision
declares which older decision(s) it replaces. The matching reverse
status (`superseded` on the older decision) is "derived" in the sense
that its truth comes from that relationship — but leaving it *only*
derived means the old file's own status never changes, so greps,
dataview queries, and file-open inspection all fail to tell you whether
it is still current.

Given a recently edited `decision/*.md`, this script checks whether:

  (a) the file is at `status: final`;
  (b) the file's `supersedes:` list is non-empty.

If both hold, for each target listed in `supersedes:` it:

  1. Flips the target's `status:` from `final` to `superseded`.
  2. Bumps the target's `updated:` to today.
  3. Appends a `## Log` entry on the target:
       YYYY-MM-DD — superseded by decision/<stem>

Idempotent: already-`superseded` targets are skipped. Targets not at
`final` are reported but left alone (the propagation is only meaningful
once the successor has actually landed).

Cross-family supersedes (e.g., decision → usecase) are ignored — the
relationship is always same-family in a4.

Usage:

    uv run propagate_superseded.py <a4-dir> --file <decision-path>
    uv run propagate_superseded.py <a4-dir> --file <decision-path> --dry-run
    uv run propagate_superseded.py <a4-dir> --file <decision-path> --json

    # Sweep all files in a4/decision/ (idempotent):
    uv run propagate_superseded.py <a4-dir> --sweep

`--file` accepts either an absolute path or a workspace-relative path
(e.g. `decision/5-foo.md`). UC paths are silently ignored — the UC
cascade runs from `transition_status.py`.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml


# Per-family mapping: folder name -> status value that denotes
# "this successor is now live, so its predecessors should flip to
# superseded". The usecase entry was removed in plugin 1.10.0 — UC
# cascades run from transition_status.py.
TERMINAL_ACTIVE: dict[str, str] = {
    "decision": "final",
}


@dataclass
class Change:
    target: str
    previous_status: str
    new_status: str = "superseded"
    log_line: str = ""


@dataclass
class Report:
    successor: str = ""
    family: str = ""
    successor_status: str | None = None
    propagated: list[Change] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def split_frontmatter(path: Path) -> tuple[dict | None, str, str]:
    """Return (frontmatter-dict, raw-frontmatter-string, body)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None, "", text
    # Keep only the first split, preserving any `---` inside body content.
    after_open = text[4:] if text.startswith("---\n") else text[5:]
    end_marker_idx = after_open.find("\n---")
    if end_marker_idx == -1:
        return None, "", text
    raw_fm = after_open[:end_marker_idx]
    # Skip past the closing marker line.
    rest_start = end_marker_idx + len("\n---")
    remaining = after_open[rest_start:]
    if remaining.startswith("\r\n"):
        remaining = remaining[2:]
    elif remaining.startswith("\n"):
        remaining = remaining[1:]
    try:
        fm = yaml.safe_load(raw_fm) if raw_fm.strip() else {}
    except yaml.YAMLError:
        return None, raw_fm, remaining
    if fm is None:
        fm = {}
    if not isinstance(fm, dict):
        return None, raw_fm, remaining
    return fm, raw_fm, remaining


def _normalize_ref(ref: Any) -> str | None:
    if not isinstance(ref, str):
        return None
    cleaned = ref.strip()
    if not cleaned:
        return None
    if cleaned.endswith(".md"):
        cleaned = cleaned[:-3]
    return cleaned


def _family_of_ref(ref: str) -> str | None:
    parts = ref.split("/", 1)
    if len(parts) != 2:
        return None
    return parts[0]


def _rewrite_frontmatter_scalar(raw_fm: str, field: str, new_value: str) -> str:
    """Replace `field: <anything-on-rest-of-line>` with the new value.

    Preserves surrounding whitespace and other lines. If the field is
    absent, appends it at the end of the frontmatter block.
    """
    lines = raw_fm.split("\n")
    pattern_prefix = f"{field}:"
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(pattern_prefix):
            indent = line[: len(line) - len(stripped)]
            lines[i] = f"{indent}{field}: {new_value}"
            return "\n".join(lines)
    # Field absent — append before trailing empty lines.
    while lines and lines[-1].strip() == "":
        lines.pop()
    lines.append(f"{field}: {new_value}")
    return "\n".join(lines)


def _append_log_entry(body: str, log_line: str) -> str:
    """Append a line to the `## Log` section; create the section if missing.

    Convention: `## Log` is the last body section when present. We append
    a bullet `- <log_line>` under it.
    """
    log_header = "## Log"
    normalized_body = body.rstrip("\n")
    if log_header in normalized_body:
        parts = normalized_body.rsplit(log_header, 1)
        head, tail = parts[0], parts[1]
        tail = tail.rstrip("\n") + f"\n- {log_line}\n"
        return f"{head}{log_header}{tail}"
    # No Log section — append one.
    sep = "\n\n" if normalized_body else ""
    return f"{normalized_body}{sep}## Log\n\n- {log_line}\n"


def _write_file(path: Path, raw_fm: str, body: str) -> None:
    # Reconstruct with a leading `---\n` + trailing `---\n` so the
    # round-trip matches the existing files' shape.
    trimmed_fm = raw_fm.rstrip("\n")
    content = f"---\n{trimmed_fm}\n---\n{body.lstrip()}"
    # Preserve trailing newline if the body has one.
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def _flip_target(
    a4_dir: Path,
    family: str,
    target_ref: str,
    successor_ref: str,
    today: str,
    dry_run: bool,
) -> tuple[Change | None, dict | None, str | None]:
    """Flip a single target file to `superseded`.

    Returns (change, skip-info, error). Exactly one is non-None per call.
    """
    target_path = a4_dir / f"{target_ref}.md"
    if not target_path.is_file():
        return None, {
            "target": target_ref,
            "reason": "target-missing",
            "detail": f"{target_path} not found",
        }, None

    fm, raw_fm, body = split_frontmatter(target_path)
    if fm is None:
        return None, None, f"{target_path}: unreadable frontmatter"

    current = fm.get("status")
    terminal_active = TERMINAL_ACTIVE.get(family)
    if current == "superseded":
        return None, {
            "target": target_ref,
            "reason": "already-superseded",
        }, None
    if current != terminal_active:
        return None, {
            "target": target_ref,
            "reason": "not-terminal-active",
            "detail": f"status={current!r}, expected {terminal_active!r}",
        }, None

    log_line = f"{today} — superseded by {successor_ref}"
    new_fm = _rewrite_frontmatter_scalar(raw_fm, "status", "superseded")
    new_fm = _rewrite_frontmatter_scalar(new_fm, "updated", today)
    new_body = _append_log_entry(body, log_line)

    if not dry_run:
        _write_file(target_path, new_fm, new_body)

    return Change(
        target=target_ref,
        previous_status=str(current),
        log_line=log_line,
    ), None, None


def propagate_for_file(
    a4_dir: Path, successor_rel: str, dry_run: bool = False
) -> Report:
    report = Report(successor=successor_rel)
    family = _family_of_ref(successor_rel.removesuffix(".md"))
    if family not in TERMINAL_ACTIVE:
        return report  # silent no-op: the rule only applies to usecase + decision

    report.family = family
    successor_path = a4_dir / successor_rel
    if not successor_path.is_file():
        report.errors.append(f"successor file missing: {successor_path}")
        return report

    fm, _, _ = split_frontmatter(successor_path)
    if fm is None:
        report.errors.append(f"successor has unreadable frontmatter: {successor_path}")
        return report

    status = fm.get("status")
    report.successor_status = str(status) if status is not None else None
    terminal_active = TERMINAL_ACTIVE[family]
    if status != terminal_active:
        # Not live yet — nothing to propagate. Not an error.
        return report

    supersedes = fm.get("supersedes") or []
    if not isinstance(supersedes, list) or not supersedes:
        return report

    today = date.today().isoformat()
    successor_ref = successor_rel.removesuffix(".md")

    for entry in supersedes:
        norm = _normalize_ref(entry)
        if norm is None:
            report.skipped.append(
                {"target": str(entry), "reason": "unparseable-ref"}
            )
            continue
        target_family = _family_of_ref(norm)
        if target_family != family:
            report.skipped.append(
                {
                    "target": norm,
                    "reason": "cross-family-ref",
                    "detail": (
                        f"successor is {family}, target is {target_family}; "
                        "supersedes must stay within the same family"
                    ),
                }
            )
            continue
        change, skip, err = _flip_target(
            a4_dir, family, norm, successor_ref, today, dry_run
        )
        if err:
            report.errors.append(err)
        elif change:
            report.propagated.append(change)
        elif skip:
            report.skipped.append(skip)

    return report


def sweep(a4_dir: Path, dry_run: bool = False) -> list[Report]:
    reports: list[Report] = []
    for family in TERMINAL_ACTIVE:
        folder = a4_dir / family
        if not folder.is_dir():
            continue
        for p in sorted(folder.glob("*.md")):
            rel = f"{family}/{p.name}"
            reports.append(propagate_for_file(a4_dir, rel, dry_run=dry_run))
    return reports


def _resolve_file(a4_dir: Path, raw: str) -> str | None:
    p = Path(raw)
    abs_path = p if p.is_absolute() else (a4_dir / p)
    try:
        rel = abs_path.resolve().relative_to(a4_dir.resolve())
    except ValueError:
        return None
    return str(rel)


def _report_to_dict(report: Report) -> dict:
    return {
        "successor": report.successor,
        "family": report.family,
        "successor_status": report.successor_status,
        "propagated": [asdict(c) for c in report.propagated],
        "skipped": report.skipped,
        "errors": report.errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize `superseded` status onto predecessor files when a "
            "successor UC or decision reaches its terminal-active state."
        )
    )
    parser.add_argument("a4_dir", type=Path, help="path to the a4/ workspace")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--file",
        dest="file",
        type=str,
        default=None,
        help=(
            "propagate for a single successor file (absolute or "
            "workspace-relative path)"
        ),
    )
    mode.add_argument(
        "--sweep",
        action="store_true",
        help="sweep every usecase/ and decision/ file (idempotent)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report planned changes without modifying files",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit structured JSON to stdout"
    )
    args = parser.parse_args()

    a4_dir = args.a4_dir.resolve()
    if not a4_dir.is_dir():
        print(f"Error: {a4_dir} is not a directory", file=sys.stderr)
        sys.exit(2)

    if args.sweep:
        reports = sweep(a4_dir, dry_run=args.dry_run)
    else:
        rel = _resolve_file(a4_dir, args.file)
        if rel is None:
            print(
                f"Error: --file {args.file} is not inside {a4_dir}",
                file=sys.stderr,
            )
            sys.exit(2)
        reports = [propagate_for_file(a4_dir, rel, dry_run=args.dry_run)]

    total_changes = sum(len(r.propagated) for r in reports)
    total_errors = sum(len(r.errors) for r in reports)

    if args.json:
        out = {
            "a4_dir": str(a4_dir),
            "dry_run": args.dry_run,
            "reports": [_report_to_dict(r) for r in reports],
            "total_propagated": total_changes,
            "total_errors": total_errors,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        for report in reports:
            if not report.propagated and not report.errors and not report.skipped:
                continue
            if report.propagated or report.errors:
                print(f"[{report.successor}] status={report.successor_status}")
            for change in report.propagated:
                prefix = "(dry-run) " if args.dry_run else ""
                print(
                    f"  {prefix}→ flipped {change.target}: "
                    f"{change.previous_status} → superseded"
                )
            for err in report.errors:
                print(f"  ! error: {err}", file=sys.stderr)

    if total_errors:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
