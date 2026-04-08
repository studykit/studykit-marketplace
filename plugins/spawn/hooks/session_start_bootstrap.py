# /// script
# requires-python = ">=3.10"
# ///
"""session_start_bootstrap — SessionStart hook that injects context into child sessions.

Reads session-tree.json to find the child entry matching this session,
then outputs context instructions to stdout for injection into the conversation.

For new sessions (pending): injects full context and marks active.
For resumed sessions: updates status to resumed, increments resume_count, no context injection.
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

    if child.bootstrap_prompt_snippet:
        lines += ["**Context:**", child.bootstrap_prompt_snippet, ""]

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

    ppid = os.getppid()

    if child.status == "pending":
        # New session: inject context and mark active
        context = _build_context(child)

        response = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            },
        }
        print(json.dumps(response, ensure_ascii=False))

        def activate(tree: SessionTree) -> None:
            c = tree.find_child(session_id)
            if c:
                c.status = "active"
                c.transcript_path = transcript_path
                c.pid = ppid

        st_write(activate)
    else:
        # Resume: update status, increment resume_count, update pid
        # No context re-injection — conversation history already has it
        def resume(tree: SessionTree) -> None:
            c = tree.find_child(session_id)
            if c:
                c.status = "resumed"
                c.resume_count += 1
                c.pid = ppid
                # transcript_path preserved (same transcript, appended to)

        st_write(resume)


if __name__ == "__main__":
    main()
