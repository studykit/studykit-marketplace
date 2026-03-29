# /// script
# requires-python = ">=3.10"
# ///
"""spawn_session — Spawn a child Claude Code session in a new iTerm2 tab.

Usage:
    uv run "${CLAUDE_SKILL_DIR}/scripts/spawn_session.py" \
        --session-id <uuid> \
        --topic "topic name" \
        [--skill "skill-name"] \
        [--reference-files "file1.md,file2.md"] \
        [--context-summary "summary text"] \
        [--result-patterns "docs/*.md,A4/**/*.requirement.md"]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# session_tree library is in global/hooks/lib/
_HOOKS_LIB = Path("global/hooks/lib")
sys.path.insert(0, str(_HOOKS_LIB))

from session_tree import st_read, st_write


def _parse_csv(value: str) -> list[str]:
    """Parse a comma-separated string into a trimmed list."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Spawn a child Claude Code session")
    parser.add_argument("--session-id", required=True, help="Main session ID")
    parser.add_argument("--topic", required=True, help="Child session topic")
    parser.add_argument("--skill", default=None, help="Skill to inject")
    parser.add_argument("--reference-files", default="", help="Comma-separated reference file paths")
    parser.add_argument("--context-summary", default="", help="Context summary text")
    parser.add_argument("--result-patterns", default="", help="Comma-separated glob patterns")
    args = parser.parse_args()

    ref_files = _parse_csv(args.reference_files)
    patterns = _parse_csv(args.result_patterns)

    # --- Set up paths ---
    session_dir = Path(f".claude/sessions/{args.session_id}")
    session_tree = session_dir / "session-tree.json"
    os.environ["SESSION_TREE"] = str(session_tree)

    # Reload session_tree module to pick up the new SESSION_TREE value.
    import session_tree as st_mod
    st_mod._SESSION_TREE = str(session_tree)

    # --- Initialize session-tree.json if needed ---
    if not session_tree.exists():
        session_dir.mkdir(parents=True, exist_ok=True)
        initial = {
            "mainSession": {"id": args.session_id, "name": None},
            "children": [],
        }
        session_tree.write_text(json.dumps(initial, ensure_ascii=False, indent=2) + "\n")

    # --- Generate child session ID ---
    child_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- Add child entry to session-tree.json ---
    child_entry = {
        "id": child_id,
        "topic": args.topic,
        "status": "pending",
        "createdAt": created_at,
        "pid": None,
        "skill": args.skill,
        "transcriptPath": None,
        "resultPatterns": patterns,
        "resultFiles": [],
        "referenceFiles": ref_files,
        "contextSummary": args.context_summary,
    }

    def add_child(tree: dict) -> None:
        tree["children"].append(child_entry)

    st_write(add_child)

    # --- Launch iTerm2 pane ---
    iterm2_script = _HOOKS_LIB / "iterm2_launcher.py"
    subprocess.run(
        [
            "uv", "run", str(iterm2_script),
            "--session-tree", str(session_tree),
            "--session-id", child_id,
            "--prompt-file", "global/prompts/interactive-child.txt",
            "--title", args.topic,
        ],
        check=True,
    )

    # --- Output ---
    print("Spawned child session:")
    print(f"  ID:    {child_id}")
    print(f"  Topic: {args.topic}")
    print(f"  Tree:  {session_tree}")


if __name__ == "__main__":
    main()
