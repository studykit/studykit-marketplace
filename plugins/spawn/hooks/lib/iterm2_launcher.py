# /// script
# requires-python = ">=3.10"
# dependencies = ["iterm2"]
# ///
"""iterm2_launcher — Create a vertical split pane in iTerm2 and run a Claude Code session.

Usage:
    uv run iterm2_launcher.py \\
        --session-tree <path> --session-id <uuid> --prompt-file <path> [--title <topic>]

Requires: iTerm2 with Python API enabled (Preferences > General > Magic > Enable Python API).
"""

from __future__ import annotations

import argparse
import sys

import iterm2


async def _spawn(connection: iterm2.Connection, args: argparse.Namespace) -> None:
    app = await iterm2.async_get_app(connection)
    window = app.current_terminal_window
    if window is None:
        print("Error: No current iTerm2 window found.", file=sys.stderr)
        sys.exit(1)

    current_session = window.current_tab.current_session
    session = await current_session.async_split_pane(vertical=True)

    if args.title:
        await session.async_set_name(args.title)

    plugin_dir_flag = f"--plugin-dir '{args.plugin_dir}' " if args.plugin_dir else ""

    if args.resume:
        cmd = (
            f"SESSION_TREE='{args.session_tree}' "
            f"claude --resume {args.session_id} "
            f"{plugin_dir_flag}"
            f"--append-system-prompt-file '{args.prompt_file}'"
        )
    else:
        cmd = (
            f"SESSION_TREE='{args.session_tree}' "
            f"claude --session-id {args.session_id} "
            f"{plugin_dir_flag}"
            f"--append-system-prompt-file '{args.prompt_file}'"
        )
    await session.async_send_text(cmd + "\n")

    print("Spawned iTerm2 pane successfully.")


async def _activate(connection: iterm2.Connection, topic: str) -> bool:
    app = await iterm2.async_get_app(connection)
    for window in app.terminal_windows:
        for tab in window.tabs:
            for session in tab.sessions:
                name = await session.async_get_variable("user.name")
                if name == topic:
                    await window.async_activate()
                    await tab.async_select()
                    await session.async_activate()
                    return True
    return False


def launch_pane(
    *,
    session_tree: str,
    session_id: str,
    prompt_file: str,
    title: str = "",
    plugin_dir: str | None = None,
    resume: bool = False,
) -> None:
    """Launch a child Claude Code session in an iTerm2 vertical split pane."""
    ns = argparse.Namespace(
        session_tree=session_tree,
        session_id=session_id,
        prompt_file=prompt_file,
        title=title,
        plugin_dir=plugin_dir,
        resume=resume,
    )
    iterm2.run_until_complete(lambda conn: _spawn(conn, ns))


def activate_pane(topic: str) -> bool:
    """Activate an existing iTerm2 pane by its session name. Returns True if found."""
    result: list[bool] = []

    async def _run(conn: iterm2.Connection) -> None:
        result.append(await _activate(conn, topic))

    iterm2.run_until_complete(_run)
    return result[0] if result else False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Launch a child Claude Code session in an iTerm2 vertical pane",
    )
    parser.add_argument("--session-tree", required=True, help="Path to session-tree.json")
    parser.add_argument("--session-id", required=True, help="Child session UUID")
    parser.add_argument("--prompt-file", required=True, help="Path to system prompt file")
    parser.add_argument("--title", default="", help="Pane title")
    parser.add_argument("--plugin-dir", default=None, help="Plugin directory for local dev mode")
    parser.add_argument("--resume", action="store_true", help="Resume an existing session")
    args = parser.parse_args()

    launch_pane(
        session_tree=args.session_tree,
        session_id=args.session_id,
        prompt_file=args.prompt_file,
        title=args.title,
        plugin_dir=args.plugin_dir,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
