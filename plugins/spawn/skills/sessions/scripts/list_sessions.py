# /// script
# requires-python = ">=3.10"
# ///
"""list_sessions — List all child sessions and their status.

Usage (invoked by SKILL.md shell injection):
    uv run list_sessions.py <session_id>
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "hooks", "lib"))

from session_tree import set_session_tree_path, st_read


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: /sessions")
        sys.exit(1)

    session_id = sys.argv[1]

    session_tree_env = os.environ.get("SESSION_TREE", "")
    if session_tree_env:
        set_session_tree_path(session_tree_env)
    else:
        session_tree = Path(f".claude/sessions/{session_id}/session-tree.json")
        if not session_tree.exists():
            print("No child sessions yet.")
            return
        set_session_tree_path(str(session_tree))

    tree = st_read()

    if not tree.children:
        print("No child sessions yet.")
        return

    lines: list[str] = ["Child Sessions:\n"]
    for child in tree.children:
        resume_info = f"  (resumed {child.resume_count}x)" if child.resume_count > 0 else ""
        lines.append(f"  {child.topic:20s} {child.status:16s} {child.created_at}{resume_info}")
        if child.persona:
            lines.append(f"    Persona: {child.persona}")
        if child.reference_files:
            lines.append(f"    References: {', '.join(child.reference_files)}")
        if child.result_files:
            lines.append(f"    Results: {', '.join(child.result_files)}")
        else:
            lines.append(f"    Results: (none)")
        lines.append("")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
