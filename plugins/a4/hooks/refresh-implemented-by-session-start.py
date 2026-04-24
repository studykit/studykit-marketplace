# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""SessionStart hook: refresh `implemented_by:` reverse-links on UC files.

Runs `scripts/refresh_implemented_by.py` with `--json` so any drift in
UC `implemented_by:` (caused by cross-branch edits, manual task edits,
or agent-driven task changes that bypassed /a4:plan) is reconciled at
session start — before the LLM or the user starts working.

Output policy:
  - clean      (no changes, no errors): silent, exit 0.
  - changed    (>=1 UC refreshed): `systemMessage` one-liner +
                structured `additionalContext` with per-UC diffs.
  - partial    (some UCs refreshed, some errors): both, each counted.
  - hard fail  (subprocess/parse error): silent, exit 0 — never block
                session start.

Non-blocking: always exits 0.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def emit(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def main() -> None:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not project_dir or not plugin_root:
        return

    a4_dir = Path(project_dir) / "a4"
    if not a4_dir.is_dir():
        return

    script = Path(plugin_root) / "scripts" / "refresh_implemented_by.py"
    if not script.is_file():
        return

    try:
        completed = subprocess.run(
            ["uv", "run", str(script), str(a4_dir), "--json"],
            capture_output=True,
            text=True,
            timeout=12,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return

    if completed.returncode != 0:
        return

    try:
        report = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return

    changes = report.get("changes") or []
    errors = report.get("errors") or []

    if not changes and not errors:
        return

    parts: list[str] = []
    if changes:
        parts.append(f"refreshed implemented_by on {len(changes)} UC(s)")
    if errors:
        parts.append(f"{len(errors)} error(s)")
    system_message = ", ".join(parts)
    if errors:
        system_message += " — see context"

    lines: list[str] = ["## a4/ implemented_by refresh (SessionStart)", ""]
    if changes:
        lines.append(f"Refreshed `implemented_by:` on {len(changes)} UC(s):")
        lines.append("")
        for ch in changes:
            uc = ch.get("uc", "?")
            prev = ch.get("previous") or []
            new = ch.get("new") or []
            lines.append(f"- `{uc}`: `{prev}` → `{new}`")
        lines.append("")
    if errors:
        lines.append(f"Errors ({len(errors)}):")
        lines.append("")
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")
    lines.append(
        "`implemented_by:` is auto-maintained by "
        "`scripts/refresh_implemented_by.py`; the SessionStart hook "
        "reconciles drift from cross-branch edits or manual task edits."
    )
    additional_context = "\n".join(lines)

    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": additional_context,
            },
            "systemMessage": system_message,
        }
    )


if __name__ == "__main__":
    main()
