# /// script
# requires-python = ">=3.10"
# ///
"""session_start_bootstrap — SessionStart hook that injects context into child sessions.

Reads session-tree.json to find the child entry matching this session,
then outputs context instructions to stdout for injection into the conversation.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from session_tree import ChildEntry, SessionTree, read_stdin_json, st_find_child, st_write


def _build_context(child: ChildEntry) -> str:
    lines: list[str] = ["## Session Context (injected by orchestrator)", ""]

    if child.topic:
        lines += [f"**Topic:** {child.topic}", ""]

    if child.reference_files:
        lines.append("**Reference files:**")
        for f in child.reference_files:
            lines.append(f"- {f}")
        lines.append("")

    if child.additional_context:
        lines += ["**Additional context:**", child.additional_context, ""]

    if child.result_patterns:
        patterns_str = "`, `".join(child.result_patterns)
        lines += ["**Result file patterns:**", f"Save your deliverables to paths matching: `{patterns_str}`", ""]

    if child.skill:
        lines += [f"**Skill:** Please invoke /{child.skill} to begin.", ""]

    return "\n".join(lines)


def main() -> None:
    if not os.environ.get("SESSION_TREE"):
        return

    data = read_stdin_json()
    session_id: str = data.get("session_id", "")
    transcript_path: str = data.get("transcript_path", "")

    if not session_id:
        return

    child = st_find_child(session_id)
    if child is None:
        return

    context = _build_context(child)

    response = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        },
    }
    print(json.dumps(response, ensure_ascii=False))

    ppid = os.getppid()

    def update(tree: SessionTree) -> None:
        c = tree.find_child(session_id)
        if c:
            c.status = "active"
            c.transcript_path = transcript_path
            c.pid = ppid

    st_write(update)


if __name__ == "__main__":
    main()
