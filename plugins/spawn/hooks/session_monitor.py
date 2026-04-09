# /// script
# requires-python = ">=3.10"
# ///
"""session_monitor — FileChanged hook (matcher: session-tree.json).

Monitors child session status changes from the main session side.
Writes notifications to the queue file and outputs systemMessage JSON
for immediate user visibility.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from notifications import append_notification, notification_queue_path
from session_tree import ChildEntry, SessionTree, read_stdin_json, st_read, st_write
from sessions_statusline_cache import update_cache


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
    queue_entries: list[dict] = []
    now_epoch = time.time()

    session_tree_dir = str(Path(session_tree_path).parent)
    queue = notification_queue_path(session_tree_dir, "", is_main=True)

    prev_children: dict[str, ChildEntry] = {c.id: c for c in previous.children if c.id}

    for child in current.children:
        if not child.id:
            continue

        prev_entry = prev_children.get(child.id) if has_previous else None
        prev_status = prev_entry.status if prev_entry else ""

        # Crash detection (active or resumed with dead pid)
        if child.status in ("active", "resumed") and child.pid is not None:
            if not _pid_alive(child.pid):
                def _mark_crashed(tree: SessionTree, _cid: str = child.id) -> None:
                    c = tree.find_child(_cid)
                    if c:
                        c.status = "crashed"

                st_write(_mark_crashed)
                msg = f"Session **{child.topic}** crashed — process no longer alive"
                notifications.append(msg)
                queue_entries.append({
                    "type": "crash", "childId": child.id,
                    "topic": child.topic, "message": msg,
                })
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
                msg = f"Session **{child.topic}** failed to start — handshake timeout (>30s)"
                notifications.append(msg)
                queue_entries.append({
                    "type": "failed_to_start", "childId": child.id,
                    "topic": child.topic, "message": msg,
                })
                continue

        # Deliverable notification via resultUpdatedAt change
        if child.result_updated_at and prev_entry:
            prev_updated = prev_entry.result_updated_at or ""
            if child.result_updated_at != prev_updated:
                files_str = ", ".join(child.result_files) if child.result_files else "(none)"
                msg = f"Session **{child.topic}** registered new deliverables: {files_str}"
                notifications.append(msg)
                queue_entries.append({
                    "type": "deliverable", "childId": child.id,
                    "topic": child.topic, "resultFiles": child.result_files,
                    "message": msg,
                })

        # Terminated session
        if child.status == "terminated" and prev_status != "terminated":
            if child.result_files:
                files_str = ", ".join(child.result_files)
                msg = f"Session **{child.topic}** terminated. Results: {files_str}"
            else:
                msg = f"Session **{child.topic}** terminated. No result files registered. You can resume it to register deliverables."
            notifications.append(msg)
            queue_entries.append({
                "type": "terminated", "childId": child.id,
                "topic": child.topic,
                "resultFiles": child.result_files,
                "message": msg,
            })
            continue

        # Report non-active statuses on first run (no previous snapshot)
        if not has_previous and child.status not in ("active", "resumed", "terminated"):
            msg = f"Session **{child.topic}**: {child.status}"
            notifications.append(msg)

    # Write to notification queue
    for entry in queue_entries:
        append_notification(queue, entry)

    # Update statusline cache
    main_session_id = current.main_session.id if current.main_session else ""
    if main_session_id:
        update_cache(session_tree_path, main_session_id)

    # Output systemMessage for immediate user visibility
    if notifications:
        body = "Child Session Updates:\n"
        for note in notifications:
            body += f"- {note}\n"
        print(json.dumps({"systemMessage": body}, ensure_ascii=False))


if __name__ == "__main__":
    main()
