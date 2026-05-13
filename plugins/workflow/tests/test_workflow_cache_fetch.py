"""Tests for the agent-facing workflow cache fetch entrypoint."""

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
from workflow_cache_fetch import main as cache_fetch_main  # noqa: E402
from workflow_command import CommandRequest, CommandResult  # noqa: E402
from workflow_github import DEFAULT_ISSUE_FIELDS, GitHubRepository  # noqa: E402
from workflow_issue_cache import issue_numbers_from_references  # noqa: E402


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


def issue_payload(number: int, *, body: str = "Issue body.") -> dict[str, object]:
    return {
        "number": number,
        "title": f"Issue {number}",
        "state": "OPEN",
        "stateReason": None,
        "body": body,
        "labels": [{"name": "task"}],
        "updatedAt": "2026-05-14T00:00:00Z",
        "comments": [],
    }


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


def test_issue_numbers_from_references_accepts_agent_shell_inputs() -> None:
    references = [
        "42",
        "#43",
        "studykit/studykit-plugins#44",
        "https://github.com/studykit/studykit-plugins/issues/45",
        "other/repo#46",
        "42",
    ]

    assert issue_numbers_from_references(references, repo=repo()) == ["42", "43", "44", "45"]


def test_cache_fetch_uses_cache_hit_without_remote_issue_view(tmp_path: Path) -> None:
    write_config(tmp_path)
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=repo())
    cache.write_issue_bundle(repo(), issue_payload(42, body="Cached body."))
    runner = FakeRunner({})
    stdout = io.StringIO()

    code = cache_fetch_main(
        ["--project", str(tmp_path), "--json", "42"],
        stdout=stdout,
        runner=runner,
    )

    payload = json.loads(stdout.getvalue())
    assert code == 0
    assert payload["operation"] == "cache_fetch"
    assert payload["cache_base"] == ".workflow-cache/issues/"
    assert payload["issues"][0]["issue"] == "42"
    assert payload["issues"][0]["relative_issue_dir"] == "42/"
    assert payload["issues"][0]["cache_hit"] is True
    assert runner.requests == []


def test_cache_fetch_refresh_reads_remote_and_updates_cache(tmp_path: Path) -> None:
    write_config(tmp_path)
    remote = issue_payload(42, body="Fresh body.")
    runner = FakeRunner({gh_issue_view_args(42): result(gh_issue_view_args(42), stdout=json.dumps(remote))})
    stdout = io.StringIO()

    code = cache_fetch_main(
        ["--project", str(tmp_path), "--json", "--cache-policy", "refresh", "42"],
        stdout=stdout,
        runner=runner,
    )

    payload = json.loads(stdout.getvalue())
    assert code == 0
    assert payload["cache_policy"] == "refresh"
    assert payload["issues"][0]["cache_hit"] is False
    assert [request.args for request in runner.requests] == [gh_issue_view_args(42)]
    cached = GitHubIssueCache.for_project(tmp_path, configured_repo=repo()).read_issue(repo(), 42)
    assert cached["body"] == "Fresh body."
