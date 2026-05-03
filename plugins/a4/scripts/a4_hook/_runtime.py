"""Hook runtime strategies for Claude Code and Codex.

The a4 hook entry points stay intentionally small: they choose one runtime
strategy up front, then ask that strategy how to interpret edit targets and how
to shape runtime-specific output behavior.

Tool names are treated as the strongest runtime signal. This keeps Claude Code
safe when it is launched from an environment that happens to inherit Codex
variables such as ``PLUGIN_ROOT`` or ``CODEX_THREAD_ID``: if Claude sends a
``Write`` / ``Edit`` / ``MultiEdit`` payload, the Claude strategy wins.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol


HookRuntimeName = Literal["claude", "codex", "unknown"]


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

    def edit_targets(self, payload: dict, project_dir: str) -> list[EditTarget]:
        return []


CLAUDE_STRATEGY = ClaudeHookStrategy()
CODEX_STRATEGY = CodexHookStrategy()
UNKNOWN_STRATEGY = UnknownHookStrategy()


def select_hook_strategy(payload: dict) -> HookRuntimeStrategy:
    """Pick the runtime strategy for a hook payload.

    The ordering intentionally protects Claude Code first for file-edit hooks:
    Claude's ``Write`` / ``Edit`` / ``MultiEdit`` tools win even if Codex
    environment variables leaked into the process.
    """

    import os

    tool_name = payload.get("tool_name")
    if tool_name in ClaudeHookStrategy._TOOLS:
        return CLAUDE_STRATEGY
    if tool_name == "apply_patch":
        return CODEX_STRATEGY

    # Turn-scoped Codex hooks include `turn_id` in the wire format.
    if payload.get("turn_id"):
        return CODEX_STRATEGY

    # Codex plugin hooks set PLUGIN_ROOT / PLUGIN_DATA. Claude-prefixed plugin
    # variables are compatibility aliases in Codex, so they are not used here.
    if os.environ.get("PLUGIN_ROOT") or os.environ.get("PLUGIN_DATA"):
        return CODEX_STRATEGY

    if (
        os.environ.get("CLAUDE_PROJECT_DIR")
        or os.environ.get("CLAUDE_CODE_SHELL")
        or os.environ.get("CLAUDE_ENV_FILE")
    ):
        return CLAUDE_STRATEGY

    if os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_CI"):
        return CODEX_STRATEGY

    return UNKNOWN_STRATEGY


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
