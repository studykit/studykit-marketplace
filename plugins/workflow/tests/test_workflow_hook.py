"""Tests for workflow SessionStart policy injection."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from authoring_ledger import read_ledger, record_reads  # noqa: E402
from authoring_resolver import resolve_authoring  # noqa: E402
from workflow_command import CommandRequest, CommandResult  # noqa: E402
from workflow_github import DEFAULT_ISSUE_FIELDS, GitHubRepository  # noqa: E402
from workflow_hook import (  # noqa: E402
    extract_issue_numbers,
    post_read,
    pre_write,
    session_start,
    stop,
    user_prompt_submit,
)


class FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CommandResult]):
        self.responses = responses
        self.requests: list[CommandRequest] = []

    def __call__(self, request: CommandRequest) -> CommandResult:
        self.requests.append(request)
        response = self.responses.get(request.args)
        if response is None:
            return CommandResult(request=request, returncode=127, stderr="unexpected command")
        return response


def result(args: tuple[str, ...], stdout: str = "", stderr: str = "", returncode: int = 0) -> CommandResult:
    return CommandResult(request=CommandRequest(args=args), returncode=returncode, stdout=stdout, stderr=stderr)


def gh_issue_view_args(issue: int | str) -> tuple[str, ...]:
    return (
        "gh",
        "issue",
        "view",
        str(issue),
        "--repo",
        "studykit/studykit-plugins",
        "--json",
        ",".join(DEFAULT_ISSUE_FIELDS),
    )


def issue_payload(number: int, *, title: str = "Implement workflow hook cache context") -> dict[str, Any]:
    return {
        "number": number,
        "title": title,
        "state": "OPEN",
        "stateReason": None,
        "body": "Issue body.",
        "labels": [{"name": "workflow"}],
        "updatedAt": "2026-05-14T00:00:00Z",
        "comments": [],
    }


def _write_config(project: Path, *, projection_path: str | None = None) -> None:
    projection = "  mode: none\n"
    if projection_path is not None:
        projection = f"  mode: persistent\n  path: {projection_path}\n"

    config_path = project / ".workflow" / "config.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        f"""
version: 1
providers:
  issues:
    kind: github
    repo: studykit/studykit-plugins
  knowledge:
    kind: github
    path: wiki/workflow
issue_id_format: github
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


def test_extract_issue_numbers_respects_issue_id_format() -> None:
    repo = GitHubRepository(host="github.com", owner="studykit", name="studykit-plugins")
    text = (
        "Review #45, GH-46, issue 47, studykit/studykit-plugins#48, "
        "other/repo#49, and https://github.com/studykit/studykit-plugins/issues/50."
    )

    assert extract_issue_numbers(text, repo=repo, issue_id_format="github") == ["45", "48", "50"]
    assert extract_issue_numbers(text, issue_id_format="jira") == []


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
    assert f"Config file: `{tmp_path / '.workflow/config.yml'}`" in context
    assert f"Workflow plugin root: `{_PLUGIN_ROOT}`" in context
    assert "Issue provider: `github`" in context
    assert "Issue ID format: `github`" in context
    assert "Knowledge provider: `github`" in context
    assert "Local projection: `none`" in context
    assert "Commit references: `provider-native`" in context
    assert "Workflow script command recipes are intentionally not injected here" in context
    assert "Use the `workflow-operator` agent as the operational boundary" in context
    assert "cache-aware provider reads" in context
    assert "guarded GitHub issue writes" in context
    assert "authoring resolver/ledger/guard execution" in context
    assert "main assistant should pass workflow intent, issue refs, artifact type, and session id" in context
    assert "Provider writes must use guarded workflow wrappers" in context
    assert "keep those wrapper calls behind the `workflow-operator` boundary" in context
    assert "does not auto-trigger workflow skills or agents" in context
    assert "WORKFLOW_PLUGIN_ROOT=" not in context
    assert "$WORKFLOW_PLUGIN_ROOT/scripts/" not in context
    assert "scripts/authoring_resolver.py" not in context
    assert "scripts/authoring_ledger.py" not in context
    assert "scripts/authoring_guard.py" not in context
    assert "scripts/workflow_github.py" not in context
    assert "## workflow provider cache context" in context
    assert "Workflow cache root: `.workflow-cache/`" in context
    assert "GitHub issue cache base: `.workflow-cache/issues/`" in context
    assert "Hook-reported issue cache paths are relative to the GitHub issue cache base" in context
    assert "use the `workflow-operator` boundary instead of carrying script commands" in context
    assert "scripts/workflow_cache_fetch.py" not in context
    assert "scripts/workflow_cache_writeback.py" not in context
    assert "scripts/workflow_cache_comments.py" not in context


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
    assert f"Config file: `{tmp_path / '.workflow/config.yml'}`" in context


def test_user_prompt_caches_issue_and_injects_issue_base_relative_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    _hook_env(monkeypatch, tmp_path)
    runner = FakeRunner(
        {
            gh_issue_view_args(45): result(
                gh_issue_view_args(45),
                stdout=json.dumps(issue_payload(45, title="Write-back freshness checks")),
            )
        }
    )

    captured = io.StringIO()
    assert user_prompt_submit(
        {
            "session_id": "s1",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "prompt": "#45 작업 내용 확인",
        },
        stdout=captured,
        runner=runner,
    ) == 0

    payload = json.loads(captured.getvalue())
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert payload["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "- #45 → `45/` — open — Write-back freshness checks" in context
    assert ".workflow-cache" not in context
    assert (
        tmp_path
        / ".workflow-cache"
        / "issues"
        / "45"
        / "issue.md"
    ).is_file()


def test_user_prompt_dedupes_announced_issue_paths_within_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    _hook_env(monkeypatch, tmp_path)
    runner = FakeRunner(
        {
            gh_issue_view_args(45): result(
                gh_issue_view_args(45),
                stdout=json.dumps(issue_payload(45)),
            )
        }
    )
    payload = {
        "session_id": "s1",
        "turn_id": "turn-1",
        "cwd": str(tmp_path),
        "prompt": "Please inspect #45.",
    }

    first = io.StringIO()
    assert user_prompt_submit(payload, stdout=first, runner=runner) == 0
    second = io.StringIO()
    assert user_prompt_submit(payload, stdout=second, runner=runner) == 0

    assert first.getvalue()
    assert second.getvalue() == ""


def test_stop_records_pending_issue_reference_without_provider_read_or_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    _hook_env(monkeypatch, tmp_path)
    runner = FakeRunner(
        {
            gh_issue_view_args(46): result(
                gh_issue_view_args(46),
                stdout=json.dumps(issue_payload(46, title="Stop hook cache finalization")),
            )
        }
    )

    captured = io.StringIO()
    assert stop(
        {
            "session_id": "s2",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "transcript": "The assistant referenced #46 during the turn.",
        },
        stdout=captured,
        runner=runner,
    ) == 0

    assert captured.getvalue() == ""
    assert runner.requests == []
    pending_file = (
        tmp_path
        / ".workflow-cache"
        / "hook-state"
        / "workflow-pending-issues-s2.txt"
    )
    assert pending_file.read_text(encoding="utf-8") == "46\n"
    issue_file = (
        tmp_path
        / ".workflow-cache"
        / "issues"
        / "46"
        / "issue.md"
    )
    assert not issue_file.exists()

    prompt_context = io.StringIO()
    assert user_prompt_submit(
        {
            "session_id": "s2",
            "turn_id": "turn-2",
            "cwd": str(tmp_path),
            "prompt": "Continue.",
        },
        stdout=prompt_context,
        runner=runner,
    ) == 0

    assert issue_file.is_file()
    assert not pending_file.exists()
    payload = json.loads(prompt_context.getvalue())
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert payload["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "- #46 → `46/` — open — Stop hook cache finalization" in context


def test_session_start_emits_nothing_for_invalid_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / ".workflow" / "config.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
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
