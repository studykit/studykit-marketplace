# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Refresh the `implemented_by:` reverse-link field on UC files.

Use cases reference tasks indirectly — the forward link is on tasks
(`implements: [usecase/<id>-<slug>]`). The reverse link
(`implemented_by: [task/<id>-<slug>, ...]`) on the UC is maintained by
this script by back-scanning the task directory.

`implemented_by:` is consumed by:

  - `task-implementer`: `ready → implementing` is allowed only if the
    target UC has `implemented_by:` non-empty (there is work to do).
  - `/a4:plan` Step 2.5: ship-check confirms every listed task is
    `complete` before flipping the UC to `shipped`.

Normal invocation happens at the end of `/a4:plan` Phase 1 after task
files are generated. A SessionStart sweep is also useful after a `git
checkout` or branch rebase.

This script only writes `implemented_by:`. It does not change status,
updated, or any other field. Running it twice with no intervening task
edits is a no-op.

Usage:
    uv run refresh_implemented_by.py <a4-dir>                # sweep all UCs
    uv run refresh_implemented_by.py <a4-dir> --file <uc-path>
    uv run refresh_implemented_by.py <a4-dir> --dry-run --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Change:
    uc: str
    previous: list[str]
    new: list[str]


@dataclass
class Report:
    a4_dir: str = ""
    changes: list[Change] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = False


def split_frontmatter(path: Path) -> tuple[dict | None, str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None, "", text
    after_open = text[4:] if text.startswith("---\n") else text[5:]
    end_marker_idx = after_open.find("\n---")
    if end_marker_idx == -1:
        return None, "", text
    raw_fm = after_open[:end_marker_idx]
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


def normalize_ref(ref: Any) -> str | None:
    if not isinstance(ref, str):
        return None
    cleaned = ref.strip()
    if not cleaned:
        return None
    if cleaned.endswith(".md"):
        cleaned = cleaned[:-3]
    return cleaned


def collect_implements(a4_dir: Path) -> dict[str, list[str]]:
    """Map `usecase/<stem>` → sorted list of `task/<stem>` references."""
    task_dir = a4_dir / "task"
    out: dict[str, set[str]] = {}
    if not task_dir.is_dir():
        return {}
    for p in sorted(task_dir.glob("*.md")):
        fm, _, _ = split_frontmatter(p)
        if fm is None:
            continue
        implements = fm.get("implements")
        if not isinstance(implements, list):
            continue
        task_ref = f"task/{p.stem}"
        for entry in implements:
            norm = normalize_ref(entry)
            if norm is None or not norm.startswith("usecase/"):
                continue
            out.setdefault(norm, set()).add(task_ref)
    return {uc_ref: sorted(tasks) for uc_ref, tasks in out.items()}


def _rewrite_list_field(raw_fm: str, field_name: str, values: list[str]) -> str:
    """Set `field_name:` to a YAML flow-list. Add field if absent."""
    lines = raw_fm.split("\n")
    prefix = f"{field_name}:"
    yaml_value = _format_list(values)
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(prefix):
            indent = line[: len(line) - len(stripped)]
            # Replace this line; if the field had a block-style list
            # continuation on following lines (starting with `- ` at
            # same or deeper indent), remove those too.
            end = i + 1
            list_indent = indent + "  "
            while end < len(lines):
                nxt = lines[end]
                if nxt.lstrip().startswith("- ") and nxt.startswith(list_indent):
                    end += 1
                    continue
                if nxt.strip() == "" or not nxt.startswith(indent):
                    break
                break
            new_line = f"{indent}{field_name}: {yaml_value}"
            return "\n".join(lines[:i] + [new_line] + lines[end:])
    # Append at end.
    while lines and lines[-1].strip() == "":
        lines.pop()
    lines.append(f"{field_name}: {yaml_value}")
    return "\n".join(lines)


def _format_list(values: list[str]) -> str:
    if not values:
        return "[]"
    # Single-line flow list — short, dataview-friendly.
    quoted = ", ".join(values)
    return f"[{quoted}]"


def _write_file(path: Path, raw_fm: str, body: str) -> None:
    trimmed = raw_fm.rstrip("\n")
    content = f"---\n{trimmed}\n---\n{body.lstrip()}"
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def _current_implemented_by(fm: dict) -> list[str]:
    raw = fm.get("implemented_by")
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for x in raw:
        n = normalize_ref(x)
        if n:
            out.append(n)
    return sorted(out)


def _refresh_uc(
    a4_dir: Path,
    uc_path: Path,
    target_list: list[str],
    dry_run: bool,
    report: Report,
) -> None:
    fm, raw_fm, body = split_frontmatter(uc_path)
    if fm is None:
        report.errors.append(f"{uc_path}: unreadable frontmatter")
        return
    current = _current_implemented_by(fm)
    uc_ref = f"usecase/{uc_path.stem}"
    if current == target_list:
        report.unchanged.append(uc_ref)
        return
    if not dry_run:
        new_fm = _rewrite_list_field(raw_fm, "implemented_by", target_list)
        _write_file(uc_path, new_fm, body)
    report.changes.append(
        Change(uc=uc_ref, previous=current, new=target_list)
    )


def refresh_all(a4_dir: Path, dry_run: bool) -> Report:
    report = Report(a4_dir=str(a4_dir), dry_run=dry_run)
    uc_dir = a4_dir / "usecase"
    if not uc_dir.is_dir():
        return report
    implements_map = collect_implements(a4_dir)
    for p in sorted(uc_dir.glob("*.md")):
        uc_ref = f"usecase/{p.stem}"
        target = implements_map.get(uc_ref, [])
        _refresh_uc(a4_dir, p, target, dry_run, report)
    return report


def refresh_one(a4_dir: Path, uc_rel: str, dry_run: bool) -> Report:
    report = Report(a4_dir=str(a4_dir), dry_run=dry_run)
    uc_path = a4_dir / uc_rel
    if not uc_path.is_file():
        report.errors.append(f"UC file not found: {uc_path}")
        return report
    implements_map = collect_implements(a4_dir)
    uc_ref = f"usecase/{uc_path.stem}"
    target = implements_map.get(uc_ref, [])
    _refresh_uc(a4_dir, uc_path, target, dry_run, report)
    return report


def _resolve_rel(a4_dir: Path, raw: str) -> str | None:
    p = Path(raw)
    abs_path = p if p.is_absolute() else (a4_dir / p)
    try:
        rel = abs_path.resolve().relative_to(a4_dir.resolve())
    except ValueError:
        return None
    return str(rel)


def _report_to_dict(report: Report) -> dict:
    return {
        "a4_dir": report.a4_dir,
        "dry_run": report.dry_run,
        "changes": [asdict(c) for c in report.changes],
        "unchanged": report.unchanged,
        "errors": report.errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh UC `implemented_by:` from task `implements:` back-scan."
    )
    parser.add_argument("a4_dir", type=Path, help="path to the a4/ workspace")
    parser.add_argument(
        "--file", type=str, default=None,
        help="refresh a single UC file (absolute or workspace-relative)",
    )
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

    if args.file:
        rel = _resolve_rel(a4_dir, args.file)
        if rel is None:
            print(
                f"Error: --file {args.file} is not inside {a4_dir}",
                file=sys.stderr,
            )
            sys.exit(2)
        report = refresh_one(a4_dir, rel, dry_run=args.dry_run)
    else:
        report = refresh_all(a4_dir, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(_report_to_dict(report), indent=2, ensure_ascii=False))
    else:
        prefix = "(dry-run) " if args.dry_run else ""
        for c in report.changes:
            print(
                f"{prefix}{c.uc}: implemented_by {c.previous} → {c.new}"
            )
        if not report.changes and not report.errors:
            print(f"OK — {len(report.unchanged)} UC(s) already up to date.")
        for e in report.errors:
            print(f"error: {e}", file=sys.stderr)

    sys.exit(2 if report.errors else 0)


if __name__ == "__main__":
    main()
