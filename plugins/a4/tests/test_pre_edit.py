"""Tests for `_pre_edit` status snapshot behavior in a4_hook.

PreEdit intentionally performs only status-transition bookkeeping. Authoring
entrypoints are emitted by SessionStart for all runtimes, so PreEdit should not
emit authoring `additionalContext` for either Claude or Codex.
"""

from __future__ import annotations

import importlib
import io
import json
import sys
from pathlib import Path

import pytest


@pytest.fixture
def hook_module(monkeypatch: pytest.MonkeyPatch):
    plugin_root = Path(__file__).resolve().parent.parent
    scripts_dir = plugin_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    if "a4_hook" in sys.modules:
        del sys.modules["a4_hook"]
    return importlib.import_module("a4_hook")


def _run_pre_edit(
    hook_module,
    monkeypatch: pytest.MonkeyPatch,
    project_dir: Path,
    file_path: Path,
    session_id: str = "sess1",
    tool_name: str = "Write",
    extra_payload: dict | None = None,
) -> tuple[int, str]:
    payload = {
        "tool_name": tool_name,
        "tool_input": {"file_path": str(file_path)},
        "session_id": session_id,
    }
    if extra_payload:
        payload.update(extra_payload)
    monkeypatch.setenv("A4_HOOK_RUNTIME", "claude")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project_dir))
    monkeypatch.setattr(hook_module.sys, "stdin", io.StringIO(json.dumps(payload)))
    captured = io.StringIO()
    monkeypatch.setattr(hook_module.sys, "stdout", captured)
    rc = hook_module._pre_edit()
    return rc, captured.getvalue()


def _make_a4_layout(project_dir: Path) -> None:
    for folder in ("task", "spike", "bug", "research", "umbrella"):
        (project_dir / "a4" / folder).mkdir(parents=True, exist_ok=True)


def test_new_file_write_emits_no_authoring_context_and_no_prestatus(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    new_file = tmp_path / "a4" / "task" / "1-new.md"

    rc, out = _run_pre_edit(
        hook_module, monkeypatch, tmp_path, new_file, session_id="sess-new"
    )

    assert rc == 0
    assert out == ""
    prestatus_file = (
        tmp_path
        / ".claude"
        / "tmp"
        / "a4-edited"
        / "a4-prestatus-sess-new.json"
    )
    assert not prestatus_file.exists()


def test_existing_file_edit_stashes_prestatus_without_authoring_context(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    existing = tmp_path / "a4" / "task" / "3-live.md"
    existing.write_text(
        "---\n"
        "type: task\n"
        "id: 3\n"
        "title: Live\n"
        "status: in_progress\n"
        "---\n\n"
        "## Description\nx\n",
        encoding="utf-8",
    )

    rc, out = _run_pre_edit(
        hook_module,
        monkeypatch,
        tmp_path,
        existing,
        session_id="sess-existing",
        tool_name="Edit",
    )

    assert rc == 0
    assert out == ""
    prestatus_file = (
        tmp_path
        / ".claude"
        / "tmp"
        / "a4-edited"
        / "a4-prestatus-sess-existing.json"
    )
    assert prestatus_file.is_file()
    data = json.loads(prestatus_file.read_text(encoding="utf-8"))
    assert data[str(existing)] == "in_progress"


def test_existing_file_without_status_emits_no_context_and_no_prestatus(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "a4").mkdir(parents=True, exist_ok=True)
    wiki_file = tmp_path / "a4" / "domain.md"
    wiki_file.write_text("---\ntype: domain\n---\n\n# Domain\n", encoding="utf-8")

    rc, out = _run_pre_edit(
        hook_module,
        monkeypatch,
        tmp_path,
        wiki_file,
        session_id="sess-wiki",
        tool_name="Edit",
    )

    assert rc == 0
    assert out == ""
    prestatus_file = (
        tmp_path
        / ".claude"
        / "tmp"
        / "a4-edited"
        / "a4-prestatus-sess-wiki.json"
    )
    assert not prestatus_file.exists()


def test_archive_path_emits_no_context(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "a4" / "archive" / "task").mkdir(parents=True, exist_ok=True)
    archived = tmp_path / "a4" / "archive" / "task" / "1-old.md"

    rc, out = _run_pre_edit(hook_module, monkeypatch, tmp_path, archived)

    assert rc == 0
    assert out == ""


def test_non_a4_path_skipped(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = tmp_path / "notes" / "scratch.md"
    other.parent.mkdir(parents=True, exist_ok=True)

    rc, out = _run_pre_edit(hook_module, monkeypatch, tmp_path, other)

    assert rc == 0
    assert out == ""


def test_claude_common_fields_still_emit_no_authoring_context(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Claude Code common payload fields do not re-enable PreEdit guidance."""
    _make_a4_layout(tmp_path)
    existing = tmp_path / "a4" / "task" / "31-common-fields.md"
    existing.write_text(
        "---\n"
        "type: task\n"
        "id: 31\n"
        "title: Common Fields\n"
        "status: in_progress\n"
        "---\n\n"
        "## Description\nx\n",
        encoding="utf-8",
    )

    rc, out = _run_pre_edit(
        hook_module,
        monkeypatch,
        tmp_path,
        existing,
        session_id="sess-claude-common",
        tool_name="Edit",
        extra_payload={
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "model": "claude-sonnet-4-6",
        },
    )

    assert rc == 0
    assert out == ""


def test_claude_file_tool_signal_wins_over_inherited_codex_env(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    monkeypatch.setenv("PLUGIN_ROOT", "/tmp/inherited-codex-plugin-root")
    monkeypatch.setenv("CODEX_THREAD_ID", "inherited-thread-id")
    new_file = tmp_path / "a4" / "task" / "37-inherited-env.md"

    rc, out = _run_pre_edit(
        hook_module,
        monkeypatch,
        tmp_path,
        new_file,
        session_id="sess-claude-inherited-env",
        tool_name="Write",
        extra_payload={
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "model": "claude-sonnet-4-6",
        },
    )

    assert rc == 0
    assert out == ""


def test_claude_relative_file_path_resolves_from_project_dir(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    existing = tmp_path / "a4" / "task" / "39-relative.md"
    existing.write_text(
        "---\n"
        "type: task\n"
        "id: 39\n"
        "title: Relative\n"
        "status: queued\n"
        "---\n\n"
        "## Description\nx\n",
        encoding="utf-8",
    )

    rc, out = _run_pre_edit(
        hook_module,
        monkeypatch,
        tmp_path,
        Path("a4/task/39-relative.md"),
        session_id="sess-claude-relative",
        tool_name="Edit",
        extra_payload={
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "model": "claude-sonnet-4-6",
        },
    )

    assert rc == 0
    assert out == ""
    prestatus_file = (
        tmp_path
        / ".claude"
        / "tmp"
        / "a4-edited"
        / "a4-prestatus-sess-claude-relative.json"
    )
    data = json.loads(prestatus_file.read_text(encoding="utf-8"))
    assert data[str(existing)] == "queued"


def test_codex_apply_patch_emits_no_authoring_context(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.setenv("A4_HOOK_RUNTIME", "codex")
    monkeypatch.setenv("PLUGIN_ROOT", "/tmp/fake-codex-plugin")

    patch_text = (
        "*** Begin Patch\n"
        "*** Add File: a4/task/41-codex.md\n"
        "+---\n"
        "+type: task\n"
        "+id: 41\n"
        "+title: Codex\n"
        "+status: queued\n"
        "+---\n"
        "+\n"
        "+## Description\n"
        "+x\n"
        "*** End Patch\n"
    )
    payload = {
        "tool_name": "apply_patch",
        "tool_input": {"command": patch_text},
        "session_id": "sess-codex-apply-patch",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "model": "gpt-5.5",
        "turn_id": "turn-1",
    }
    monkeypatch.setattr(hook_module.sys, "stdin", io.StringIO(json.dumps(payload)))
    captured = io.StringIO()
    monkeypatch.setattr(hook_module.sys, "stdout", captured)

    rc = hook_module._pre_edit()

    assert rc == 0
    assert captured.getvalue() == ""
