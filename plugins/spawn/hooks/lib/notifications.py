"""notifications — shared helpers for the notification queue system.

Provides append-safe JSONL writes and cursor-based reads for
inter-session notifications (session monitor, context drift, relay).
"""

from __future__ import annotations

import fcntl
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def notification_queue_path(session_tree_dir: str, session_id: str, is_main: bool) -> Path:
    """Return the notifications.jsonl path for a session.

    Main session:  <dir>/notifications.jsonl
    Child session: <dir>/<session_id>.notifications.jsonl
    """
    d = Path(session_tree_dir)
    if is_main:
        return d / "notifications.jsonl"
    return d / f"{session_id}.notifications.jsonl"


def cursor_path(queue: Path) -> Path:
    """Return the cursor file path for a given queue file."""
    return queue.with_suffix(".cursor")


def append_notification(queue: Path, entry: dict[str, Any]) -> None:
    """Append a notification entry to a JSONL queue file (append-safe with flock)."""
    if "ts" not in entry:
        entry["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    queue.parent.mkdir(parents=True, exist_ok=True)
    lock = queue.with_suffix(".nlock")
    lock.touch(exist_ok=True)

    with open(lock) as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            with open(queue, "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def read_new_notifications(queue: Path) -> list[dict[str, Any]]:
    """Read new notification entries since the last cursor position.

    Updates the cursor file after reading. Returns [] if no new entries
    or the queue file does not exist.
    """
    if not queue.exists():
        return []

    cur = cursor_path(queue)

    last_line = 0
    if cur.exists():
        try:
            data = json.loads(cur.read_text())
            last_line = data.get("lastLine", 0)
        except (json.JSONDecodeError, ValueError):
            last_line = 0

    try:
        lines = queue.read_text().splitlines()
    except OSError:
        return []

    # Guard: if file was truncated (fewer lines than cursor), reset
    if last_line > len(lines):
        last_line = 0

    new_lines = lines[last_line:]
    if not new_lines:
        return []

    entries: list[dict[str, Any]] = []
    for line in new_lines:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # Update cursor
    cur.parent.mkdir(parents=True, exist_ok=True)
    cur.write_text(json.dumps({"lastLine": len(lines)}) + "\n")

    return entries
