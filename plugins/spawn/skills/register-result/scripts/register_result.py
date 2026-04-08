# /// script
# requires-python = ">=3.10"
# ///
"""register_result — Register deliverable file paths from a child session.

Usage (invoked by SKILL.md shell injection):
    uv run register_result.py <session_id> <file1> [file2] ...
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "hooks", "lib"))

from session_tree import SessionTree, set_session_tree_path, st_read, st_write


def main() -> None:
    session_tree_env = os.environ.get("SESSION_TREE", "")
    if not session_tree_env:
        print("Error: This command is only available in child sessions.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: /register-result <file1> [file2] ...")
        sys.exit(1)

    session_id = sys.argv[1]
    file_args = sys.argv[2:]

    if not file_args:
        print("Usage: /register-result <file1> [file2] ...")
        sys.exit(1)

    set_session_tree_path(session_tree_env)

    # Validate file existence
    valid_files: list[str] = []
    for f in file_args:
        if Path(f).exists():
            valid_files.append(f)
        else:
            print(f"Warning: File not found, skipping: {f}")

    if not valid_files:
        print("No valid files to register.")
        return

    # Find the child entry and verify it's a child session
    tree = st_read()
    child = tree.find_child(session_id)
    if child is None:
        print(f"Error: Session ID '{session_id}' not found in session tree.")
        sys.exit(1)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def register(t: SessionTree) -> None:
        c = t.find_child(session_id)
        if c is None:
            return
        for f in valid_files:
            if f not in c.result_files:
                c.result_files.append(f)
        c.result_updated_at = now

    st_write(register)

    print(f"Registered {len(valid_files)} deliverable(s):")
    for f in valid_files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
