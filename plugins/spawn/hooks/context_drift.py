# /// script
# requires-python = ">=3.10"
# ///
"""context_drift — FileChanged hook that detects modifications to referenced files.

Fires on all file changes in child sessions. Compares the changed file
against the child session's referenceFiles list. If a match is found,
writes a notification to the child's queue and outputs a systemMessage.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from notifications import append_notification, notification_queue_path
from session_tree import read_stdin_json, st_find_child


def main() -> None:
    session_tree_env = os.environ.get("SESSION_TREE", "")
    if not session_tree_env:
        return

    data = read_stdin_json()
    session_id: str = data.get("session_id", "")
    file_path: str = data.get("file_path", "")

    if not session_id or not file_path:
        return

    child = st_find_child(session_id)
    if child is None:
        # session_id is the main session or unknown — not a child
        return

    if not child.reference_files:
        return

    # Check if the changed file matches any reference file
    # Normalize paths for comparison
    changed = Path(file_path).resolve()
    matched = False
    for ref in child.reference_files:
        ref_resolved = Path(ref).resolve()
        if changed == ref_resolved:
            matched = True
            break

    if not matched:
        return

    # Write notification to child's queue
    session_tree_dir = str(Path(session_tree_env).parent)
    queue = notification_queue_path(session_tree_dir, session_id, is_main=False)

    msg = f"Referenced file **{Path(file_path).name}** has been modified externally."
    append_notification(queue, {
        "type": "context_drift",
        "file": file_path,
        "message": msg,
    })

    # Output systemMessage for immediate user visibility
    print(json.dumps({"systemMessage": msg}, ensure_ascii=False))


if __name__ == "__main__":
    main()
