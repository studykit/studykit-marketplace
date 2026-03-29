# /// script
# requires-python = ">=3.10"
# ///
"""session_start_bootstrap — SessionStart hook that injects context into child sessions.

Reads session-tree.json to find the child entry matching this session,
then outputs context instructions to stdout for injection into the conversation.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from session_tree import read_stdin_json, st_find_child, st_write


def main() -> None:
    # Guard: if SESSION_TREE is not set, this is a normal (non-child) session.
    if not os.environ.get("SESSION_TREE"):
        return

    # Read stdin JSON from Claude Code.
    data = read_stdin_json()
    session_id: str = data.get("session_id", "")
    transcript_path: str = data.get("transcript_path", "")

    if not session_id:
        return

    # Find our entry in session-tree.json.
    child = st_find_child(session_id)
    if child is None:
        return

    # Extract fields.
    topic = child.get("topic", "")
    context_summary = child.get("contextSummary", "")
    skill = child.get("skill") or ""
    ref_files: list[str] = child.get("referenceFiles") or []
    result_patterns: list[str] = child.get("resultPatterns") or []

    # --- Inject context via stdout ---
    print("## Session Context (injected by orchestrator)")
    print()

    if topic:
        print(f"**Topic:** {topic}")
        print()

    if ref_files:
        print("**Reference files:**")
        for f in ref_files:
            print(f"- {f}")
        print()

    if context_summary:
        print("**Context from main session:**")
        print(context_summary)
        print()

    if result_patterns:
        patterns_str = "`, `".join(result_patterns)
        print("**Result file patterns:**")
        print(f"Save your deliverables to paths matching: `{patterns_str}`")
        print()

    if skill:
        print(f"**Skill:** Please invoke /{skill} to begin.")
        print()

    # --- Write back metadata to session-tree.json ---
    # Note: os.getppid() is the parent process (Claude Code), since the hook
    # runs as a subprocess.
    ppid = os.getppid()

    def update(tree: dict) -> None:
        for c in tree.get("children", []):
            if c.get("id") == session_id:
                c["status"] = "active"
                c["transcriptPath"] = transcript_path
                c["pid"] = ppid
                break

    st_write(update)


if __name__ == "__main__":
    main()
