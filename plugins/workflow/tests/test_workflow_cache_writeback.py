"""Tests for the agent-facing workflow cache write-back entrypoint."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_cache import GitHubIssueCache  # noqa: E402
from workflow_cache_writeback import main as cache_writeback_main  # noqa: E402
from workflow_command import CommandRequest, CommandResult  # noqa: E402
from workflow_github import DEFAULT_ISSUE_FIELDS, GitHubRepository  # noqa: E402
from workflow_providers import ProviderRequest  # noqa: E402


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


def repo() -> GitHubRepository:
    return GitHubRepository(host="github.com", owner="studykit", name="studykit-plugins")


def issue_payload() -> dict[str, object]:
    return {
        "number": 42,
        "title": "Cached title",
        "state": "OPEN",
        "stateReason": None,
        "body": "Cached body.",
        "labels": [{"name": "task"}, {"name": "workflow"}],
        "updatedAt": "2026-05-14T00:00:00Z",
        "comments": [],
    }


def gh_issue_view_args(issue: int | str, fields: str) -> tuple[str, ...]:
    return (
        "gh",
        "issue",
        "view",
        str(issue),
        "--repo",
        "studykit/studykit-plugins",
        "--json",
        fields,
    )


def write_config(project: Path) -> None:
    path = project / ".workflow" / "config.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
version: 1
providers:
  issues:
    kind: github
    repo: studykit/studykit-plugins
  knowledge:
    kind: github
issue_id_format: github
""".lstrip(),
        encoding="utf-8",
    )


def test_cache_writeback_script_dispatches_guarded_provider_update(tmp_path: Path) -> None:
    write_config(tmp_path)
    GitHubIssueCache.for_project(tmp_path, configured_repo=repo()).write_issue_bundle(
        repo(),
        issue_payload(),
        fetched_at="2026-05-14T00:10:00Z",
    )
    runner = FakeRunner(
        {
            gh_issue_view_args(42, "number,updatedAt,labels,state,stateReason"): result(
                gh_issue_view_args(42, "number,updatedAt,labels,state,stateReason"),
                stdout=json.dumps(
                    {
                        "number": 42,
                        "updatedAt": "2026-05-14T00:00:00Z",
                        "labels": [{"name": "task"}],
                        "state": "OPEN",
                        "stateReason": None,
                    }
                ),
            ),
            gh_issue_view_args(42, "title,body,labels"): result(
                gh_issue_view_args(42, "title,body,labels"),
                stdout=json.dumps(
                    {
                        "title": "Cached title",
                        "body": "Cached body.",
                        "labels": [{"name": "task"}, {"name": "workflow"}],
                    }
                ),
            ),
            gh_issue_view_args(42, ",".join(DEFAULT_ISSUE_FIELDS)): result(
                gh_issue_view_args(42, ",".join(DEFAULT_ISSUE_FIELDS)),
                stdout=json.dumps(issue_payload()),
            ),
        }
    )
    guard_calls: list[ProviderRequest] = []

    def guard(request: ProviderRequest) -> None:
        guard_calls.append(request)

    def runner_with_edit(request: CommandRequest) -> CommandResult:
        if request.args[:3] == ("gh", "issue", "edit"):
            body_file = Path(request.args[request.args.index("--body-file") + 1])
            assert body_file.read_text(encoding="utf-8") == "Cached body."
            assert request.args[request.args.index("--title") + 1] == "Cached title"
            assert ("--add-label", "workflow") in zip(request.args, request.args[1:])
            return CommandResult(request=request, returncode=0)
        return runner(request)

    stdout = io.StringIO()

    code = cache_writeback_main(
        ["--project", str(tmp_path), "--session", "s1", "--type", "task", "--json", "42"],
        stdout=stdout,
        runner=runner_with_edit,
        guard=guard,
    )

    payload = json.loads(stdout.getvalue())
    assert code == 0
    assert payload["operation"] == "cache_writeback"
    assert payload["issues"][0]["operation"] == "update_issue_from_cache"
    assert payload["issues"][0]["issue"] == "42"
    assert payload["issues"][0]["verified"] is True
    assert guard_calls[0].operation == "update"
    assert guard_calls[0].payload["from_cache"] is True
