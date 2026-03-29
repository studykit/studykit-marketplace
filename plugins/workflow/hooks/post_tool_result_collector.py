# /// script
# requires-python = ">=3.10"
# ///
"""post_tool_result_collector — PostToolUse hook.

When a child session writes a file, check if it matches resultPatterns
and register it in resultFiles in session-tree.json.
"""

from __future__ import annotations

import fnmatch
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from session_tree import SessionTree, read_stdin_json, st_find_child, st_write


def main() -> None:
    if not os.environ.get("SESSION_TREE"):
        return

    data = read_stdin_json()

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        return

    file_path = (data.get("tool_input") or {}).get("file_path", "")
    if not file_path:
        return

    session_id: str = data.get("session_id", "")
    if not session_id:
        return

    child = st_find_child(session_id)
    if child is None:
        return

    if not child.result_patterns:
        return

    matched = any(fnmatch.fnmatch(file_path, pat) for pat in child.result_patterns)
    if not matched:
        return

    if file_path in child.result_files:
        return

    def update(tree: SessionTree) -> None:
        c = tree.find_child(session_id)
        if c and file_path not in c.result_files:
            c.result_files.append(file_path)

    st_write(update)


if __name__ == "__main__":
    main()
