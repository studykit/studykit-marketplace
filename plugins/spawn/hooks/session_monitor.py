# /// script
# requires-python = ">=3.10"
# ///
"""session_monitor — FileChanged hook (matcher: session-tree.json).

Monitors child session status changes from the main session side.
Outputs additionalContext JSON when notable changes are detected.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from session_tree import ChildEntry, SessionTree, read_stdin_json, st_read, st_write


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _parse_iso(ts: str) -> float:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return 0.0


def main() -> None:
    session_tree_path = os.environ.get("SESSION_TREE", "")
    if not session_tree_path:
        return

    data = read_stdin_json()
    file_path: str = data.get("file_path", "")

    if file_path != session_tree_path:
        return

    current = st_read()

    last_file = Path(session_tree_path).with_suffix(".last")

    previous = SessionTree()
    has_previous = False

    if last_file.exists():
        try:
            previous = SessionTree.from_dict(json.loads(last_file.read_text()))
            has_previous = True
        except (json.JSONDecodeError, ValueError):
            previous = SessionTree()

    last_file.write_text(json.dumps(current.to_dict(), ensure_ascii=False, indent=2) + "\n")

    notifications: list[str] = []
    now_epoch = time.time()

    prev_children: dict[str, ChildEntry] = {c.id: c for c in previous.children if c.id}

    for child in current.children:
        if not child.id:
            continue

        prev_status = ""
        if has_previous:
            prev = prev_children.get(child.id)
            prev_status = prev.status if prev else ""

        # Crash detection
        if child.status == "active" and child.pid is not None:
            if not _pid_alive(child.pid):
                def _mark_crashed(tree: SessionTree, _cid: str = child.id) -> None:
                    c = tree.find_child(_cid)
                    if c:
                        c.status = "crashed"

                st_write(_mark_crashed)
                notifications.append(
                    f"- **{child.topic}** ({child.id}): crashed — process no longer alive"
                )
                continue

        # Handshake timeout
        if child.status == "pending" and child.created_at:
            created_epoch = _parse_iso(child.created_at)
            if now_epoch - created_epoch > 30:
                def _mark_failed(tree: SessionTree, _cid: str = child.id) -> None:
                    c = tree.find_child(_cid)
                    if c:
                        c.status = "failed_to_start"

                st_write(_mark_failed)
                notifications.append(
                    f"- **{child.topic}** ({child.id}): failed to start — handshake timeout (>30s)"
                )
                continue

        # New result files
        if child.status == "active" and has_previous:
            prev_entry = prev_children.get(child.id)
            prev_files = set(prev_entry.result_files) if prev_entry else set()
            curr_files = set(child.result_files)
            new_files = sorted(curr_files - prev_files)
            if new_files:
                notifications.append(
                    f"- **{child.topic}** ({child.id}): new result files: {', '.join(new_files)}"
                )

        # Terminated session
        if child.status == "terminated" and prev_status != "terminated":
            if child.result_files:
                notifications.append(
                    f"- **{child.topic}** ({child.id}): terminated — result files: {', '.join(child.result_files)}"
                )
            else:
                notifications.append(
                    f"- **{child.topic}** ({child.id}): terminated"
                )
            continue

        # Report other non-active statuses on first run
        if not has_previous and child.status not in ("active", "terminated"):
            notifications.append(
                f"- **{child.topic}** ({child.id}): {child.status}"
            )

    if notifications:
        body = "## Child Session Updates\\n\\n"
        for note in notifications:
            body += f"{note}\\n"
        print(json.dumps({"additionalContext": body}))


if __name__ == "__main__":
    main()
