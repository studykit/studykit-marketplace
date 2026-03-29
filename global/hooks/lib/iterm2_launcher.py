# /// script
# requires-python = ">=3.10"
# dependencies = ["iterm2"]
# ///
"""iterm2 — Create a vertical split pane in iTerm2 and run a Claude Code session.

Usage:
    uv run global/hooks/lib/iterm2.py --session-tree <path> --session-id <uuid> --prompt-file <path> [--title <topic>]

Requires: iTerm2 with Python API enabled (Preferences > General > Magic > Enable Python API).
"""

from __future__ import annotations

import argparse
import sys

import iterm2


async def spawn(connection: iterm2.Connection, args: argparse.Namespace) -> None:
    app = await iterm2.async_get_app(connection)
    window = app.current_terminal_window
    if window is None:
        print("Error: No current iTerm2 window found.", file=sys.stderr)
        sys.exit(1)

    # Create a vertical split pane.
    current_session = app.current_terminal_window.current_tab.current_session
    session = await current_session.async_split_pane(vertical=True)

    # Set pane title if provided.
    if args.title:
        await session.async_set_name(args.title)

    # Run claude in the new tab.
    cmd = (
        f"SESSION_TREE='{args.session_tree}' "
        f"claude --session-id {args.session_id} "
        f"--append-system-prompt-file '{args.prompt_file}'"
    )
    await session.async_send_text(cmd + "\n")

    print("Spawned iTerm2 pane successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch a child Claude Code session in an iTerm2 vertical pane")
    parser.add_argument("--session-tree", required=True, help="Path to session-tree.json")
    parser.add_argument("--session-id", required=True, help="Child session UUID")
    parser.add_argument("--prompt-file", required=True, help="Path to system prompt file")
    parser.add_argument("--title", default="", help="Tab title")
    args = parser.parse_args()

    iterm2.run_until_complete(lambda conn: spawn(conn, args))


if __name__ == "__main__":
    main()
