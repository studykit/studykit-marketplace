#!/usr/bin/env python3
"""Workflow hook dispatcher.

SessionStart injects a concise workflow authoring policy only when the active
project has a valid ``workflow.config.yml``. The hook never starts workflow
skills and never blocks session startup.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, TextIO

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from workflow_config import WorkflowConfig, WorkflowConfigError, load_workflow_config  # noqa: E402

RUNTIME_ENV_VAR = "WORKFLOW_HOOK_RUNTIME"


def session_start(payload: dict[str, Any] | None = None, *, stdout: TextIO | None = None) -> int:
    """SessionStart entry point. Always exits 0."""

    if payload is None:
        payload = _read_payload()
    output = stdout or sys.stdout

    project_dir = project_dir_from_payload(payload)
    if project_dir is None:
        return 0

    try:
        config = load_workflow_config(project_dir)
    except WorkflowConfigError:
        return 0

    if config is None:
        return 0

    plugin_root = plugin_root_from_payload(payload)
    context = build_session_start_context(config, plugin_root)
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        },
        stdout=output,
    )
    return 0


def build_session_start_context(config: WorkflowConfig, plugin_root: Path) -> str:
    """Build the context block injected for configured workflow projects."""

    resolver = plugin_root / "scripts" / "authoring_resolver.py"
    ledger = plugin_root / "scripts" / "authoring_ledger.py"
    guard = plugin_root / "scripts" / "authoring_guard.py"

    commit_ref = "disabled"
    if config.commit_refs.enabled:
        commit_ref = config.commit_refs.style

    return (
        "## workflow authoring policy\n\n"
        f"Configured workflow project: `{config.root}`\n"
        f"Config file: `{config.path}`\n"
        f"Issue provider: `{config.issues.kind}`\n"
        f"Knowledge provider: `{config.knowledge.kind}`\n"
        f"Local projection: `{config.local_projection.mode}`\n"
        f"Commit references: `{commit_ref}`\n\n"
        "Before creating or editing any workflow issue, knowledge artifact, "
        "or local projection, resolve and read the required authoring contracts.\n\n"
        "Resolver command:\n\n"
        "```bash\n"
        f'python3 "{resolver}" --project "{config.root}" --type <artifact-type> '
        "[--role issue|knowledge] --json\n"
        "```\n\n"
        "Use `--role issue` or `--role knowledge` for dual artifacts such as "
        "`usecase` and `research`.\n\n"
        "The resolver JSON contains `required_authoring_files`, and every path "
        "in that list is absolute. Read every listed file before writing.\n\n"
        "When a wrapper or hook requires ledger enforcement, record reads with:\n\n"
        "```bash\n"
        f'python3 "{ledger}" --project "{config.root}" --session <session-id> '
        "record --json <absolute-authoring-file>...\n"
        "```\n\n"
        "Check write readiness with:\n\n"
        "```bash\n"
        f'python3 "{guard}" --project "{config.root}" --session <session-id> '
        "--type <artifact-type> [--role issue|knowledge] --json\n"
        "```\n\n"
        "SessionStart only injects this policy. It does not auto-trigger "
        "workflow skills."
    )


def project_dir_from_payload(payload: dict[str, Any]) -> Path | None:
    """Resolve the active project directory from host-specific hook inputs."""

    runtime = hook_runtime(payload)
    if runtime == "claude":
        project_env = os.environ.get("CLAUDE_PROJECT_DIR")
        if project_env:
            return Path(project_env).expanduser().resolve()

    cwd = payload.get("cwd") or os.getcwd()
    if not isinstance(cwd, str) or not cwd:
        return None

    cwd_path = Path(cwd).expanduser().resolve()
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd_path), "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return cwd_path

    root = proc.stdout.strip()
    if not root:
        return cwd_path
    return Path(root).expanduser().resolve()


def plugin_root_from_payload(payload: dict[str, Any]) -> Path:
    """Resolve the workflow plugin root from host-specific adapter inputs."""

    runtime = hook_runtime(payload)
    env_names = ("CLAUDE_PLUGIN_ROOT",) if runtime == "claude" else ("PLUGIN_ROOT",)
    for env_name in env_names:
        explicit = os.environ.get(env_name)
        if explicit:
            return Path(explicit).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def hook_runtime(payload: dict[str, Any]) -> str:
    runtime = os.environ.get(RUNTIME_ENV_VAR, "").strip().lower()
    if runtime in {"claude", "codex"}:
        return runtime
    if payload.get("turn_id"):
        return "codex"
    return "unknown"


def emit(payload: dict[str, Any], *, stdout: TextIO | None = None) -> None:
    output = stdout or sys.stdout
    json.dump(payload, output, ensure_ascii=False)
    output.write("\n")


def _read_payload() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
    except OSError:
        return {}
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        return 0
    if args[0] == "session-start":
        return session_start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
