#!/usr/bin/env python3
"""Workflow shell environment contract helpers.

Hook adapters and shell wrappers use this module to publish the small
``WORKFLOW_*`` environment contract consumed by workflow script entrypoints.
Host-specific shell markers such as ``CODEX_THREAD_ID`` and
``CLAUDE_CODE_SESSION_ID`` stay at the wrapper boundary.
"""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

WORKFLOW_PLUGIN_ROOT_ENV = "WORKFLOW_PLUGIN_ROOT"
WORKFLOW_PROJECT_DIR_ENV = "WORKFLOW_PROJECT_DIR"
WORKFLOW_SESSION_ID_ENV = "WORKFLOW_SESSION_ID"

CLAUDE_ENV_FILE_ENV = "CLAUDE_ENV_FILE"
CLAUDE_CODE_SESSION_ID_ENV = "CLAUDE_CODE_SESSION_ID"
CODEX_THREAD_ID_ENV = "CODEX_THREAD_ID"

_EXPORT_ORDER = (
    WORKFLOW_PLUGIN_ROOT_ENV,
    WORKFLOW_PROJECT_DIR_ENV,
    WORKFLOW_SESSION_ID_ENV,
)


class WorkflowEnvError(ValueError):
    """Raised when the workflow environment contract cannot be resolved."""


@dataclass(frozen=True)
class ShellRuntime:
    """Runtime marker found in an assistant shell-tool process."""

    name: str
    session_id: str


def workflow_env_values(*, plugin_root: Path, project_dir: Path, session_id: str) -> dict[str, str]:
    """Build the normalized workflow shell environment values."""

    return {
        WORKFLOW_PLUGIN_ROOT_ENV: str(plugin_root.expanduser().resolve()),
        WORKFLOW_PROJECT_DIR_ENV: str(project_dir.expanduser().resolve()),
        WORKFLOW_SESSION_ID_ENV: session_id,
    }


def render_shell_exports(values: Mapping[str, str]) -> str:
    """Render POSIX ``export`` statements for the workflow environment."""

    lines: list[str] = []
    for key in _EXPORT_ORDER:
        if key not in values:
            continue
        lines.append(f"export {key}={shlex.quote(str(values[key]))}")
    return "\n".join(lines) + ("\n" if lines else "")


def append_shell_exports(path: Path, values: Mapping[str, str]) -> bool:
    """Append workflow exports to a host-provided shell environment file."""

    try:
        path = path.expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(render_shell_exports(values))
        return True
    except OSError:
        return False


def write_shell_exports(path: Path, values: Mapping[str, str]) -> bool:
    """Write a complete workflow export file."""

    try:
        path = path.expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_shell_exports(values), encoding="utf-8")
        return True
    except OSError:
        return False


def codex_env_file_path(project: Path, session_id: str) -> Path:
    """Return the session-scoped Codex workflow export file path."""

    from workflow_session_state import session_env_state_path

    path = session_env_state_path(project.expanduser().resolve(), "codex", session_id)
    if path is None:
        raise WorkflowEnvError("Codex session id is required for a workflow env file")
    return path


def write_codex_env_file(
    *,
    project_dir: Path,
    plugin_root: Path,
    codex_session_id: str,
    workflow_session_id: str,
) -> Path | None:
    """Write the Codex export file keyed by the shell-visible Codex session id."""

    if not codex_session_id or not workflow_session_id:
        return None
    path = codex_env_file_path(project_dir, codex_session_id)
    values = workflow_env_values(
        plugin_root=plugin_root,
        project_dir=project_dir,
        session_id=workflow_session_id,
    )
    return path if write_shell_exports(path, values) else None


def append_claude_env_file(
    *,
    env_file: str,
    project_dir: Path,
    plugin_root: Path,
    session_id: str,
) -> bool:
    """Append workflow exports to ``CLAUDE_ENV_FILE`` when Claude provides it."""

    if not env_file or not session_id:
        return False
    return append_shell_exports(
        Path(env_file),
        workflow_env_values(plugin_root=plugin_root, project_dir=project_dir, session_id=session_id),
    )


def workflow_project_dir_from_env(
    *,
    environ: Mapping[str, str] | None = None,
    default: Path | None = None,
) -> Path:
    """Resolve the workflow project directory from ``WORKFLOW_PROJECT_DIR`` or a default."""

    env = environ or os.environ
    value = env.get(WORKFLOW_PROJECT_DIR_ENV)
    if value:
        return Path(value).expanduser().resolve()
    return (default or Path.cwd()).expanduser().resolve()


def workflow_session_id_from_env(*, environ: Mapping[str, str] | None = None) -> str:
    """Resolve the normalized workflow session id from ``WORKFLOW_SESSION_ID``."""

    env = environ or os.environ
    value = env.get(WORKFLOW_SESSION_ID_ENV)
    if value:
        return value
    raise WorkflowEnvError(f"session id is required; pass --session or set {WORKFLOW_SESSION_ID_ENV}")


def detect_shell_runtime(*, environ: Mapping[str, str] | None = None) -> ShellRuntime:
    """Detect the assistant shell runtime from exact session variables only."""

    env = environ or os.environ
    codex_session = env.get(CODEX_THREAD_ID_ENV) or ""
    claude_session = env.get(CLAUDE_CODE_SESSION_ID_ENV) or ""
    if codex_session and claude_session:
        raise WorkflowEnvError(
            f"ambiguous workflow shell runtime: both {CODEX_THREAD_ID_ENV} and "
            f"{CLAUDE_CODE_SESSION_ID_ENV} are set"
        )
    if codex_session:
        return ShellRuntime(name="codex", session_id=codex_session)
    if claude_session:
        return ShellRuntime(name="claude", session_id=claude_session)
    return ShellRuntime(name="", session_id="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    codex_path = subparsers.add_parser("codex-env-path", help="print the Codex workflow env file path")
    codex_path.add_argument("--project", type=Path, default=workflow_project_dir_from_env(), help="project path")
    codex_path.add_argument("--session", required=True, help="Codex session id")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "codex-env-path":
            print(codex_env_file_path(args.project, args.session))
            return 0
    except WorkflowEnvError as exc:
        print(f"workflow env error: {exc}", file=sys.stderr)
        return 2

    parser.error("unhandled command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
