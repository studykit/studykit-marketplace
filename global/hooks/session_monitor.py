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

from session_tree import read_stdin_json, st_read, st_write


def _pid_alive(pid: int) -> bool:
    """Check if a process is alive."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _parse_iso(ts: str) -> float:
    """Parse ISO 8601 timestamp to epoch seconds."""
    try:
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, TypeError):
        return 0.0


def main() -> None:
    session_tree_path = os.environ.get("SESSION_TREE", "")
    if not session_tree_path:
        return

    data = read_stdin_json()
    file_path = data.get("file_path", "")

    if file_path != session_tree_path:
        return

    # Read current state.
    current = st_read()

    # Snapshot file for change detection.
    last_file = Path(session_tree_path).with_suffix(".last")

    # Determine previous state.
    if last_file.exists():
        try:
            previous = json.loads(last_file.read_text())
        except (json.JSONDecodeError, ValueError):
            previous = {"mainSession": None, "children": []}
        has_previous = True
    else:
        previous = {"mainSession": None, "children": []}
        has_previous = False

    # Save current state as the new snapshot.
    last_file.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n")

    notifications: list[str] = []
    now_epoch = time.time()

    prev_children = {c.get("id"): c for c in (previous.get("children") or [])}

    for child in current.get("children", []):
        if not child:
            continue

        child_id = child.get("id", "")
        child_status = child.get("status", "")
        child_topic = child.get("topic", "unknown")
        child_pid = child.get("pid")
        child_created = child.get("createdAt", "")

        prev_status = ""
        if has_previous:
            prev = prev_children.get(child_id)
            prev_status = prev.get("status", "") if prev else ""

        # Crash detection: active with a pid that is no longer alive.
        if child_status == "active" and child_pid is not None:
            if not _pid_alive(int(child_pid)):
                def _mark_crashed(tree: dict, _cid: str = child_id) -> None:
                    for c in tree.get("children", []):
                        if c.get("id") == _cid:
                            c["status"] = "crashed"
                            break

                st_write(_mark_crashed)
                notifications.append(f"- **{child_topic}** ({child_id}): crashed — process no longer alive")
                continue

        # Handshake timeout: pending and createdAt older than 30 seconds.
        if child_status == "pending" and child_created:
            created_epoch = _parse_iso(child_created)
            if now_epoch - created_epoch > 30:
                def _mark_failed(tree: dict, _cid: str = child_id) -> None:
                    for c in tree.get("children", []):
                        if c.get("id") == _cid:
                            c["status"] = "failed_to_start"
                            break

                st_write(_mark_failed)
                notifications.append(f"- **{child_topic}** ({child_id}): failed to start — handshake timeout (>30s)")
                continue

        # New result files: compare current vs previous.
        if child_status == "active" and has_previous:
            prev_entry = prev_children.get(child_id)
            prev_files = set((prev_entry.get("resultFiles") or []) if prev_entry else [])
            curr_files = set(child.get("resultFiles") or [])
            new_files = curr_files - prev_files
            if new_files:
                notifications.append(f"- **{child_topic}** ({child_id}): new result files: {', '.join(sorted(new_files))}")

        # Terminated session: report if status changed.
        if child_status == "terminated" and prev_status != "terminated":
            result_files = child.get("resultFiles") or []
            if result_files:
                notifications.append(f"- **{child_topic}** ({child_id}): terminated — result files: {', '.join(result_files)}")
            else:
                notifications.append(f"- **{child_topic}** ({child_id}): terminated")
            continue

        # Report other non-active statuses on first run.
        if not has_previous and child_status not in ("active", "terminated"):
            notifications.append(f"- **{child_topic}** ({child_id}): {child_status}")

    # Only output if there are notable changes.
    if notifications:
        body = "## Child Session Updates\\n\\n"
        for note in notifications:
            body += f"{note}\\n"
        print(json.dumps({"additionalContext": body}))


if __name__ == "__main__":
    main()
