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
from workflow_config import load_workflow_config  # noqa: E402
from workflow_github import DEFAULT_ISSUE_FIELDS, GitHubRepository  # noqa: E402
from workflow_jira import JiraDataCenterIssueCache, jira_data_center_site_from_provider_config  # noqa: E402
from workflow_providers import ProviderRequest  # noqa: E402


class FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CommandResult | list[CommandResult]]):
        self.responses = responses
        self.requests: list[CommandRequest] = []

    def __call__(self, request: CommandRequest) -> CommandResult:
        self.requests.append(request)
        response = self.responses.get(request.args)
        if response is None:
            return CommandResult(request=request, returncode=127, stderr="unexpected command")
        if isinstance(response, list):
            if not response:
                return CommandResult(request=request, returncode=127, stderr="unexpected command")
            return response.pop(0)
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


def write_jira_config(project: Path) -> None:
    path = project / ".workflow" / "config.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
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
""".lstrip(),
        encoding="utf-8",
    )


def jira_site(project: Path):
    config = load_workflow_config(project)
    assert config is not None
    return jira_data_center_site_from_provider_config(config.issues)


def jira_issue_payload(*, body: str = "Data Center description.") -> dict[str, object]:
    return {
        "id": "10001",
        "key": "TM-1234",
        "fields": {
            "summary": "Support Jira Data Center",
            "description": body,
            "labels": ["workflow", "jira"],
            "created": "2026-05-15T09:00:00.000+0900",
            "updated": "2026-05-15T10:00:00.000+0900",
            "status": {"name": "In Progress", "statusCategory": {"key": "indeterminate"}},
            "comment": {"comments": []},
            "issuelinks": [],
        },
    }


def remote_links_payload() -> list[dict[str, object]]:
    return [
        {
            "id": 1,
            "relationship": "mentioned in",
            "object": {"title": "Design note", "url": "https://example.com/design"},
        }
    ]


def curl_args(url: str) -> tuple[str, ...]:
    return ("curl", "--silent", "--show-error", "--fail", "--request", "GET", "--config", "-", url)


def curl_write_args() -> tuple[str, ...]:
    return ("curl", "--silent", "--show-error", "--fail", "--config", "-")


def jira_issue_url(issue: str = "TM-1234") -> str:
    return f"https://jira.daumkakao.com/rest/api/2/issue/{issue}"


def jira_remote_links_url(issue: str = "TM-1234") -> str:
    return f"https://jira.daumkakao.com/rest/api/2/issue/{issue}/remotelink"


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


def test_cache_writeback_script_dispatches_jira_provider_update(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    site = jira_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(
        site,
        jira_issue_payload(body="Cached Jira write-back body."),
        remote_links=remote_links_payload(),
        fetched_at="2026-05-15T10:00:00.000+0900",
    )
    runner = FakeRunner(
        {
            curl_args(jira_issue_url()): [
                result(curl_args(jira_issue_url()), stdout=json.dumps(jira_issue_payload(body="Provider current."))),
                result(
                    curl_args(jira_issue_url()),
                    stdout=json.dumps(jira_issue_payload(body="Cached Jira write-back body.")),
                ),
            ],
            curl_write_args(): result(curl_write_args(), stdout=""),
            curl_args(jira_remote_links_url()): result(
                curl_args(jira_remote_links_url()),
                stdout=json.dumps(remote_links_payload()),
            ),
        }
    )
    guard_calls: list[ProviderRequest] = []

    def guard(request: ProviderRequest) -> None:
        guard_calls.append(request)

    stdout = io.StringIO()

    code = cache_writeback_main(
        ["--project", str(tmp_path), "--session", "s1", "--type", "task", "--json", "tm-1234"],
        stdout=stdout,
        runner=runner,
        guard=guard,
    )

    payload = json.loads(stdout.getvalue())
    assert code == 0
    assert payload["operation"] == "cache_writeback"
    assert payload["kind"] == "jira"
    assert "repository" not in payload
    assert payload["issues"][0]["operation"] == "update_issue_from_cache"
    assert payload["issues"][0]["issue"] == "TM-1234"
    assert payload["issues"][0]["verified"] is True
    assert guard_calls[0].kind == "jira"
    assert guard_calls[0].operation == "update"
    assert guard_calls[0].payload["from_cache"] is True
    write_request = runner.requests[1]
    assert write_request.args == curl_write_args()
    assert 'request = "PUT"' in str(write_request.input_text)
    assert 'url = "https://jira.daumkakao.com/rest/api/2/issue/TM-1234"' in str(write_request.input_text)
    assert '\\"description\\":\\"Cached Jira write-back body.\\"' in str(write_request.input_text)
    assert cache.read_issue(site, "TM-1234")["body"] == "Cached Jira write-back body."
