# /// script
# requires-python = ">=3.10"
# ///
"""session_end_collector — SessionEnd hook.

Marks the child session as "terminated" in session-tree.json.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from session_tree import read_stdin_json, st_find_child, st_write


def main() -> None:
    if not os.environ.get("SESSION_TREE"):
        return

    data = read_stdin_json()
    session_id: str = data.get("session_id", "")
    if not session_id:
        return

    # Find self — exit if not a managed child.
    if st_find_child(session_id) is None:
        return

    def update(tree: dict) -> None:
        for c in tree.get("children", []):
            if c.get("id") == session_id:
                c["status"] = "terminated"
                break

    st_write(update)


if __name__ == "__main__":
    main()
