"""Hook runtime strategies for Claude Code and Codex.

The a4 hook entry points stay intentionally small: they choose one runtime
strategy up front, then ask that strategy how to interpret edit targets and how
to shape runtime-specific output behavior.

Agent-specific hook manifests set ``A4_HOOK_RUNTIME`` to ``claude`` or
``codex`` so the dispatcher can identify the host explicitly. Tool names remain
only as a payload-based fallback for direct script tests or older manifests
that have not set the marker yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol


HookRuntimeName = Literal["claude", "codex", "unknown"]

RUNTIME_ENV_VAR = "A4_HOOK_RUNTIME"


@dataclass(frozen=True)
class EditTarget:
    """Normalized markdown edit target.

    ``is_new_file_intent`` is true when the hook payload represents a create
    operation. Claude signals this with ``Write``. Codex signals this through
    ``*** Add File:`` in the ``apply_patch`` body.
    """

    path: str
    is_new_file_intent: bool


class HookRuntimeStrategy(Protocol):
    name: HookRuntimeName
    suppress_pretooluse_context: bool
    aggregate_posttooluse_output: bool
    project_root_env_vars: tuple[str, ...]
    plugin_root_env_vars: tuple[str, ...]

    def edit_targets(self, payload: dict, project_dir: str) -> list[EditTarget]:
        """Return normalized markdown edit targets for this runtime."""


class ClaudeHookStrategy:
    """Claude Code strategy.

    Claude Code file-edit hooks expose one target path at
    ``tool_input.file_path`` and can consume ``PreToolUse`` additionalContext,
    so authoring-contract injection remains enabled.
    """

    name: HookRuntimeName = "claude"
    suppress_pretooluse_context = False
    aggregate_posttooluse_output = False
    project_root_env_vars = ("CLAUDE_PROJECT_DIR",)
    plugin_root_env_vars = ("CLAUDE_PLUGIN_ROOT",)

    _TOOLS = frozenset({"Write", "Edit", "MultiEdit"})

    def edit_targets(self, payload: dict, project_dir: str) -> list[EditTarget]:
        tool_name = payload.get("tool_name")
        if tool_name not in self._TOOLS:
            return []

        tool_input = payload.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            return []

        file_path = tool_input.get("file_path") or ""
        if not isinstance(file_path, str) or not file_path.endswith(".md"):
            return []

        return [
            EditTarget(
                path=_resolve_path(file_path, payload, project_dir),
                is_new_file_intent=tool_name == "Write",
            )
        ]


class CodexHookStrategy:
    """Codex strategy.

    Codex file-edit hooks report the canonical ``apply_patch`` tool. One patch
    can touch several files, and Codex expects hook stdout as one JSON object,
    so ``PostToolUse`` output is aggregated by the caller.
    """

    name: HookRuntimeName = "codex"
    suppress_pretooluse_context = True
    aggregate_posttooluse_output = True
    project_root_env_vars = ()
    plugin_root_env_vars = ("PLUGIN_ROOT",)

    def edit_targets(self, payload: dict, project_dir: str) -> list[EditTarget]:
        if payload.get("tool_name") != "apply_patch":
            return []

        tool_input = payload.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            return []

        command = tool_input.get("command") or ""
        if not isinstance(command, str) or not command:
            return []

        seen: set[str] = set()
        out: list[EditTarget] = []
        for raw_path, is_new in _apply_patch_paths(command):
            path = _resolve_path(raw_path, payload, project_dir)
            if not path.endswith(".md") or path in seen:
                continue
            seen.add(path)
            out.append(EditTarget(path=path, is_new_file_intent=is_new))
        return out


class UnknownHookStrategy:
    """Fail-open strategy for unsupported or non-edit payloads."""

    name: HookRuntimeName = "unknown"
    suppress_pretooluse_context = False
    aggregate_posttooluse_output = False
    project_root_env_vars = ()
    plugin_root_env_vars = ()

    def edit_targets(self, payload: dict, project_dir: str) -> list[EditTarget]:
        return []


CLAUDE_STRATEGY = ClaudeHookStrategy()
CODEX_STRATEGY = CodexHookStrategy()
UNKNOWN_STRATEGY = UnknownHookStrategy()


def select_hook_strategy(payload: dict) -> HookRuntimeStrategy:
    """Pick the runtime strategy for a hook payload.

    Agent-specific hook manifests are expected to set ``A4_HOOK_RUNTIME``.
    When absent, fall back only to hook payload shape; do not infer runtime from
    unrelated inherited environment variables.
    """

    import os

    runtime = os.environ.get(RUNTIME_ENV_VAR, "").strip().lower()
    if runtime == "claude":
        return CLAUDE_STRATEGY
    if runtime == "codex":
        return CODEX_STRATEGY

    tool_name = payload.get("tool_name")
    if tool_name in ClaudeHookStrategy._TOOLS:
        return CLAUDE_STRATEGY
    if tool_name == "apply_patch":
        return CODEX_STRATEGY

    # Turn-scoped Codex hooks include `turn_id` in the wire format.
    if payload.get("turn_id"):
        return CODEX_STRATEGY

    return UNKNOWN_STRATEGY


def project_root_from_payload(payload: dict) -> str:
    """Resolve the active project root for the selected runtime.

    Claude exposes its project root through Claude-prefixed environment
    variables. Codex does not need a project-root environment variable because
    its hook payload includes the official session ``cwd``; for cwd-derived
    paths we normalize to the git root when available and fall back to cwd
    itself.
    """

    import os
    import subprocess

    strategy = select_hook_strategy(payload)
    for env_var in strategy.project_root_env_vars:
        explicit = os.environ.get(env_var)
        if explicit:
            return str(Path(explicit).expanduser().resolve())

    cwd = payload.get("cwd") or os.getcwd()
    if not isinstance(cwd, str) or not cwd:
        return ""
    cwd_path = Path(cwd).expanduser().resolve()

    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd_path), "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        root = proc.stdout.strip()
        if root:
            return str(Path(root).resolve())
    except (OSError, subprocess.CalledProcessError):
        pass

    return str(cwd_path)


def plugin_root_from_payload(payload: dict, fallback: Path) -> Path:
    """Resolve the active plugin root for the selected runtime."""

    import os

    strategy = select_hook_strategy(payload)
    for env_var in strategy.plugin_root_env_vars:
        explicit = os.environ.get(env_var)
        if explicit:
            return Path(explicit).expanduser().resolve()
    return fallback


def _resolve_path(raw_path: str, payload: dict, project_dir: str) -> str:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        cwd = payload.get("cwd") or project_dir
        base = (
            Path(cwd).expanduser()
            if isinstance(cwd, str) and cwd
            else Path(project_dir)
        )
        path = base / path
    return str(path.resolve(strict=False))


def _apply_patch_paths(patch_text: str) -> list[tuple[str, bool]]:
    """Extract file paths from Codex ``apply_patch`` text."""

    out: list[tuple[str, bool]] = []
    for line in patch_text.splitlines():
        if line.startswith("*** Add File: "):
            out.append((line.removeprefix("*** Add File: ").strip(), True))
        elif line.startswith("*** Update File: "):
            out.append((line.removeprefix("*** Update File: ").strip(), False))
        elif line.startswith("*** Delete File: "):
            out.append((line.removeprefix("*** Delete File: ").strip(), False))
        elif line.startswith("*** Move to: "):
            out.append((line.removeprefix("*** Move to: ").strip(), True))
    return out
