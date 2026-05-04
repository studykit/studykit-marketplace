"""SessionStart subcommand: sweep stale hook state and inject type→location map.

Surfaces the layout (issue families as flat ``a4/<type>/<id>-<slug>.md``;
wiki pages as top-level ``a4/<type>.md``) so the LLM places new files
correctly, and the runnable allocator command so it can claim a
workspace-global monotonic id without searching for it — both before
the first Write/Edit triggers PreToolUse contract-injection. Built
from ``common.WIKI_TYPES`` and ``common.ISSUE_FOLDERS`` so adding a new
type does not require touching this function.

The allocator path is emitted as a fully-resolved absolute path
(runtime-specific plugin-root environment declared in ``a4_hook._runtime``;
``__file__`` fallback for direct script tests) so the LLM can invoke
``allocate_id.py`` directly via its shebang — no ``uv run`` wrapper required.

The stale-record sweep runs once per SessionStart before the ``a4/`` directory
check so crashed-session state is cleaned even if the workspace has since
removed a4/. Silent when the project has no ``a4/`` directory (non-a4 projects
get no SessionStart context noise). Always exits 0.
"""

from __future__ import annotations

import sys
from pathlib import Path

from a4_hook._runtime import plugin_root_from_payload
from a4_hook._state import PLUGIN_ROOT, emit, project_dir_from_payload, trace, trace_file


_STALE_RECORD_MAX_AGE_SECONDS = 24 * 60 * 60
_STALE_RECORD_NAMES = {"trace.log"}
_STALE_RECORD_PATTERNS: tuple[tuple[str, str], ...] = (
    ("a4-edited-", ".txt"),
    ("a4-resolved-ids-", ".txt"),
    ("a4-prestatus-", ".json"),
    ("a4-injected-", ".txt"),
)


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

    swept_records = _sweep_old_records(project_dir)

    a4_dir = Path(project_dir) / "a4"
    if not a4_dir.is_dir():
        trace(
            project_dir,
            None,
            "session-start",
            "noop",
            reason="no_a4_dir",
            swept_records=swept_records,
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
            swept_records=swept_records,
        )
        return 0

    issue_lines = [
        f"- `{t}` → `a4/{t}/<id>-<slug>.md`" for t in ISSUE_FOLDERS
    ]
    wiki_lines = [f"- `{t}` → `a4/{t}.md`" for t in sorted(WIKI_TYPES)]

    plugin_root = plugin_root_from_payload(payload, PLUGIN_ROOT)
    allocator = str(plugin_root / "scripts" / "allocate_id.py")
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
        swept_records=swept_records,
        issue_types=ISSUE_FOLDERS,
        wiki_types=sorted(WIKI_TYPES),
    )
    return 0


def _sweep_old_records(project_dir: str) -> int:
    """Delete stale a4 hook record files older than one day.

    This is the Python equivalent of the historical
    ``hooks/sweep-old-edited-a4.sh`` hook, kept inside SessionStart so every
    runtime uses the same runtime-layer project resolution.
    """

    import time

    record_dir = trace_file(project_dir).parent
    if not record_dir.is_dir():
        return 0

    cutoff = time.time() - _STALE_RECORD_MAX_AGE_SECONDS
    deleted = 0
    try:
        candidates = list(record_dir.iterdir())
    except OSError:
        return 0

    for path in candidates:
        if not path.is_file() or not _is_stale_record_name(path.name):
            continue
        try:
            if path.stat().st_mtime >= cutoff:
                continue
            path.unlink()
            deleted += 1
        except OSError:
            continue

    return deleted


def _is_stale_record_name(name: str) -> bool:
    if name in _STALE_RECORD_NAMES:
        return True
    return any(
        name.startswith(prefix) and name.endswith(suffix)
        for prefix, suffix in _STALE_RECORD_PATTERNS
    )
