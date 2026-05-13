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
from workflow_cache import GitHubIssueCache  # noqa: E402
from workflow_command import CommandRequest, CommandResult  # noqa: E402
from workflow_github import DEFAULT_ISSUE_FIELDS, GitHubRepository  # noqa: E402
from workflow_hook import (  # noqa: E402
    extract_issue_numbers,
    post_read,
    pre_write,
    record_session_issues,
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


def _write_filesystem_config(project: Path) -> None:
    config_path = project / ".workflow" / "config.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        """
version: 1
providers:
  issues:
    kind: fs
    path: workflow/issues
  knowledge:
    kind: local
    path: workflow/knowledge
issue_id_format: number
local_projection:
  mode: persistent
  path: workflow
commit_refs:
  enabled: false
""".lstrip(),
        encoding="utf-8",
    )


def _run_session_start(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    runtime: str,
    payload_update: dict[str, Any] | None = None,
) -> str:
    payload = {
        "session_id": f"{runtime}-session",
        "cwd": str(project),
        "hook_event_name": "SessionStart",
        "source": "startup",
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

    if payload_update:
        payload.update(payload_update)

    captured = io.StringIO()
    assert session_start(payload, stdout=captured) == 0
    return captured.getvalue()


def _write_subagent_transcript(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "session_meta",
                "payload": {
                    "thread_source": "subagent",
                    "source": {
                        "subagent": {
                            "thread_spawn": {
                                "parent_thread_id": "parent-thread",
                                "agent_role": "default",
                            }
                        }
                    },
                    "agent_role": "default",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize("runtime", ["claude", "codex"])
def test_session_start_emits_nothing_without_workflow_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    runtime: str,
) -> None:
    out = _run_session_start(tmp_path, monkeypatch, runtime=runtime)

    assert out == ""


@pytest.mark.parametrize("runtime", ["claude", "codex"])
@pytest.mark.parametrize(
    "payload_update",
    [
        {"source": "agent"},
        {"subagent_type": "workflow-operator"},
        {"parent_session_id": "parent-session"},
    ],
)
def test_session_start_emits_nothing_for_agent_sessions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    runtime: str,
    payload_update: dict[str, Any],
) -> None:
    _write_config(tmp_path)

    out = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime=runtime,
        payload_update=payload_update,
    )

    assert out == ""


def test_session_start_emits_nothing_for_codex_subagent_transcript(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    transcript_path = tmp_path / "subagent-rollout.jsonl"
    _write_subagent_transcript(transcript_path)

    out = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="codex",
        payload_update={"source": "startup", "transcript_path": str(transcript_path)},
    )

    assert out == ""


def test_session_start_transcript_agent_metadata_is_codex_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    transcript_path = tmp_path / "subagent-rollout.jsonl"
    _write_subagent_transcript(transcript_path)

    out = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="claude",
        payload_update={"transcript_path": str(transcript_path)},
    )

    assert out != ""


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
    assert "Before documentation or workflow artifact edits" in context
    assert "which authoring file paths must be read" in context
    assert "The operator should return file paths only" in context
    assert "the main assistant reads those files directly" in context
    assert "Use the workflow operator only for workflow operations" in context
    assert "Do not delegate issue or wiki content interpretation to it" in context
    assert "provider/cache metadata, issue relationship metadata, and paths only" in context
    assert "the main assistant reads and summarizes artifact content directly" in context
    assert "delegate to the `workflow-operator` agent first" in context
    assert "any raw GitHub CLI (`gh`) operation" in context
    assert "Pass workflow intent, issue refs, artifact type, and session id" in context
    assert "script command recipes in the main context" in context
    assert "workflow scripts first and raw `gh` only when those scripts cannot support or complete" in context
    assert "main assistant should not run raw `gh` for workflow operations" in context
    assert "report that limitation instead" in context
    assert "Workflow script command recipes are intentionally not injected here" not in context
    assert "Provider writes must use guarded workflow wrappers" not in context
    assert "does not auto-trigger workflow skills or agents" not in context
    assert "WORKFLOW_PLUGIN_ROOT=" not in context
    assert "$WORKFLOW_PLUGIN_ROOT/scripts/" not in context
    assert "scripts/authoring_resolver.py" not in context
    assert "scripts/authoring_ledger.py" not in context
    assert "scripts/authoring_guard.py" not in context
    assert "scripts/workflow_github.py" not in context
    assert "## workflow provider cache context" not in context
    assert "Do not inspect `.workflow-cache`" not in context
    assert "UserPromptSubmit may pre-read" not in context
    assert "Stop may record session-mentioned issue references" not in context
    assert "scripts/workflow_cache_fetch.py" not in context
    assert "scripts/workflow_cache_writeback.py" not in context
    assert "scripts/workflow_cache_comments.py" not in context


@pytest.mark.parametrize("runtime", ["claude", "codex"])
def test_session_start_uses_filesystem_issue_policy_for_local_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    runtime: str,
) -> None:
    _write_filesystem_config(tmp_path)

    out = _run_session_start(tmp_path, monkeypatch, runtime=runtime)

    payload = json.loads(out)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert "Issue provider: `filesystem`" in context
    assert "Issue ID format: `number`" in context
    assert "Local projection: `persistent`" in context
    assert "Configured workflow issues are filesystem-backed local artifacts" in context
    assert "Edit issue Markdown under the configured issue or local projection paths directly" in context
    assert "required authoring contracts are read" in context
    assert "provider cache, write-back, and comment-append delegation does not apply" in context
    assert "Before documentation or workflow artifact edits" in context
    assert "The operator should return file paths only" in context
    assert "Use the workflow operator only for workflow operations" in context
    assert "Do not delegate issue or wiki content interpretation to it" in context
    assert "provider/cache metadata, issue relationship metadata, and paths only" in context
    assert "the main assistant reads and summarizes artifact content directly" in context
    assert "raw GitHub CLI (`gh`)" not in context
    assert "main assistant should not run raw `gh`" not in context


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


def test_user_prompt_caches_issue_and_injects_project_relative_path(
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
    assert "- #45 → `.workflow-cache/issues/45/issue.md`" in context
    assert "open" not in context
    assert "Write-back freshness checks" not in context
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


def test_user_prompt_injects_explicit_issue_and_pending_issues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    _hook_env(monkeypatch, tmp_path)
    record_session_issues(tmp_path, "s1", ["33", "45"], "pending")
    runner = FakeRunner(
        {
            gh_issue_view_args(33): result(
                gh_issue_view_args(33),
                stdout=json.dumps(issue_payload(33, title="Pending issue 33")),
            ),
            gh_issue_view_args(39): result(
                gh_issue_view_args(39),
                stdout=json.dumps(issue_payload(39, title="Requested issue")),
            ),
            gh_issue_view_args(45): result(
                gh_issue_view_args(45),
                stdout=json.dumps(issue_payload(45, title="Pending issue 45")),
            )
        }
    )

    captured = io.StringIO()
    assert user_prompt_submit(
        {
            "session_id": "s1",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "prompt": "#39 작업 내용 확인",
        },
        stdout=captured,
        runner=runner,
    ) == 0

    payload = json.loads(captured.getvalue())
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert context == "\n".join(
        [
            "Workflow issue cache: `.workflow-cache/issues/`",
            "- #33 → `33/issue.md`",
            "- #45 → `45/issue.md`",
            "- #39 → `39/issue.md`",
        ]
    )
    assert [request.args for request in runner.requests] == [
        gh_issue_view_args(33),
        gh_issue_view_args(45),
        gh_issue_view_args(39),
    ]
    assert not (
        tmp_path
        / ".workflow-cache"
        / "hook-state"
        / "workflow-pending-issues-s1.txt"
    ).exists()


def test_user_prompt_injects_compact_relationship_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    _hook_env(monkeypatch, tmp_path)
    repo = GitHubRepository(host="github.com", owner="studykit", name="studykit-plugins")
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=repo)
    cache.write_issue_bundle(repo, issue_payload(39, title="Requested issue"))
    cache.relationships_file(repo, 39).write_text(
        """
schema_version: 1
source_updated_at: 2026-05-14T00:00:00Z
fetched_at: 2026-05-14T00:00:00Z
parent:
  number: 28
children:
  - number: 41
dependencies:
  blocked_by:
    - number: 33
  blocking:
    - number: 45
""".lstrip(),
        encoding="utf-8",
    )

    captured = io.StringIO()
    assert user_prompt_submit(
        {
            "session_id": "s1",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "prompt": "#39 작업 내용 확인",
        },
        stdout=captured,
        runner=FakeRunner({}),
    ) == 0

    payload = json.loads(captured.getvalue())
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert context == (
        "Workflow issue cache:\n"
        "- #39 → `.workflow-cache/issues/39/issue.md` — "
        "parent #28; children #41; blocked_by #33; blocking #45"
    )


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
    assert "- #46 → `.workflow-cache/issues/46/issue.md`" in context
    assert "open" not in context
    assert "Stop hook cache finalization" not in context


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
