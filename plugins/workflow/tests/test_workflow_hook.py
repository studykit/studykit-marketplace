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

from workflow_cache import GitHubIssueCache  # noqa: E402
from workflow_command import CommandRequest, CommandResult  # noqa: E402
from workflow_github import DEFAULT_ISSUE_FIELDS, GitHubRepository  # noqa: E402
from workflow_hook import (  # noqa: E402
    extract_issue_numbers,
    record_session_issues,
)
from hook_claude import ClaudeCommonPayload, ClaudePreToolUsePayload  # noqa: E402
from hook_claude import ClaudeSessionStartPayload  # noqa: E402
from hook_claude import main as claude_main  # noqa: E402
from hook_claude import parse_claude_event_payload  # noqa: E402
from hook_claude import session_start as claude_session_start  # noqa: E402
from hook_codex import CodexSessionStartPayload  # noqa: E402
from hook_codex import CodexStopPayload, CodexUserPromptSubmitPayload  # noqa: E402
from hook_codex import parse_codex_event_payload  # noqa: E402
from hook_codex import session_start as codex_session_start  # noqa: E402
from hook_codex import stop, user_prompt_submit  # noqa: E402
from workflow_env import codex_env_file_path  # noqa: E402


class FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CommandResult]):
        self.responses = responses
        self.requests: list[CommandRequest] = []

    def __call__(self, request: CommandRequest) -> CommandResult:
        self.requests.append(request)
        response = self.responses.get(request.args)
        if response is None:
            response = default_github_relationship_response(request)
        if response is None:
            return CommandResult(request=request, returncode=127, stderr="unexpected command")
        return response


def result(args: tuple[str, ...], stdout: str = "", stderr: str = "", returncode: int = 0) -> CommandResult:
    return CommandResult(request=CommandRequest(args=args), returncode=returncode, stdout=stdout, stderr=stderr)


def default_github_relationship_response(request: CommandRequest) -> CommandResult | None:
    args = request.args
    if len(args) < 3 or args[:2] != ("gh", "api"):
        return None

    path = args[2]
    prefix = "repos/studykit/studykit-plugins/issues/"
    if not path.startswith(prefix):
        return None

    suffix = path.removeprefix(prefix)
    issue_number = suffix.split("/", 1)[0]
    try:
        issue_id = int(issue_number) * 1000
    except ValueError:
        return None

    if suffix == issue_number:
        return CommandResult(
            request=request,
            returncode=0,
            stdout=json.dumps(
                {
                    "id": issue_id,
                    "number": int(issue_number),
                    "title": f"Issue {issue_number}",
                    "state": "open",
                    "state_reason": None,
                    "updated_at": "2026-05-14T00:00:00Z",
                }
            ),
        )

    if suffix == f"{issue_number}/parent":
        return CommandResult(request=request, returncode=404, stderr="not found")

    if args[3:] == ("--paginate",) and suffix in {
        f"{issue_number}/sub_issues",
        f"{issue_number}/dependencies/blocked_by",
        f"{issue_number}/dependencies/blocking",
    }:
        return CommandResult(request=request, returncode=0, stdout="[]")

    return None


def _json_object(output: str) -> dict[str, Any]:
    parsed = json.loads(output)
    assert isinstance(parsed, dict)
    return parsed


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


def gh_api_args(*args: str) -> tuple[str, ...]:
    return ("gh", "api", *args)


def empty_relationship_read_args(issue: int | str) -> list[tuple[str, ...]]:
    base = f"repos/studykit/studykit-plugins/issues/{issue}"
    return [
        gh_api_args(base),
        gh_api_args(f"{base}/parent"),
        gh_api_args(f"{base}/sub_issues", "--paginate"),
        gh_api_args(f"{base}/dependencies/blocked_by", "--paginate"),
        gh_api_args(f"{base}/dependencies/blocking", "--paginate"),
    ]


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
    kind: filesystem
    path: workflow/issues
  knowledge:
    kind: filesystem
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


def _write_jira_config(project: Path) -> None:
    config_path = project / ".workflow" / "config.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        """
version: 1
providers:
  issues:
    kind: jira
    site: https://jira.daumkakao.com
    deployment: data-center
    api_version: 2
    project: TM
    issue_type: Task
  knowledge:
    kind: github
issue_id_format: jira
local_projection:
  mode: none
commit_refs:
  enabled: true
  style: provider-native
""".lstrip(),
        encoding="utf-8",
    )


def jira_issue_payload(*, title: str = "Support Jira Data Center hooks") -> dict[str, Any]:
    return {
        "id": "10001",
        "key": "TM-1234",
        "fields": {
            "summary": title,
            "description": "Jira hook body.",
            "labels": ["workflow", "jira"],
            "created": "2026-05-15T09:00:00.000+0900",
            "updated": "2026-05-15T10:00:00.000+0900",
            "status": {"name": "In Progress", "statusCategory": {"key": "indeterminate"}},
            "comment": {"comments": []},
            "issuelinks": [],
        },
    }


def curl_args(url: str) -> tuple[str, ...]:
    return ("curl", "--silent", "--show-error", "--fail", "--request", "GET", "--config", "-", url)


def jira_issue_url(issue: str = "TM-1234") -> str:
    return f"https://jira.daumkakao.com/rest/api/2/issue/{issue}"


def jira_remote_links_url(issue: str = "TM-1234") -> str:
    return f"https://jira.daumkakao.com/rest/api/2/issue/{issue}/remotelink"


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
        monkeypatch.setenv("PLUGIN_ROOT", str(_PLUGIN_ROOT))
        monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    else:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(_PLUGIN_ROOT))
        monkeypatch.delenv("PLUGIN_ROOT", raising=False)

    if payload_update:
        payload.update(payload_update)

    captured = io.StringIO()
    if runtime == "codex":
        codex_event = parse_codex_event_payload(payload)
        assert isinstance(codex_event, CodexSessionStartPayload)
        assert codex_session_start(codex_event, stdout=captured) == 0
    else:
        event_payload = parse_claude_event_payload(payload)
        assert isinstance(event_payload, ClaudeSessionStartPayload)
        assert claude_session_start(event_payload, stdout=captured) == 0
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
def test_session_start_injects_policy_once_per_session_except_clear(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    runtime: str,
) -> None:
    _write_config(tmp_path)

    first = _run_session_start(tmp_path, monkeypatch, runtime=runtime)
    second = _run_session_start(tmp_path, monkeypatch, runtime=runtime)
    clear = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime=runtime,
        payload_update={"source": "clear"},
    )
    after_clear = _run_session_start(tmp_path, monkeypatch, runtime=runtime)
    third = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime=runtime,
        payload_update={"session_id": f"{runtime}-session-2", "turn_id": "turn-2"},
    )

    assert first
    assert second == ""
    assert clear
    assert after_clear == ""
    assert third


def test_session_start_policy_state_is_runtime_scoped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)

    claude_first = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="claude",
        payload_update={"session_id": "shared-session"},
    )
    codex_first = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="codex",
        payload_update={"session_id": "shared-session"},
    )
    claude_second = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="claude",
        payload_update={"session_id": "shared-session"},
    )
    codex_second = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="codex",
        payload_update={"session_id": "shared-session"},
    )

    assert claude_first
    assert codex_first
    assert claude_second == ""
    assert codex_second == ""


def test_session_start_ignores_claude_compact_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)

    compact = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="claude",
        payload_update={"source": "compact"},
    )
    startup = _run_session_start(tmp_path, monkeypatch, runtime="claude")

    assert compact == ""
    assert startup


def test_claude_entrypoint_owns_runtime_for_codex_shaped_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(_PLUGIN_ROOT))
    monkeypatch.delenv("PLUGIN_ROOT", raising=False)

    captured = io.StringIO()
    event_payload = parse_claude_event_payload(
        {
            "session_id": "claude-session",
            "turn_id": "codex-shaped-turn",
            "cwd": str(tmp_path),
            "hook_event_name": "SessionStart",
            "source": "compact",
        }
    )
    assert isinstance(event_payload, ClaudeSessionStartPayload)
    assert claude_session_start(event_payload, stdout=captured) == 0

    assert captured.getvalue() == ""


def test_claude_main_dispatches_from_payload_event_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(_PLUGIN_ROOT))
    monkeypatch.delenv("PLUGIN_ROOT", raising=False)

    captured = io.StringIO()
    assert claude_main(
        ["legacy-subcommand-ignored"],
        payload={
            "session_id": "claude-main-dispatch",
            "cwd": str(tmp_path),
            "hook_event_name": "SessionStart",
            "source": "startup",
        },
        stdout=captured,
    ) == 0

    payload = json.loads(captured.getvalue())
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"


def test_parse_claude_event_payload_builds_event_structures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(_PLUGIN_ROOT))

    session_event = parse_claude_event_payload(
        {
            "session_id": "s1",
            "cwd": str(tmp_path),
            "hook_event_name": "SessionStart",
            "source": "startup",
            "model": "claude-sonnet-4-6",
        }
    )
    assert isinstance(session_event, ClaudeSessionStartPayload)
    assert isinstance(session_event, ClaudeCommonPayload)
    assert session_event.session_id == "s1"
    assert session_event.cwd == str(tmp_path)
    assert session_event.hook_event_name == "SessionStart"
    assert session_event.agent_type is None
    assert not hasattr(session_event, "permission_mode")
    assert not hasattr(session_event, "effort")
    assert not hasattr(session_event, "agent_id")
    assert session_event.source == "startup"
    assert session_event.model == "claude-sonnet-4-6"

    tool_event = parse_claude_event_payload(
        {
            "session_id": "s1",
            "cwd": str(tmp_path),
            "permission_mode": "default",
            "effort": {"level": "medium"},
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "workflow/task.md", "content": "body"},
            "tool_use_id": "toolu_123",
        }
    )
    assert isinstance(tool_event, ClaudePreToolUsePayload)
    assert tool_event.hook_event_name == "PreToolUse"
    assert tool_event.permission_mode == "default"
    assert tool_event.effort == {"level": "medium"}
    assert tool_event.tool_name == "Write"
    assert tool_event.tool_input == {"file_path": "workflow/task.md", "content": "body"}
    assert tool_event.tool_use_id == "toolu_123"
    assert not hasattr(tool_event, "edit_targets")


def test_session_start_clear_uses_documented_source_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)

    first = _run_session_start(tmp_path, monkeypatch, runtime="codex")
    alias_clear = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="codex",
        payload_update={"source": "", "matcher": "clear", "session_start_source": "clear"},
    )
    source_clear = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="codex",
        payload_update={"source": "clear"},
    )

    assert first
    assert alias_clear == ""
    assert source_clear


@pytest.mark.parametrize(
    "payload_update",
    [
        {"source": "agent"},
        {"subagent_type": "workflow-operator"},
        {"parent_session_id": "parent-session"},
    ],
)
def test_codex_session_start_emits_nothing_for_agent_sessions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload_update: dict[str, Any],
) -> None:
    _write_config(tmp_path)

    out = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="codex",
        payload_update=payload_update,
    )

    assert out == ""


@pytest.mark.parametrize(
    "payload_update",
    [
        {"agent_type": "workflow-operator"},
    ],
)
def test_claude_session_start_emits_nothing_for_agent_sessions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload_update: dict[str, Any],
) -> None:
    _write_config(tmp_path)

    out = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="claude",
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
        "Review #45, issue 47, studykit/studykit-plugins#48, "
        "other/repo#49, https://github.com/studykit/studykit-plugins/issues/50, "
        "and Jira keys tm-1234 plus TM-1235."
    )

    assert extract_issue_numbers(text, repo=repo, issue_id_format="github") == ["45", "48", "50"]
    assert extract_issue_numbers(text, issue_id_format="jira") == ["TM-1234", "TM-1235"]


def _hook_env(
    monkeypatch: pytest.MonkeyPatch,
    project: Path,
    *,
    runtime: str = "codex",
) -> None:
    if runtime == "codex":
        monkeypatch.setenv("PLUGIN_ROOT", str(_PLUGIN_ROOT))
        monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    else:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(_PLUGIN_ROOT))
        monkeypatch.delenv("PLUGIN_ROOT", raising=False)


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
    expected_context = [
        "## workflow policy",
        "",
        "Delegate workflow provider/cache/relationship/write-back/comment/authoring-path operations to `workflow-operator`.",
        "For workflow commits, stage changes and write the commit message locally, then ask `workflow-operator` to run commit only.",
        "Do not run raw provider CLIs directly when the operator can handle the operation.",
    ]
    if runtime == "codex":
        expected_context.append(
            "If a `workflow-operator` thread is already open, reuse it for later workflow operations."
        )
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert context == "\n".join(expected_context)
    assert ", and session id" not in context
    assert "session id" not in context
    assert "script recipes" not in context
    assert "hook" not in context.lower()
    assert "wrapper" not in context
    assert "WORKFLOW_*" not in context
    assert "provider/cache metadata, issue relationship metadata, and paths" not in context
    assert "The operator does not interpret content" not in context
    assert "Read and summarize issue, comment, knowledge, or authoring file content directly" not in context
    assert "Workflow issues live in GitHub" not in context
    assert "raw `gh` as its own fallback" not in context
    assert "For cached issue body edits, edit `issue.md` in the cache projection first" not in context
    assert "Configured workflow project:" not in context
    assert "Config file:" not in context
    assert "Workflow plugin root:" not in context
    assert "Issue ID format:" not in context
    assert "Knowledge provider:" not in context
    assert "Local projection:" not in context
    assert "Commit references:" not in context
    assert "Before workflow artifact edits" not in context
    assert "operator should return `NONE`" not in context
    assert "treat `NONE`" not in context
    assert "Use the workflow operator only for workflow operations" not in context
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


def test_claude_session_start_appends_workflow_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    env_file = tmp_path / "claude.env"
    monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))

    _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="claude",
        payload_update={"session_id": "claude-shell-session"},
    )

    content = env_file.read_text(encoding="utf-8")
    assert f"export WORKFLOW={_PLUGIN_ROOT / 'scripts' / 'workflow'}" in content
    assert f"export WORKFLOW_PLUGIN_ROOT={_PLUGIN_ROOT}" in content
    assert f"export WORKFLOW_PROJECT_DIR={tmp_path}" in content
    assert "export WORKFLOW_SESSION_ID=claude-shell-session" in content


def test_codex_session_start_writes_session_export_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)

    _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="codex",
        payload_update={"session_id": "codex-shell-session"},
    )

    env_file = codex_env_file_path(tmp_path, "codex-shell-session")
    content = env_file.read_text(encoding="utf-8")
    assert f"export WORKFLOW={_PLUGIN_ROOT / 'scripts' / 'workflow'}" in content
    assert f"export WORKFLOW_PLUGIN_ROOT={_PLUGIN_ROOT}" in content
    assert f"export WORKFLOW_PROJECT_DIR={tmp_path}" in content
    assert "export WORKFLOW_SESSION_ID=codex-shell-session" in content


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
    expected_context = [
        "## workflow policy",
        "",
        "Delegate workflow provider/cache/relationship/write-back/comment/authoring-path operations to `workflow-operator`.",
        "For workflow commits, stage changes and write the commit message locally, then ask `workflow-operator` to run commit only.",
        "Do not run raw provider CLIs directly when the operator can handle the operation.",
    ]
    if runtime == "codex":
        expected_context.append(
            "If a `workflow-operator` thread is already open, reuse it for later workflow operations."
        )
    assert context == "\n".join(expected_context)
    assert "issue provider: `filesystem`" not in context
    assert "Workflow issues are filesystem-backed local Markdown artifacts" not in context
    assert "The operator does not interpret content" not in context
    assert "Issue ID format:" not in context
    assert "Local projection:" not in context
    assert "Before workflow artifact edits" not in context
    assert "operator should return `NONE`" not in context
    assert "Use the workflow operator only for workflow operations" not in context
    assert "raw GitHub CLI (`gh`)" not in context
    assert "should not run raw `gh`" not in context


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
    assert "## workflow policy" in context
    assert "workflow-operator" in context


def test_non_empty_hook_stdout_is_json_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, projection_path="workflow")

    codex_session = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="codex",
        payload_update={"session_id": "codex-json-session"},
    )
    claude_session = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="claude",
        payload_update={"session_id": "claude-json-session"},
    )

    _hook_env(monkeypatch, tmp_path)
    runner = FakeRunner(
        {
            gh_issue_view_args(45): result(
                gh_issue_view_args(45),
                stdout=json.dumps(issue_payload(45)),
            )
        }
    )
    user_prompt_output = io.StringIO()
    user_prompt_event = parse_codex_event_payload(
        {
            "session_id": "codex-json-prompt",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "hook_event_name": "UserPromptSubmit",
            "prompt": "Inspect #45.",
        },
    )
    assert isinstance(user_prompt_event, CodexUserPromptSubmitPayload)
    assert user_prompt_submit(
        user_prompt_event,
        stdout=user_prompt_output,
        runner=runner,
    ) == 0

    outputs = [
        codex_session,
        claude_session,
        user_prompt_output.getvalue(),
    ]
    for output in outputs:
        assert output
        _json_object(output)


def _write_operator_subagent_transcript(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "session_meta",
                "payload": {
                    "thread_source": "subagent",
                    "agent_role": "workflow-operator",
                    "source": {
                        "subagent": {
                            "agent_name": "workflow-operator",
                            "thread_spawn": {
                                "parent_thread_id": "codex-main-thread",
                                "agent_role": "workflow-operator",
                            },
                        }
                    },
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_session_start_prepares_codex_operator_env_file_and_bootstrap_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    transcript = tmp_path / "subagent-rollout.jsonl"
    _write_operator_subagent_transcript(transcript)

    out = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="codex",
        payload_update={"source": "startup", "transcript_path": str(transcript)},
    )

    payload = json.loads(out)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "## workflow operator bootstrap" in context
    assert f"WORKFLOW={_PLUGIN_ROOT / 'scripts' / 'workflow'}" in context
    assert "hook-state" not in context
    assert "parent_thread_id" not in context
    env_file = codex_env_file_path(tmp_path, "codex-session")
    content = env_file.read_text(encoding="utf-8")
    assert f"export WORKFLOW={_PLUGIN_ROOT / 'scripts' / 'workflow'}" in content
    assert "export WORKFLOW_SESSION_ID=codex-main-thread" in content


def test_session_start_skips_codex_subagent_when_not_operator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    transcript = tmp_path / "subagent-rollout.jsonl"
    _write_subagent_transcript(transcript)

    out = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="codex",
        payload_update={"source": "startup", "transcript_path": str(transcript)},
    )

    assert out == ""


def test_session_start_skips_claude_subagent_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Claude subagent SessionStart persists env but injects no policy."""

    _write_config(tmp_path)
    env_file = tmp_path / "claude.env"
    monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))
    out = _run_session_start(
        tmp_path,
        monkeypatch,
        runtime="claude",
        payload_update={"agent_type": "workflow-operator", "session_id": "claude-subagent-session"},
    )

    assert out == ""
    content = env_file.read_text(encoding="utf-8")
    assert f"export WORKFLOW={_PLUGIN_ROOT / 'scripts' / 'workflow'}" in content
    assert "export WORKFLOW_SESSION_ID=claude-subagent-session" in content


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
    event_payload = parse_codex_event_payload(
        {
            "session_id": "s1",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "hook_event_name": "UserPromptSubmit",
            "prompt": "#45 작업 내용 확인",
        },
    )
    assert isinstance(event_payload, CodexUserPromptSubmitPayload)
    assert user_prompt_submit(event_payload, stdout=captured, runner=runner) == 0

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


def test_user_prompt_injects_github_commit_prefix_hint_without_issue_fetch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    _hook_env(monkeypatch, tmp_path)
    runner = FakeRunner({})

    raw_payload = {
        "session_id": "commit-s1",
        "turn_id": "turn-1",
        "cwd": str(tmp_path),
        "hook_event_name": "UserPromptSubmit",
        "prompt": "Please commit the staged workflow changes.",
    }
    captured = io.StringIO()
    event_payload = parse_codex_event_payload(raw_payload)
    assert isinstance(event_payload, CodexUserPromptSubmitPayload)
    assert user_prompt_submit(event_payload, stdout=captured, runner=runner) == 0

    payload = json.loads(captured.getvalue())
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert context == "\n".join(
        [
            "## Workflow commit",
            "",
            "Stage changes and write the commit message locally, then ask `workflow-operator` to run commit only.",
            "Prefix the subject with the related issue ref.",
        ]
    )

    repeated = io.StringIO()
    repeated_event = parse_codex_event_payload(raw_payload)
    assert isinstance(repeated_event, CodexUserPromptSubmitPayload)
    assert user_prompt_submit(repeated_event, stdout=repeated, runner=runner) == 0

    assert repeated.getvalue() == ""
    assert runner.requests == []


def test_user_prompt_emits_nothing_for_codex_subagent_payload_marker(
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

    captured = io.StringIO()
    event_payload = parse_codex_event_payload(
        {
            "session_id": "subagent-prompt-s1",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "hook_event_name": "UserPromptSubmit",
            "parent_session_id": "parent-session",
            "prompt": "Please inspect #45 and commit.",
        },
    )
    assert isinstance(event_payload, CodexUserPromptSubmitPayload)
    assert user_prompt_submit(event_payload, stdout=captured, runner=runner) == 0

    assert captured.getvalue() == ""
    assert runner.requests == []


def test_user_prompt_emits_nothing_for_codex_subagent_transcript(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    _hook_env(monkeypatch, tmp_path)
    transcript_path = tmp_path / "subagent-rollout.jsonl"
    _write_subagent_transcript(transcript_path)
    runner = FakeRunner(
        {
            gh_issue_view_args(45): result(
                gh_issue_view_args(45),
                stdout=json.dumps(issue_payload(45)),
            )
        }
    )

    captured = io.StringIO()
    event_payload = parse_codex_event_payload(
        {
            "session_id": "subagent-prompt-s2",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "hook_event_name": "UserPromptSubmit",
            "transcript_path": str(transcript_path),
            "prompt": "Please inspect #45 and commit.",
        },
    )
    assert isinstance(event_payload, CodexUserPromptSubmitPayload)
    assert user_prompt_submit(event_payload, stdout=captured, runner=runner) == 0

    assert captured.getvalue() == ""
    assert runner.requests == []


def test_user_prompt_caches_jira_issue_and_injects_snapshot_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_jira_config(tmp_path)
    _hook_env(monkeypatch, tmp_path)
    runner = FakeRunner(
        {
            curl_args(jira_issue_url()): result(
                curl_args(jira_issue_url()),
                stdout=json.dumps(jira_issue_payload(title="Jira hook cache context")),
            ),
            curl_args(jira_remote_links_url()): result(
                curl_args(jira_remote_links_url()),
                stdout="[]",
            ),
        }
    )

    captured = io.StringIO()
    event_payload = parse_codex_event_payload(
        {
            "session_id": "jira-s1",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "hook_event_name": "UserPromptSubmit",
            "prompt": "TM-1234 작업 내용 확인",
        },
    )
    assert isinstance(event_payload, CodexUserPromptSubmitPayload)
    assert user_prompt_submit(event_payload, stdout=captured, runner=runner) == 0

    payload = json.loads(captured.getvalue())
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert payload["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "- TM-1234 → `.workflow-cache/jira/jira.daumkakao.com/issues/TM-1234/snapshot.md`" in context
    assert "#TM-1234" not in context
    assert "Jira hook cache context" not in context
    assert [request.args for request in runner.requests] == [
        curl_args(jira_issue_url()),
        curl_args(jira_remote_links_url()),
    ]
    assert (
        tmp_path
        / ".workflow-cache"
        / "jira"
        / "jira.daumkakao.com"
        / "issues"
        / "TM-1234"
        / "snapshot.md"
    ).is_file()


def test_user_prompt_injects_jira_commit_prefix_hint_without_issue_fetch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_jira_config(tmp_path)
    _hook_env(monkeypatch, tmp_path)
    runner = FakeRunner({})

    captured = io.StringIO()
    event_payload = parse_codex_event_payload(
        {
            "session_id": "jira-commit-s1",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "hook_event_name": "UserPromptSubmit",
            "prompt": "커밋 준비",
        },
    )
    assert isinstance(event_payload, CodexUserPromptSubmitPayload)
    assert user_prompt_submit(event_payload, stdout=captured, runner=runner) == 0

    payload = json.loads(captured.getvalue())
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert context == "\n".join(
        [
            "## Workflow commit",
            "",
            "Stage changes and write the commit message locally, then ask `workflow-operator` to run commit only.",
            "Prefix the subject with the related issue ref.",
        ]
    )
    assert runner.requests == []


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
    raw_payload = {
        "session_id": "s1",
        "turn_id": "turn-1",
        "cwd": str(tmp_path),
        "hook_event_name": "UserPromptSubmit",
        "prompt": "Please inspect #45.",
    }

    first_event = parse_codex_event_payload(raw_payload)
    assert isinstance(first_event, CodexUserPromptSubmitPayload)
    first = io.StringIO()
    assert user_prompt_submit(first_event, stdout=first, runner=runner) == 0
    second_event = parse_codex_event_payload(raw_payload)
    assert isinstance(second_event, CodexUserPromptSubmitPayload)
    second = io.StringIO()
    assert user_prompt_submit(second_event, stdout=second, runner=runner) == 0

    assert first.getvalue()
    assert second.getvalue() == ""


def test_user_prompt_ignores_stop_pending_issue_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    _hook_env(monkeypatch, tmp_path)
    record_session_issues(tmp_path, "s1", ["33", "45"], "pending")
    runner = FakeRunner(
        {
            gh_issue_view_args(39): result(
                gh_issue_view_args(39),
                stdout=json.dumps(issue_payload(39, title="Requested issue")),
            ),
        }
    )

    captured = io.StringIO()
    event_payload = parse_codex_event_payload(
        {
            "session_id": "s1",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "hook_event_name": "UserPromptSubmit",
            "prompt": "#39 작업 내용 확인",
        },
    )
    assert isinstance(event_payload, CodexUserPromptSubmitPayload)
    assert user_prompt_submit(event_payload, stdout=captured, runner=runner) == 0

    payload = json.loads(captured.getvalue())
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert context == "\n".join(
        [
            "## Workflow issue cache",
            "",
            "- #39 → `.workflow-cache/issues/39/issue.md`",
        ]
    )
    assert [request.args for request in runner.requests] == [
        gh_issue_view_args(39),
        *empty_relationship_read_args(39),
    ]
    assert (
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
    event_payload = parse_codex_event_payload(
        {
            "session_id": "s1",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "hook_event_name": "UserPromptSubmit",
            "prompt": "#39 작업 내용 확인",
        },
    )
    assert isinstance(event_payload, CodexUserPromptSubmitPayload)
    assert user_prompt_submit(event_payload, stdout=captured, runner=FakeRunner({})) == 0

    payload = json.loads(captured.getvalue())
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert context == (
        "## Workflow issue cache\n\n"
        "- #39 → `.workflow-cache/issues/39/issue.md` — "
        "parent #28; children #41; blocked_by #33; blocking #45"
    )


def test_stop_does_not_carry_issue_refs_to_next_user_prompt(
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
    stop_event = parse_codex_event_payload(
        {
            "session_id": "s2",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "hook_event_name": "Stop",
            "last_assistant_message": "The assistant referenced #46 during the turn.",
        },
    )
    assert isinstance(stop_event, CodexStopPayload)
    assert stop(stop_event, stdout=captured, runner=runner) == 0

    assert captured.getvalue() == ""
    assert runner.requests == []
    pending_file = (
        tmp_path
        / ".workflow-cache"
        / "hook-state"
        / "workflow-pending-issues-s2.txt"
    )
    assert not pending_file.exists()
    issue_file = (
        tmp_path
        / ".workflow-cache"
        / "issues"
        / "46"
        / "issue.md"
    )
    assert not issue_file.exists()

    prompt_context = io.StringIO()
    follow_event = parse_codex_event_payload(
        {
            "session_id": "s2",
            "turn_id": "turn-2",
            "cwd": str(tmp_path),
            "hook_event_name": "UserPromptSubmit",
            "prompt": "Continue.",
        },
    )
    assert isinstance(follow_event, CodexUserPromptSubmitPayload)
    assert user_prompt_submit(follow_event, stdout=prompt_context, runner=runner) == 0

    assert not issue_file.exists()
    assert not pending_file.exists()
    assert prompt_context.getvalue() == ""


def test_claude_pre_write_guards_github_cache_issue_body_without_local_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(_PLUGIN_ROOT))

    issue_file = tmp_path / ".workflow-cache" / "issues" / "39" / "issue.md"
    issue_file.parent.mkdir(parents=True)
    current_issue_text = """---
schema_version: 1
title: Cached issue
state: open
labels:
  - task
  - workflow
source_updated_at: 2026-05-14T00:00:00Z
---

Current body.
"""
    issue_file.write_text(current_issue_text, encoding="utf-8")
    next_issue_text = current_issue_text.replace("Current body.", "Updated body.")

    captured = io.StringIO()
    assert claude_main(
        payload={
            "session_id": "cache-issue-guard",
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(issue_file),
                "content": next_issue_text,
            },
        },
        stdout=captured,
    ) == 0

    payload = json.loads(captured.getvalue())
    reason = payload["reason"]
    assert payload["decision"] == "block"
    assert "required authoring files have not been read" in reason
    assert f"Target: {issue_file}" in reason
    assert "Artifact type: task" in reason
    assert "Role: issue" in reason
    assert "Provider: github" in reason


def test_claude_pre_write_blocks_creating_github_cache_issue_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(_PLUGIN_ROOT))

    issue_file = tmp_path / ".workflow-cache" / "issues-pending" / "draft-1" / "issue.md"
    issue_text = """---
title: New issue
labels:
  - task
---

Updated body.
"""

    captured = io.StringIO()
    assert claude_main(
        payload={
            "session_id": "cache-issue-guard",
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(issue_file),
                "content": issue_text,
            },
        },
        stdout=captured,
    ) == 0

    payload = json.loads(captured.getvalue())
    reason = payload["reason"]
    assert payload["decision"] == "block"
    assert "projection has not been prepared yet" in reason
    assert f"Target: {issue_file}" in reason
    assert "Ask `workflow-operator` to prepare or refresh the cache projection" in reason


def test_claude_pre_write_blocks_github_cache_issue_frontmatter_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(_PLUGIN_ROOT))

    issue_file = tmp_path / ".workflow-cache" / "issues" / "39" / "issue.md"
    issue_file.parent.mkdir(parents=True)
    issue_file.write_text(
        """---
schema_version: 1
title: Cached issue
state: open
labels:
  - task
  - workflow
source_updated_at: 2026-05-14T00:00:00Z
---

Current body.
""",
        encoding="utf-8",
    )

    captured = io.StringIO()
    assert claude_main(
        payload={
            "session_id": "cache-frontmatter-guard",
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(issue_file),
                "old_string": "title: Cached issue",
                "new_string": "title: Changed issue",
            },
        },
        stdout=captured,
    ) == 0

    payload = json.loads(captured.getvalue())
    reason = payload["reason"]
    assert payload["decision"] == "block"
    assert "provider frontmatter is projection-owned" in reason
    assert "edit only the Markdown body" in reason


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
