#!/usr/bin/env python3
"""Workflow operator subagent start hook.

Dedicated entry point invoked from ``plugins/workflow/agents/workflow-operator.md``
frontmatter when Claude spawns the workflow-operator subagent. The hook emits
the parent session id as ``additionalContext`` so the operator binds its
ledger and guard lookups to the main session's read history.

Codex has no ``SubagentStart`` event, so the codex equivalent rides on
``SessionStart`` inside ``workflow_hook.py`` and uses
``CodexHookContext.subagent_metadata()`` from ``workflow_hook_context`` to
extract the same parent thread id from the subagent rollout transcript.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TextIO

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from workflow_config import WorkflowConfigError, load_workflow_config  # noqa: E402
from workflow_hook_context import HookContext  # noqa: E402

WORKFLOW_OPERATOR_AGENT_NAME = "workflow-operator"


def subagent_start(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
) -> int:
    """SubagentStart entry point for the Claude workflow-operator subagent.

    Emits the parent session id as ``additionalContext`` so the operator
    binds its ledger and guard lookups to the main session's read history.
    The manifest matcher restricts firing to ``workflow-operator``; a
    defensive re-check keeps unrelated payloads silent.
    """

    ctx = HookContext.from_payload(payload) if payload is not None else HookContext.from_stdin()
    output = stdout or sys.stdout

    if not payload_targets_operator(ctx.payload):
        return 0

    project_dir = ctx.project_dir()
    if project_dir is None:
        return 0

    try:
        config = load_workflow_config(project_dir)
    except WorkflowConfigError:
        return 0
    if config is None:
        return 0

    parent_session_id = ctx.session_id()
    if not parent_session_id:
        return 0

    context = build_operator_subagent_context(parent_session_id, config.root)
    ctx.emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": context,
            }
        },
        stdout=output,
    )
    return 0


def build_operator_subagent_context(parent_session_id: str, project_root: Path) -> str:
    """Build the additionalContext block injected when the operator subagent starts."""

    return (
        "## workflow operator session\n\n"
        f"Parent session id: `{parent_session_id}`\n"
        f"Workflow project root: `{project_root}`\n\n"
        "Use this parent session id with `--session` for every authoring "
        "ledger, guard, and provider script invocation in this subagent. Reads "
        "recorded by the main session live under this id; defaulting to the "
        "subagent's own session id or environment variables will check the "
        "wrong ledger and your guarded writes will fail."
    )


def payload_targets_operator(payload: Mapping[str, Any]) -> bool:
    """Return true when the SubagentStart payload targets workflow-operator."""

    for key in ("agent_type", "agent_name", "subagent_type"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip() == WORKFLOW_OPERATOR_AGENT_NAME:
            return True

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, Mapping):
        for key in ("subagent_type", "agent_type", "agent_name"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip() == WORKFLOW_OPERATOR_AGENT_NAME:
                return True
    return False


def agent_name_matches_operator(name: str | None) -> bool:
    return bool(name) and name.strip() == WORKFLOW_OPERATOR_AGENT_NAME


def main() -> int:
    return subagent_start()


if __name__ == "__main__":
    raise SystemExit(main())
