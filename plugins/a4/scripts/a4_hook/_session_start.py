"""SessionStart subcommand: inject type→file-location map.

Surfaces the layout (issue families as flat ``a4/<type>/<id>-<slug>.md``;
wiki pages as top-level ``a4/<type>.md``) so the LLM places new files
correctly, and the runnable allocator command so it can claim a
workspace-global monotonic id without searching for it — both before
the first Write/Edit triggers PreToolUse contract-injection. Built
from ``common.WIKI_TYPES`` and ``common.ISSUE_FOLDERS`` so adding a new
type does not require touching this function.

The allocator path is emitted as a fully-resolved absolute path
(``CLAUDE_PLUGIN_ROOT`` expanded in-process) so the LLM can invoke
``allocate_id.py`` directly via its shebang — no ``uv run`` wrapper
required.

Silent when the project has no ``a4/`` directory (non-a4 projects get
no SessionStart noise). Always exits 0.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from a4_hook._state import PLUGIN_ROOT, emit, project_dir_from_payload, trace, trace_file


_TRACE_MAX_AGE_SECONDS = 24 * 60 * 60


def session_start() -> int:
    """SessionStart entry point. Always exits 0."""
    import json
    import os

    # Drain stdin defensively. Claude Code pipes a JSON payload to
    # SessionStart hooks; we read no fields, but a closed pipe on an
    # unread parent stdin can block.
    try:
        raw = sys.stdin.read()
    except OSError:
        raw = ""
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {}
        trace(project_dir_from_payload({}), None, "session-start", "abort", reason="bad_json")

    project_dir = project_dir_from_payload(payload)
    if not project_dir:
        trace(None, None, "session-start", "abort", reason="no_project_dir")
        return 0

    trace_path = trace_file(project_dir)
    truncated_trace = False
    if trace_path.is_file():
        try:
            if trace_path.stat().st_mtime < time.time() - _TRACE_MAX_AGE_SECONDS:
                trace_path.write_text("", encoding="utf-8")
                truncated_trace = True
        except OSError:
            pass

    a4_dir = Path(project_dir) / "a4"
    if not a4_dir.is_dir():
        trace(
            project_dir,
            None,
            "session-start",
            "noop",
            reason="no_a4_dir",
            truncated_trace=truncated_trace,
        )
        return 0

    try:
        from common import ISSUE_FOLDERS, WIKI_TYPES
    except ImportError:
        trace(
            project_dir,
            None,
            "session-start",
            "abort",
            reason="import_common_failed",
            truncated_trace=truncated_trace,
        )
        return 0

    issue_lines = [
        f"- `{t}` → `a4/{t}/<id>-<slug>.md`" for t in ISSUE_FOLDERS
    ]
    wiki_lines = [f"- `{t}` → `a4/{t}.md`" for t in sorted(WIKI_TYPES)]

    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT") or str(PLUGIN_ROOT)
    allocator = f"{plugin_root}/scripts/allocate_id.py"
    context = (
        "## a4/ workspace — type → file location\n\n"
        "**Issue families** (one file per id, flat folder):\n\n"
        + "\n".join(issue_lines)
        + "\n\n**Wiki pages** (single top-level file per type):\n\n"
        + "\n".join(wiki_lines)
        + "\n\n**Allocate id** (issue files only; never invent or reuse):\n\n"
        "```bash\n"
        f'"{allocator}" <a4-dir>\n'
        "```"
    )
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }
    )
    trace(
        project_dir,
        None,
        "session-start",
        "emit_context",
        truncated_trace=truncated_trace,
        issue_types=ISSUE_FOLDERS,
        wiki_types=sorted(WIKI_TYPES),
    )
    return 0
