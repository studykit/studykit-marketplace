# /// script
# requires-python = ">=3.10"
# ///
"""notification_relay — UserPromptSubmit hook that injects queued notifications.

Reads notification queue files and outputs accumulated notifications
as additionalContext so Claude receives them on the next user message.
Works in both main and child sessions.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from notifications import notification_queue_path, read_new_notifications
from session_tree import read_stdin_json, st_read


def main() -> None:
    data = read_stdin_json()
    session_id: str = data.get("session_id", "")
    if not session_id:
        return

    session_tree_env = os.environ.get("SESSION_TREE", "")

    if session_tree_env:
        # Child session — queue is in session-tree.json's directory
        session_tree_dir = str(Path(session_tree_env).parent)
        queue = notification_queue_path(session_tree_dir, session_id, is_main=False)
    else:
        # Main session — queue is in .claude/sessions/<session_id>/
        session_dir = Path(f".claude/sessions/{session_id}")
        if not session_dir.exists():
            return
        queue = notification_queue_path(str(session_dir), session_id, is_main=True)

    entries = read_new_notifications(queue)
    if not entries:
        return

    messages = [e.get("message", "") for e in entries if e.get("message")]
    if not messages:
        return

    body = "## Notifications\n\n"
    for msg in messages:
        body += f"- {msg}\n"

    print(json.dumps({"additionalContext": body}, ensure_ascii=False))


if __name__ == "__main__":
    main()
