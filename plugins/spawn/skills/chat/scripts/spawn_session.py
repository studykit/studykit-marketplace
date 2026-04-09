# /// script
# requires-python = ">=3.10"
# dependencies = ["iterm2"]
# ///
"""spawn_session — Spawn or resume a child Claude Code session in a new iTerm2 pane.

Usage (spawn):
    uv run "${CLAUDE_SKILL_DIR}/scripts/spawn_session.py" \\
        --session-id <uuid> \\
        --topic "topic name" \\
        [--persona "discuss"] \\
        [--reference-files "file1.md,file2.md"] \\
        [--bootstrap-prompt-snippet "summary text"]

Usage (resume):
    uv run "${CLAUDE_SKILL_DIR}/scripts/spawn_session.py" \\
        --session-id <uuid> \\
        --resume "topic name"
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

from iterm2_launcher import activate_pane, launch_pane
from session_tree import ChildEntry, MainSession, SessionTree, set_session_tree_path, st_read, st_write


def _parse_csv(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# --- Orchestrator instructions appended to every Session System Prompt ---

_ORCHESTRATOR_INSTRUCTIONS = """
## Orchestrator Instructions

You are running as a **child session** managed by an orchestrator. Follow these rules:

### Deliverable Registration

- When the user signals they want to wrap up, recall files you created or modified during this session.
- Suggest registering them as deliverables: "Should I register these files as results?"
- On user approval, invoke `/register-result <file1> <file2> ...` to register them.
- The user can also request registration at any time during the session.

### Session Termination

- The user decides when the conversation ends. Never conclude, wrap up, or suggest ending the session on your own.
- When the user wants to end the session, summarize what was accomplished.
- If files were created or modified, prompt the user about registering deliverables before ending.
- **Never prevent the user from ending the session.** The user always has the final say.
"""


def _generate_prompt(persona: str, child_id: str, session_dir: Path) -> Path:
    """Generate a Session System Prompt file (persona + orchestrator instructions)."""
    plugin_root = Path(__file__).resolve().parent.parent.parent.parent
    persona_file = plugin_root / "prompts" / f"{persona}.txt"

    if not persona_file.exists():
        print(f"Error: Persona file not found: {persona_file}", file=sys.stderr)
        sys.exit(1)

    persona_content = persona_file.read_text()
    combined = persona_content.rstrip() + "\n" + _ORCHESTRATOR_INSTRUCTIONS

    prompt_path = session_dir / f"{child_id}.prompt.txt"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(combined)
    return prompt_path


def _get_plugin_dir() -> str | None:
    """Return --plugin-dir if running in local dev mode, else None."""
    plugin_root = Path(__file__).resolve().parent.parent.parent.parent
    cache_dir = Path.home() / ".claude" / "plugins" / "cache"
    is_local_dev = not str(plugin_root).startswith(str(cache_dir))
    return str(plugin_root) if is_local_dev else None


def _do_resume(args: argparse.Namespace, session_tree: Path, session_dir: Path) -> None:
    """Handle the resume flow for an existing child session."""
    tree = st_read()
    if not tree.children:
        print("Error: No child sessions found.")
        sys.exit(1)

    # Find by topic
    matches = [c for c in tree.children if c.topic == args.resume]
    if not matches:
        print(f"Error: No child session with topic '{args.resume}'.")
        print("\nAvailable sessions:")
        for c in tree.children:
            print(f"  {c.topic:20s} {c.status:16s} {c.created_at}")
        sys.exit(1)

    # Pick the most recent match
    child = matches[-1]

    if child.status == "failed_to_start":
        print(f"Error: Session '{child.topic}' failed to start (no transcript). Cannot resume.")
        print("You can create a new session with the same topic instead.")
        sys.exit(1)

    if child.status == "pending":
        print(f"Error: Session '{child.topic}' is still starting up. Please wait.")
        sys.exit(1)

    # Active/resumed + pid alive → just activate existing pane
    if child.status in ("active", "resumed") and child.pid is not None and _pid_alive(child.pid):
        print(f"Session '{child.topic}' is already running. Activating its pane...")
        activate_pane(child.topic)
        return

    # Otherwise (terminated, crashed, or stale active/resumed) → relaunch with --resume
    prompt_path = _generate_prompt(child.persona or "discuss", child.id, session_dir)

    launch_pane(
        session_tree=str(session_tree),
        session_id=child.id,
        prompt_file=str(prompt_path),
        title=child.topic,
        plugin_dir=_get_plugin_dir(),
        resume=True,
    )

    print(f"Resumed child session:")
    print(f"  ID:    {child.id}")
    print(f"  Topic: {child.topic}")


def _do_spawn(args: argparse.Namespace, session_tree: Path, session_dir: Path) -> None:
    """Handle the spawn flow for a new child session."""
    # --- Nesting guard ---
    session_tree_env = os.environ.get("SESSION_TREE", "")
    if session_tree_env:
        tree = st_read()
        if tree.main_session and tree.main_session.id != args.session_id:
            print("Error: Child sessions cannot spawn further children.")
            sys.exit(1)

    set_session_tree_path(str(session_tree))

    # --- Initialize session-tree.json if needed ---
    if not session_tree.exists():
        session_dir.mkdir(parents=True, exist_ok=True)
        initial = SessionTree(main_session=MainSession(id=args.session_id))
        session_tree.write_text(json.dumps(initial.to_dict(), ensure_ascii=False, indent=2) + "\n")

    # --- Topic uniqueness check ---
    tree = st_read()
    blocking = [c for c in tree.children
                if c.topic == args.topic and c.status in ("active", "resumed", "pending")]
    if blocking:
        print(f"Error: A child session with topic '{args.topic}' is already {blocking[0].status}.")
        print("Choose a different topic name, or resume the existing session.")
        sys.exit(1)

    # --- Generate child session ---
    child_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ref_files = _parse_csv(args.reference_files)
    persona = args.persona or "discuss"

    child_entry = ChildEntry(
        id=child_id,
        topic=args.topic,
        created_at=created_at,
        persona=persona,
        reference_files=ref_files,
        bootstrap_prompt_snippet=args.bootstrap_prompt_snippet or None,
    )

    def add_child(t: SessionTree) -> None:
        t.children.append(child_entry)

    st_write(add_child)

    # --- Generate Session System Prompt ---
    prompt_path = _generate_prompt(persona, child_id, session_dir)

    # --- Launch iTerm2 pane ---
    launch_pane(
        session_tree=str(session_tree),
        session_id=child_id,
        prompt_file=str(prompt_path),
        title=args.topic,
        plugin_dir=_get_plugin_dir(),
    )

    print("Spawned child session:")
    print(f"  ID:    {child_id}")
    print(f"  Topic: {args.topic}")
    print(f"  Tree:  {session_tree}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Spawn or resume a child Claude Code session")
    parser.add_argument("--session-id", required=True, help="Main session ID")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--topic", help="Child session topic (for spawn)")
    group.add_argument("--resume", help="Topic of session to resume")

    parser.add_argument("--persona", default="discuss", help="Persona file name (default: discuss)")
    parser.add_argument("--reference-files", default="", help="Comma-separated reference file paths")
    parser.add_argument("--bootstrap-prompt-snippet", default="", help="Context summary from main session")
    args = parser.parse_args()

    session_dir = Path(f".claude/sessions/{args.session_id}")
    session_tree = session_dir / "session-tree.json"

    set_session_tree_path(str(session_tree))

    if args.resume:
        _do_resume(args, session_tree, session_dir)
    else:
        _do_spawn(args, session_tree, session_dir)


if __name__ == "__main__":
    main()
