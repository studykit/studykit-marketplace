"""Tests for runtime Strategy selection and edit-target normalization."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from a4_hook._runtime import select_hook_strategy  # noqa: E402


def test_claude_file_tool_strategy_wins_over_inherited_codex_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PLUGIN_ROOT", "/tmp/inherited-codex-plugin-root")
    monkeypatch.setenv("CODEX_THREAD_ID", "inherited-thread-id")

    strategy = select_hook_strategy(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "a4/task/1-edit.md"},
        }
    )

    assert strategy.name == "claude"
    assert not strategy.suppress_pretooluse_context
    assert not strategy.aggregate_posttooluse_output


def test_claude_strategy_resolves_relative_file_path(tmp_path: Path) -> None:
    strategy = select_hook_strategy(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "a4/task/2-new.md"},
            "cwd": str(tmp_path),
        }
    )

    targets = strategy.edit_targets({}, str(tmp_path))
    assert targets == []

    targets = strategy.edit_targets(
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "a4/task/2-new.md"},
            "cwd": str(tmp_path),
        },
        str(tmp_path),
    )

    assert len(targets) == 1
    assert targets[0].path == str(tmp_path / "a4" / "task" / "2-new.md")
    assert targets[0].is_new_file_intent


def test_codex_strategy_extracts_apply_patch_targets(tmp_path: Path) -> None:
    payload = {
        "hook_event_name": "PreToolUse",
        "turn_id": "turn-1",
        "tool_name": "apply_patch",
        "tool_input": {
            "command": (
                "*** Begin Patch\n"
                "*** Add File: a4/task/3-new.md\n"
                "+x\n"
                "*** Update File: a4/bug/4-existing.md\n"
                "-old\n"
                "+new\n"
                "*** End Patch\n"
            )
        },
        "cwd": str(tmp_path),
    }

    strategy = select_hook_strategy(payload)
    targets = strategy.edit_targets(payload, str(tmp_path))

    assert strategy.name == "codex"
    assert strategy.suppress_pretooluse_context
    assert strategy.aggregate_posttooluse_output
    assert [(t.path, t.is_new_file_intent) for t in targets] == [
        (str(tmp_path / "a4" / "task" / "3-new.md"), True),
        (str(tmp_path / "a4" / "bug" / "4-existing.md"), False),
    ]
