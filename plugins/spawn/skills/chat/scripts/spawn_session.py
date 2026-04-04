# /// script
# requires-python = ">=3.10"
# dependencies = ["iterm2"]
# ///
"""spawn_session — Spawn a child Claude Code session in a new iTerm2 pane.

Usage:
    uv run "${CLAUDE_SKILL_DIR}/scripts/spawn_session.py" \\
        --session-id <uuid> \\
        --topic "topic name" \\
        [--skill "skill-name"] \\
        [--reference-files "file1.md,file2.md"] \\
        [--additional-context "summary text"] \\
        [--result-patterns "pattern1,pattern2"]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# session_tree library is in hooks/lib/
_HOOKS_LIB = Path(__file__).resolve().parent.parent.parent.parent / "hooks" / "lib"
sys.path.insert(0, str(_HOOKS_LIB))

from iterm2_launcher import launch_pane
from session_tree import ChildEntry, MainSession, SessionTree, set_session_tree_path, st_write


def _parse_csv(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Spawn a child Claude Code session")
    parser.add_argument("--session-id", required=True, help="Main session ID")
    parser.add_argument("--topic", required=True, help="Child session topic")
    parser.add_argument("--skill", default=None, help="Skill to inject")
    parser.add_argument("--reference-files", default="", help="Comma-separated reference file paths")
    parser.add_argument("--additional-context", default="", help="Additional context text")
    parser.add_argument("--result-patterns", default="", help="Comma-separated glob patterns")
    args = parser.parse_args()

    ref_files = _parse_csv(args.reference_files)
    patterns = _parse_csv(args.result_patterns)

    # --- Set up paths ---
    session_dir = Path(f".claude/sessions/{args.session_id}")
    session_tree = session_dir / "session-tree.json"

    set_session_tree_path(str(session_tree))

    # --- Initialize session-tree.json if needed ---
    if not session_tree.exists():
        session_dir.mkdir(parents=True, exist_ok=True)
        initial = SessionTree(main_session=MainSession(id=args.session_id))
        session_tree.write_text(json.dumps(initial.to_dict(), ensure_ascii=False, indent=2) + "\n")

    # --- Generate child session ID ---
    child_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- Add child entry to session-tree.json ---
    child_entry = ChildEntry(
        id=child_id,
        topic=args.topic,
        created_at=created_at,
        skill=args.skill,
        result_patterns=patterns,
        reference_files=ref_files,
        additional_context=args.additional_context or None,
    )

    def add_child(tree: SessionTree) -> None:
        tree.children.append(child_entry)

    st_write(add_child)

    # --- Launch iTerm2 pane ---
    plugin_root = Path(__file__).resolve().parent.parent.parent.parent
    prompt_file = plugin_root / "prompts" / "interactive-child.txt"

    # Detect local dev mode: if plugin_root is not under the plugin cache,
    # pass --plugin-dir so the child session loads the plugin.
    cache_dir = Path.home() / ".claude" / "plugins" / "cache"
    is_local_dev = not str(plugin_root).startswith(str(cache_dir))

    launch_pane(
        session_tree=str(session_tree),
        session_id=child_id,
        prompt_file=str(prompt_file),
        title=args.topic,
        plugin_dir=str(plugin_root) if is_local_dev else None,
    )

    # --- Output ---
    print("Spawned child session:")
    print(f"  ID:    {child_id}")
    print(f"  Topic: {args.topic}")
    print(f"  Tree:  {session_tree}")


if __name__ == "__main__":
    main()
