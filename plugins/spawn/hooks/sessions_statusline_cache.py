# /// script
# requires-python = ">=3.10"
# ///
"""sessions_statusline_cache — Write session summary to a cache file for statusline.

Called from session_monitor.py after session-tree.json changes.
Writes a short summary string to /tmp/claude_sessions_<session_id>.txt
that the statusline script can read.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from session_tree import set_session_tree_path, st_read


def update_cache(session_tree_path: str, session_id: str) -> None:
    set_session_tree_path(session_tree_path)
    tree = st_read()

    cache_file = Path(f"/tmp/claude_sessions_{session_id}.txt")

    if not tree.children:
        cache_file.unlink(missing_ok=True)
        return

    status_counts: dict[str, int] = {}
    for child in tree.children:
        s = child.status or "unknown"
        status_counts[s] = status_counts.get(s, 0) + 1

    parts: list[str] = []
    for status, count in status_counts.items():
        parts.append(f"{count} {status}")

    cache_file.write_text(", ".join(parts))
