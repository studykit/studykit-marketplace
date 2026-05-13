"""Tests for GitHub workflow wrappers."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_command import CommandRequest, CommandResult, MissingCommandError  # noqa: E402
from workflow_command import WorkflowCommandError  # noqa: E402
from workflow_github import DEFAULT_ISSUE_FIELDS, GitHubGuardError, GitHubParseError  # noqa: E402
from workflow_github import GitHubVerificationError  # noqa: E402
from workflow_github import close_issue, comment_issue, edit_issue_body  # noqa: E402
from workflow_github import issue_body_edit_history, issue_timeline  # noqa: E402
from workflow_github import parse_github_remote_url, resolve_github_repository, view_issue  # noqa: E402
from workflow_github import reopen_issue  # noqa: E402


class FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CommandResult | Exception]):
        self.responses = responses
        self.requests: list[CommandRequest] = []

    def __call__(self, request: CommandRequest) -> CommandResult:
        self.requests.append(request)
        response = self.responses.get(request.args)
        if isinstance(response, Exception):
            raise response
        if response is None:
            return CommandResult(request=request, returncode=127, stderr="unexpected command")
        return response


def result(args: tuple[str, ...], stdout: str = "", stderr: str = "", returncode: int = 0) -> CommandResult:
    return CommandResult(request=CommandRequest(args=args), returncode=returncode, stdout=stdout, stderr=stderr)


def gh_args(project: Path, *args: str) -> tuple[str, ...]:
    _ = project
    return ("gh", *args)


def git_args(project: Path, *args: str) -> tuple[str, ...]:
    return ("git", "-C", str(project.resolve(strict=False)), *args)


def gh_issue_view_args(issue: int | str, fields: tuple[str, ...]) -> tuple[str, ...]:
    return (
        "gh",
        "issue",
        "view",
        str(issue),
        "--repo",
        "studykit/studykit-plugins",
        "--json",
        ",".join(fields),
    )


def allow_guard(calls: list[tuple[str, Mapping[str, Any]]]):
    def guard(operation: str, payload: Mapping[str, Any]) -> None:
        calls.append((operation, payload))

    return guard


def _config_path(project: Path) -> Path:
    path = project / ".workflow" / "config.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def test_resolves_github_repository_from_workflow_config(tmp_path: Path) -> None:
    _config_path(tmp_path).write_text(
        """
version: 1
providers:
  issues:
    kind: github
    repo: studykit/studykit-plugins
  knowledge:
    kind: github
""".lstrip(),
        encoding="utf-8",
    )

    repo = resolve_github_repository(tmp_path)

    assert repo.host == "github.com"
    assert repo.slug == "studykit/studykit-plugins"


@pytest.mark.parametrize(
    ("remote_url", "host", "slug"),
    [
        ("git@github.com:studykit/studykit-plugins.git", "github.com", "studykit/studykit-plugins"),
        ("https://github.example.com/studykit/studykit-plugins.git", "github.example.com", "studykit/studykit-plugins"),
        ("ssh://git@github.com/studykit/studykit-plugins.git", "github.com", "studykit/studykit-plugins"),
    ],
)
def test_parses_common_github_remote_urls(remote_url: str, host: str, slug: str) -> None:
    repo = parse_github_remote_url(remote_url)

    assert repo.host == host
    assert repo.slug == slug


def test_view_issue_uses_gh_issue_view_with_structured_fields(tmp_path: Path) -> None:
    runner = FakeRunner(
        {
            git_args(tmp_path, "remote", "get-url", "origin"): result(
                git_args(tmp_path, "remote", "get-url", "origin"),
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            ),
            gh_args(
                tmp_path,
                "issue",
                "view",
                "38",
                "--repo",
                "studykit/studykit-plugins",
                "--json",
                ",".join(DEFAULT_ISSUE_FIELDS),
            ): result(
                gh_args(
                    tmp_path,
                    "issue",
                    "view",
                    "38",
                    "--repo",
                    "studykit/studykit-plugins",
                    "--json",
                    ",".join(DEFAULT_ISSUE_FIELDS),
                ),
                stdout=json.dumps({"number": 38, "title": "Add wrappers"}),
            ),
        }
    )

    issue = view_issue("#38", project=tmp_path, runner=runner)

    assert issue["number"] == 38
    assert issue["repository"]["slug"] == "studykit/studykit-plugins"


def test_timeline_flattens_paginated_json_arrays(tmp_path: Path) -> None:
    runner = FakeRunner(
        {
            git_args(tmp_path, "remote", "get-url", "origin"): result(
                git_args(tmp_path, "remote", "get-url", "origin"),
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            ),
            gh_args(
                tmp_path,
                "api",
                "repos/studykit/studykit-plugins/issues/37/timeline",
                "--paginate",
            ): result(
                gh_args(
                    tmp_path,
                    "api",
                    "repos/studykit/studykit-plugins/issues/37/timeline",
                    "--paginate",
                ),
                stdout='[{"event":"labeled"}]\n[{"event":"sub_issue_added"}]\n',
            ),
        }
    )

    timeline = issue_timeline(37, project=tmp_path, runner=runner)

    assert [event["event"] for event in timeline["events"]] == ["labeled", "sub_issue_added"]


def test_body_edit_history_uses_graphql_user_content_edits(tmp_path: Path) -> None:
    graphql_response = {
        "data": {
            "repository": {
                "issue": {
                    "number": 37,
                    "userContentEdits": {
                        "nodes": [{"editedAt": "2026-05-13T00:00:00Z", "diff": "@@"}]
                    },
                }
            }
        }
    }
    runner = FakeRunner(
        {
            git_args(tmp_path, "remote", "get-url", "origin"): result(
                git_args(tmp_path, "remote", "get-url", "origin"),
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            ),
        }
    )

    def graphql_runner(request: CommandRequest) -> CommandResult:
        if request.args[:3] == ("git", "-C", str(tmp_path.resolve(strict=False))):
            return runner(request)
        if request.args[:3] == ("gh", "api", "graphql"):
            return CommandResult(request=request, returncode=0, stdout=json.dumps(graphql_response))
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    history = issue_body_edit_history(37, project=tmp_path, runner=graphql_runner)

    assert history["body_edit_history"]["number"] == 37
    assert history["body_edit_history"]["userContentEdits"]["nodes"][0]["diff"] == "@@"


def test_write_operations_require_guard(tmp_path: Path) -> None:
    runner = FakeRunner(
        {
            git_args(tmp_path, "remote", "get-url", "origin"): result(
                git_args(tmp_path, "remote", "get-url", "origin"),
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            )
        }
    )

    with pytest.raises(GitHubGuardError):
        comment_issue(38, body="done", project=tmp_path, guard=None, runner=runner)  # type: ignore[arg-type]


def test_comment_issue_runs_guard_before_gh_write(tmp_path: Path) -> None:
    guard_calls: list[tuple[str, Mapping[str, Any]]] = []

    def runner(request: CommandRequest) -> CommandResult:
        if request.args == git_args(tmp_path, "remote", "get-url", "origin"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            )
        if request.args[:3] == ("gh", "issue", "comment"):
            body_file = Path(request.args[request.args.index("--body-file") + 1])
            assert body_file.read_text(encoding="utf-8") == "Implemented wrapper."
            assert guard_calls
            return CommandResult(request=request, returncode=0)
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    result_payload = comment_issue(
        38,
        body="Implemented wrapper.",
        project=tmp_path,
        guard=allow_guard(guard_calls),
        runner=runner,
    )

    assert result_payload["operation"] == "comment_issue"
    assert guard_calls[0][0] == "comment_issue"
    assert guard_calls[0][1]["issue"] == "38"


def test_edit_issue_body_verifies_after_write(tmp_path: Path) -> None:
    guard_calls: list[tuple[str, Mapping[str, Any]]] = []

    def runner(request: CommandRequest) -> CommandResult:
        if request.args == git_args(tmp_path, "remote", "get-url", "origin"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            )
        if request.args[:3] == ("gh", "issue", "edit"):
            body_file = Path(request.args[request.args.index("--body-file") + 1])
            assert body_file.read_text(encoding="utf-8") == "Updated body."
            assert guard_calls
            return CommandResult(request=request, returncode=0)
        if request.args == gh_issue_view_args(38, ("body",)):
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps({"body": "Updated body."}),
            )
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    result_payload = edit_issue_body(
        38,
        body="Updated body.",
        project=tmp_path,
        guard=allow_guard(guard_calls),
        runner=runner,
    )

    assert result_payload == {"operation": "edit_issue_body", "issue": "38", "verified": True}
    assert guard_calls[0][0] == "edit_issue_body"
    assert guard_calls[0][1]["issue"] == "38"


def test_close_issue_verifies_after_write(tmp_path: Path) -> None:
    guard_calls: list[tuple[str, Mapping[str, Any]]] = []

    def runner(request: CommandRequest) -> CommandResult:
        if request.args == git_args(tmp_path, "remote", "get-url", "origin"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            )
        if request.args == (
            "gh",
            "issue",
            "close",
            "38",
            "--repo",
            "studykit/studykit-plugins",
            "--reason",
            "completed",
        ):
            assert guard_calls
            return CommandResult(request=request, returncode=0)
        if request.args == gh_issue_view_args(38, ("state", "stateReason")):
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps({"state": "CLOSED", "stateReason": "COMPLETED"}),
            )
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    result_payload = close_issue(
        38,
        project=tmp_path,
        guard=allow_guard(guard_calls),
        runner=runner,
    )

    assert result_payload == {"operation": "close_issue", "issue": "38", "verified": True}
    assert guard_calls[0][0] == "close_issue"
    assert guard_calls[0][1]["issue"] == "38"


def test_reopen_issue_runs_guard_before_gh_write(tmp_path: Path) -> None:
    guard_calls: list[tuple[str, Mapping[str, Any]]] = []

    def runner(request: CommandRequest) -> CommandResult:
        if request.args == git_args(tmp_path, "remote", "get-url", "origin"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            )
        if request.args == (
            "gh",
            "issue",
            "reopen",
            "38",
            "--repo",
            "studykit/studykit-plugins",
        ):
            assert guard_calls
            return CommandResult(request=request, returncode=0)
        if request.args == gh_issue_view_args(38, ("state", "stateReason")):
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps({"state": "OPEN", "stateReason": None}),
            )
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    result_payload = reopen_issue(
        38,
        project=tmp_path,
        guard=allow_guard(guard_calls),
        runner=runner,
    )

    assert result_payload == {"operation": "reopen_issue", "issue": "38", "verified": True}
    assert guard_calls[0][0] == "reopen_issue"
    assert guard_calls[0][1]["issue"] == "38"


def test_close_issue_raises_when_verification_fails(tmp_path: Path) -> None:
    guard_calls: list[tuple[str, Mapping[str, Any]]] = []

    def runner(request: CommandRequest) -> CommandResult:
        if request.args == git_args(tmp_path, "remote", "get-url", "origin"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            )
        if request.args[:3] == ("gh", "issue", "close"):
            return CommandResult(request=request, returncode=0)
        if request.args == gh_issue_view_args(38, ("state", "stateReason")):
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps({"state": "OPEN", "stateReason": None}),
            )
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    with pytest.raises(GitHubVerificationError, match="state verification failed"):
        close_issue(
            38,
            project=tmp_path,
            guard=allow_guard(guard_calls),
            runner=runner,
        )

    assert guard_calls[0][0] == "close_issue"


def test_missing_gh_tool_is_reported(tmp_path: Path) -> None:
    request = CommandRequest(
        args=gh_args(
            tmp_path,
            "issue",
            "view",
            "38",
            "--repo",
            "studykit/studykit-plugins",
            "--json",
            ",".join(DEFAULT_ISSUE_FIELDS),
        )
    )
    runner = FakeRunner(
        {
            git_args(tmp_path, "remote", "get-url", "origin"): result(
                git_args(tmp_path, "remote", "get-url", "origin"),
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            ),
            request.args: MissingCommandError("command not found: gh", request=request),
        }
    )

    with pytest.raises(MissingCommandError):
        view_issue(38, project=tmp_path, runner=runner)


def test_failed_gh_command_is_reported(tmp_path: Path) -> None:
    runner = FakeRunner(
        {
            git_args(tmp_path, "remote", "get-url", "origin"): result(
                git_args(tmp_path, "remote", "get-url", "origin"),
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            ),
            gh_args(
                tmp_path,
                "issue",
                "view",
                "38",
                "--repo",
                "studykit/studykit-plugins",
                "--json",
                ",".join(DEFAULT_ISSUE_FIELDS),
            ): result(
                gh_args(
                    tmp_path,
                    "issue",
                    "view",
                    "38",
                    "--repo",
                    "studykit/studykit-plugins",
                    "--json",
                    ",".join(DEFAULT_ISSUE_FIELDS),
                ),
                stderr="not found",
                returncode=1,
            ),
        }
    )

    with pytest.raises(WorkflowCommandError):
        view_issue(38, project=tmp_path, runner=runner)


def test_invalid_json_is_parse_error(tmp_path: Path) -> None:
    runner = FakeRunner(
        {
            git_args(tmp_path, "remote", "get-url", "origin"): result(
                git_args(tmp_path, "remote", "get-url", "origin"),
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            ),
            gh_args(
                tmp_path,
                "issue",
                "view",
                "38",
                "--repo",
                "studykit/studykit-plugins",
                "--json",
                ",".join(DEFAULT_ISSUE_FIELDS),
            ): result(
                gh_args(
                    tmp_path,
                    "issue",
                    "view",
                    "38",
                    "--repo",
                    "studykit/studykit-plugins",
                    "--json",
                    ",".join(DEFAULT_ISSUE_FIELDS),
                ),
                stdout="not json",
            ),
        }
    )

    with pytest.raises(GitHubParseError):
        view_issue(38, project=tmp_path, runner=runner)
