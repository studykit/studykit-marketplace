"""Tests for workflow SessionStart policy injection."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from authoring_ledger import read_ledger, record_reads  # noqa: E402
from authoring_resolver import resolve_authoring  # noqa: E402
from workflow_hook import post_read, pre_write, session_start  # noqa: E402


def _write_config(project: Path, *, projection_path: str | None = None) -> None:
    projection = "  mode: none\n"
    if projection_path is not None:
        projection = f"  mode: persistent\n  path: {projection_path}\n"

    (project / "workflow.config.yml").write_text(
        f"""
version: 1
providers:
  issues:
    kind: github
    repo: studykit/studykit-plugins
  knowledge:
    kind: github
    path: wiki/workflow
local_projection:
{projection.rstrip()}
commit_refs:
  enabled: true
  style: provider-native
""".lstrip(),
        encoding="utf-8",
    )


def _run_session_start(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    runtime: str,
) -> str:
    payload = {
        "session_id": f"{runtime}-session",
        "cwd": str(project),
        "hook_event_name": "SessionStart",
    }
    if runtime == "codex":
        payload["turn_id"] = "turn-1"
        monkeypatch.setenv("WORKFLOW_HOOK_RUNTIME", "codex")
        monkeypatch.setenv("PLUGIN_ROOT", str(_PLUGIN_ROOT))
        monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    else:
        monkeypatch.setenv("WORKFLOW_HOOK_RUNTIME", "claude")
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(_PLUGIN_ROOT))
        monkeypatch.delenv("PLUGIN_ROOT", raising=False)

    captured = io.StringIO()
    assert session_start(payload, stdout=captured) == 0
    return captured.getvalue()


@pytest.mark.parametrize("runtime", ["claude", "codex"])
def test_session_start_emits_nothing_without_workflow_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    runtime: str,
) -> None:
    out = _run_session_start(tmp_path, monkeypatch, runtime=runtime)

    assert out == ""


def _hook_env(
    monkeypatch: pytest.MonkeyPatch,
    project: Path,
    *,
    runtime: str = "codex",
) -> None:
    if runtime == "codex":
        monkeypatch.setenv("WORKFLOW_HOOK_RUNTIME", "codex")
        monkeypatch.setenv("PLUGIN_ROOT", str(_PLUGIN_ROOT))
        monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    else:
        monkeypatch.setenv("WORKFLOW_HOOK_RUNTIME", "claude")
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(_PLUGIN_ROOT))
        monkeypatch.delenv("PLUGIN_ROOT", raising=False)


def test_post_read_records_authoring_file_by_absolute_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    state_dir = tmp_path / "state"
    authoring_file = (_PLUGIN_ROOT / "authoring" / "metadata-contract.md").resolve()
    _hook_env(monkeypatch, tmp_path)

    captured = io.StringIO()
    assert post_read(
        {
            "session_id": "s1",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "tool_name": "Read",
            "tool_input": {"file_path": str(authoring_file)},
        },
        stdout=captured,
        state_dir=state_dir,
    ) == 0

    assert captured.getvalue() == ""
    ledger = read_ledger(tmp_path, "s1", state_dir)
    assert ledger.read_authoring_files == (authoring_file,)


def test_pre_write_blocks_local_projection_when_reads_are_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, projection_path="workflow")
    target = tmp_path / "workflow" / "task.md"
    _hook_env(monkeypatch, tmp_path)

    captured = io.StringIO()
    assert pre_write(
        {
            "session_id": "s1",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(target),
                "content": "---\ntype: task\n---\n\n## Description\n\nDo the work.\n",
            },
        },
        stdout=captured,
        state_dir=tmp_path / "state",
    ) == 0

    payload = json.loads(captured.getvalue())
    reason = payload["reason"]
    assert payload["decision"] == "block"
    assert "workflow authoring guard blocked" in reason
    assert f"Target: {target}" in reason
    assert "Artifact type: task" in reason
    assert str(_PLUGIN_ROOT / "authoring" / "metadata-contract.md") in reason
    assert str(_PLUGIN_ROOT / "authoring" / "providers" / "github-issue-authoring.md") in reason


def test_pre_write_allows_local_projection_after_required_reads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, projection_path="workflow")
    state_dir = tmp_path / "state"
    target = tmp_path / "workflow" / "task.md"
    _hook_env(monkeypatch, tmp_path)

    resolution = resolve_authoring("task", project=tmp_path, require_config=True)
    record_reads(resolution.files, project=tmp_path, session_id="s1", state_dir=state_dir)

    captured = io.StringIO()
    assert pre_write(
        {
            "session_id": "s1",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(target),
                "content": "---\ntype: task\n---\n\n## Description\n\nDo the work.\n",
            },
        },
        stdout=captured,
        state_dir=state_dir,
    ) == 0

    assert captured.getvalue() == ""


def test_pre_write_emits_nothing_for_non_workflow_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "workflow" / "task.md"
    _hook_env(monkeypatch, tmp_path)

    captured = io.StringIO()
    assert pre_write(
        {
            "session_id": "s1",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(target),
                "content": "---\ntype: task\n---\n\n## Description\n\nDo the work.\n",
            },
        },
        stdout=captured,
        state_dir=tmp_path / "state",
    ) == 0

    assert captured.getvalue() == ""


@pytest.mark.parametrize("runtime", ["claude", "codex"])
def test_session_start_injects_policy_for_configured_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    runtime: str,
) -> None:
    _write_config(tmp_path)

    out = _run_session_start(tmp_path, monkeypatch, runtime=runtime)

    payload = json.loads(out)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "## workflow authoring policy" in context
    assert f"Config file: `{tmp_path / 'workflow.config.yml'}`" in context
    assert "Issue provider: `github`" in context
    assert "Knowledge provider: `github`" in context
    assert "Local projection: `none`" in context
    assert "Commit references: `provider-native`" in context
    assert str(_PLUGIN_ROOT / "scripts" / "authoring_resolver.py") in context
    assert str(_PLUGIN_ROOT / "scripts" / "authoring_ledger.py") in context
    assert str(_PLUGIN_ROOT / "scripts" / "authoring_guard.py") in context
    assert "`required_authoring_files`" in context
    assert "every path in that list is absolute" in context
    assert "does not auto-trigger workflow skills" in context


def test_session_start_discovers_config_from_nested_project_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    nested = tmp_path / "src" / "feature"
    nested.mkdir(parents=True)

    out = _run_session_start(nested, monkeypatch, runtime="codex")

    payload = json.loads(out)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert f"Config file: `{tmp_path / 'workflow.config.yml'}`" in context


def test_session_start_emits_nothing_for_invalid_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "workflow.config.yml").write_text(
        """
version: 1
providers:
  issues:
    kind: confluence
  knowledge:
    kind: github
""".lstrip(),
        encoding="utf-8",
    )

    out = _run_session_start(tmp_path, monkeypatch, runtime="claude")

    assert out == ""
