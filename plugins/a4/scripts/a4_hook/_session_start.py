"""SessionStart subcommand: inject type→file-location map and reserved-fields directive.

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
from pathlib import Path

from a4_hook._state import PLUGIN_ROOT, emit, project_dir_from_payload


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

    project_dir = project_dir_from_payload(payload)
    if not project_dir:
        return 0
    a4_dir = Path(project_dir) / "a4"
    if not a4_dir.is_dir():
        return 0

    try:
        from common import ISSUE_FOLDERS, WIKI_TYPES
    except ImportError:
        return 0

    issue_lines = [
        f"- `{t}` → `a4/{t}/<id>-<slug>.md`" for t in ISSUE_FOLDERS
    ]
    wiki_lines = [f"- `{t}` → `a4/{t}.md`" for t in sorted(WIKI_TYPES)]

    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT") or str(PLUGIN_ROOT)
    allocator = f"{plugin_root}/scripts/allocate_id.py"
    frontmatter_common = f"{plugin_root}/authoring/frontmatter-common.md"

    context = (
        "## a4/ workspace — type → file location\n\n"
        "**Issue families** (one file per id, flat folder):\n\n"
        + "\n".join(issue_lines)
        + "\n\n**Wiki pages** (single top-level file per type):\n\n"
        + "\n".join(wiki_lines)
        + "\n\n**Allocate id** (issue files only; never invent or reuse):\n\n"
        "```bash\n"
        f'"{allocator}" <a4-dir>\n'
        "```\n\n"
        "## Reserved frontmatter fields — DO NOT WRITE\n\n"
        "`created:` and `updated:` are **reserved**. Never write, edit, or "
        "include these two fields in any `a4/**/*.md` file (Write, Edit, "
        "MultiEdit). They are filled and refreshed by tooling.\n\n"
        "- Authoring a new file: omit both fields entirely.\n"
        "- Editing an existing file: leave both fields untouched.\n"
        "- Status flips: edit `status:` only.\n\n"
        f"Authoritative contract: `{frontmatter_common}`."
    )
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }
    )
    return 0
