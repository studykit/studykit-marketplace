"""Tests for `_pre_edit` authoring-contract injection in a4_hook.

Covers the policy that contract pointers fire on issue *creation* (new-file
Write) as well as edits to existing files, and that repeated edits to the
same `(file_path, type)` within a session do not re-inject.
"""

from __future__ import annotations

import importlib
import io
import json
import os
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
) -> tuple[int, str]:
    payload = {
        "tool_name": tool_name,
        "tool_input": {"file_path": str(file_path)},
        "session_id": session_id,
    }
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project_dir))
    monkeypatch.setattr(
        hook_module.sys, "stdin", io.StringIO(json.dumps(payload))
    )
    captured = io.StringIO()
    monkeypatch.setattr(hook_module.sys, "stdout", captured)
    rc = hook_module._pre_edit()
    return rc, captured.getvalue()


def _make_a4_layout(project_dir: Path) -> None:
    for folder in ("task", "spike", "bug", "research", "umbrella"):
        (project_dir / "a4" / folder).mkdir(parents=True, exist_ok=True)


def test_inject_on_new_task_file(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    new_file = tmp_path / "a4" / "task" / "1-new.md"
    assert not new_file.exists()

    rc, out = _run_pre_edit(hook_module, monkeypatch, tmp_path, new_file)

    assert rc == 0
    payload = json.loads(out.strip())
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "type: task" in ctx
    assert "frontmatter-common.md" in ctx
    assert "task-authoring.md" in ctx
    assert "issue-family-lifecycle.md" in ctx
    assert "issue-body.md" in ctx


def test_inject_on_new_spike_file(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    new_file = tmp_path / "a4" / "spike" / "42-investigate.md"

    rc, out = _run_pre_edit(hook_module, monkeypatch, tmp_path, new_file)

    assert rc == 0
    payload = json.loads(out.strip())
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "type: spike" in ctx
    assert "spike-authoring.md" in ctx
    assert "issue-family-lifecycle.md" in ctx


def test_dedupe_same_file_same_session(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    new_file = tmp_path / "a4" / "task" / "7-foo.md"

    rc1, out1 = _run_pre_edit(hook_module, monkeypatch, tmp_path, new_file)
    assert rc1 == 0
    assert out1.strip(), "first call should emit context"

    rc2, out2 = _run_pre_edit(hook_module, monkeypatch, tmp_path, new_file)
    assert rc2 == 0
    assert out2 == "", "second call within same session must not re-inject"


def test_dedupe_resets_across_sessions(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    new_file = tmp_path / "a4" / "task" / "9-bar.md"

    rc1, out1 = _run_pre_edit(
        hook_module, monkeypatch, tmp_path, new_file, session_id="s-A"
    )
    rc2, out2 = _run_pre_edit(
        hook_module, monkeypatch, tmp_path, new_file, session_id="s-B"
    )

    assert rc1 == 0 and rc2 == 0
    assert out1.strip() and out2.strip(), (
        "different sessions should each get their own injection"
    )


def test_archive_path_skipped(
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


def test_existing_file_edit_stashes_prestatus_and_injects(
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
        "created: 2026-05-01\n"
        "updated: 2026-05-01\n"
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
    payload = json.loads(out.strip())
    assert "task-authoring.md" in payload["hookSpecificOutput"][
        "additionalContext"
    ]

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


def test_new_file_does_not_create_prestatus_entry(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    new_file = tmp_path / "a4" / "bug" / "5-crash.md"

    rc, _ = _run_pre_edit(
        hook_module, monkeypatch, tmp_path, new_file, session_id="sess-new"
    )

    assert rc == 0
    prestatus_file = (
        tmp_path
        / ".claude"
        / "tmp"
        / "a4-edited"
        / "a4-prestatus-sess-new.json"
    )
    assert not prestatus_file.exists()
