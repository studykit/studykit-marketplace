"""Tests for opt-in `A4_HOOK_TRACE` diagnostics."""

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


def _trace_records(project_dir: Path) -> list[dict]:
    trace_file = project_dir / ".claude" / "tmp" / "a4-edited" / "trace.log"
    assert trace_file.is_file()
    return [
        json.loads(line)
        for line in trace_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_trace_records_no_a4_dir_abort(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(tmp_path / "a4" / "task" / "1-x.md")},
        "session_id": "trace-s1",
    }
    monkeypatch.setenv("A4_HOOK_TRACE", "1")
    monkeypatch.setenv("A4_HOOK_RUNTIME", "claude")
    monkeypatch.setenv("CLAUDE_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(hook_module.sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(hook_module.sys, "stdout", io.StringIO())

    assert hook_module._post_edit() == 0

    records = _trace_records(tmp_path)
    assert records[-1]["cmd"] == "post-edit"
    assert records[-1]["event"] == "abort"
    assert records[-1]["reason"] == "no_a4_dir"


def test_trace_records_outside_a4_skip(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "a4").mkdir()
    outside = tmp_path / "notes.md"
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(outside)},
        "session_id": "trace-s2",
    }
    monkeypatch.setenv("A4_HOOK_TRACE", "yes")
    monkeypatch.setenv("A4_HOOK_RUNTIME", "claude")
    monkeypatch.setenv("CLAUDE_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(hook_module.sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(hook_module.sys, "stdout", io.StringIO())

    assert hook_module._pre_edit() == 0

    records = _trace_records(tmp_path)
    assert records[-1]["cmd"] == "pre-edit"
    assert records[-1]["event"] == "skip"
    assert records[-1]["reason"] == "outside_a4"
