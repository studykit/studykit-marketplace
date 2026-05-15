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
from workflow_config import load_workflow_config  # noqa: E402
from workflow_github import DEFAULT_ISSUE_FIELDS, GitHubRepository  # noqa: E402
from workflow_issue_cache import issue_numbers_from_references  # noqa: E402
from workflow_jira import JiraDataCenterIssueCache, jira_data_center_site_from_provider_config  # noqa: E402


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


def gh_api_args(path: str, *, paginate: bool = False) -> tuple[str, ...]:
    args = ("gh", "api", path)
    if paginate:
        return (*args, "--paginate")
    return args


def relationship_responses(
    issue: int | str,
    *,
    updated_at: str = "2026-05-14T00:00:00Z",
) -> dict[tuple[str, ...], CommandResult]:
    issue_path = f"repos/studykit/studykit-plugins/issues/{issue}"
    return {
        gh_api_args(issue_path): result(
            gh_api_args(issue_path),
            stdout=json.dumps({"number": int(issue), "updated_at": updated_at}),
        ),
        gh_api_args(f"{issue_path}/parent"): result(
            gh_api_args(f"{issue_path}/parent"),
            stdout=json.dumps({"number": 40, "title": "Parent", "state": "open"}),
        ),
        gh_api_args(f"{issue_path}/sub_issues", paginate=True): result(
            gh_api_args(f"{issue_path}/sub_issues", paginate=True),
            stdout=json.dumps([{"number": 43, "title": "Child", "state": "closed"}]),
        ),
        gh_api_args(f"{issue_path}/dependencies/blocked_by", paginate=True): result(
            gh_api_args(f"{issue_path}/dependencies/blocked_by", paginate=True),
            stdout=json.dumps([{"number": 41, "title": "Blocker", "state": "closed"}]),
        ),
        gh_api_args(f"{issue_path}/dependencies/blocking", paginate=True): result(
            gh_api_args(f"{issue_path}/dependencies/blocking", paginate=True),
            stdout="[]",
        ),
    }


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
            "status": {
                "name": "In Progress",
                "statusCategory": {"key": "indeterminate"},
            },
            "comment": {"comments": []},
            "parent": {
                "id": "9999",
                "key": "TM-1200",
                "fields": {"summary": "Parent task", "status": {"name": "Open"}},
            },
            "subtasks": [
                {
                    "id": "10005",
                    "key": "TM-1237",
                    "fields": {"summary": "Subtask", "status": {"name": "To Do"}},
                }
            ],
            "issuelinks": [
                {
                    "id": "30001",
                    "type": {"name": "Blocks", "outward": "blocks", "inward": "is blocked by"},
                    "outwardIssue": {
                        "id": "10002",
                        "key": "TM-1235",
                        "fields": {"summary": "Follow-up", "status": {"name": "Open"}},
                    },
                },
                {
                    "id": "30002",
                    "type": {"name": "Blocks", "outward": "blocks", "inward": "is blocked by"},
                    "inwardIssue": {
                        "id": "10003",
                        "key": "TM-1233",
                        "fields": {"summary": "Blocking predecessor", "status": {"name": "In Progress"}},
                    },
                },
            ],
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


def jira_issue_url(issue: str = "TM-1234") -> str:
    return f"https://jira.daumkakao.com/rest/api/2/issue/{issue}"


def jira_remote_links_url(issue: str = "TM-1234") -> str:
    return f"https://jira.daumkakao.com/rest/api/2/issue/{issue}/remotelink"


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


def test_issue_numbers_from_references_accepts_jira_keys() -> None:
    references = [
        "tm-1234",
        "Work on TM-1235 and tm-1234.",
        "#42",
        "https://github.com/studykit/studykit-plugins/issues/43",
    ]

    assert issue_numbers_from_references(references, issue_id_format="jira") == ["TM-1234", "TM-1235"]


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
    assert set(payload) == {"operation", "role", "kind", "repository", "cache_policy", "issues"}
    assert payload["operation"] == "cache_fetch"
    assert payload["issues"][0]["issue"] == "42"
    assert set(payload["issues"][0]) == {"issue", "issue_dir", "title", "state", "cache_hit"}
    assert payload["issues"][0]["issue_dir"] == ".workflow-cache/issues/42/"
    assert payload["issues"][0]["cache_hit"] is True
    assert runner.requests == []


def test_cache_fetch_plain_output_uses_project_relative_issue_path(tmp_path: Path) -> None:
    write_config(tmp_path)
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=repo())
    cache.write_issue_bundle(repo(), issue_payload(42, body="Cached body."))
    stdout = io.StringIO()

    code = cache_fetch_main(
        ["--project", str(tmp_path), "42"],
        stdout=stdout,
        runner=FakeRunner({}),
    )

    assert code == 0
    assert "- #42 → `.workflow-cache/issues/42/issue.md`" in stdout.getvalue()


def test_cache_fetch_plain_output_uses_shared_prefix_for_multiple_issues(tmp_path: Path) -> None:
    write_config(tmp_path)
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=repo())
    cache.write_issue_bundle(repo(), issue_payload(42, body="Cached body."))
    cache.write_issue_bundle(repo(), issue_payload(43, body="Cached body."))
    cache.relationships_file(repo(), 42).write_text(
        """
schema_version: 1
source_updated_at: 2026-05-14T00:00:00Z
fetched_at: 2026-05-14T00:00:00Z
parent:
  number: 40
children:
  - number: 44
  - number: 45
dependencies:
  blocked_by:
    - number: 41
  blocking:
    - number: 46
""".lstrip(),
        encoding="utf-8",
    )
    stdout = io.StringIO()

    code = cache_fetch_main(
        ["--project", str(tmp_path), "42", "43"],
        stdout=stdout,
        runner=FakeRunner({}),
    )

    assert code == 0
    assert stdout.getvalue() == "\n".join(
        [
            "Workflow issue cache: `.workflow-cache/issues/`",
            "- #42 → `42/issue.md` — parent #40; children #44,#45; blocked_by #41; blocking #46",
            "- #43 → `43/issue.md`",
            "",
        ]
    )


def test_cache_fetch_refresh_reads_remote_and_updates_cache(tmp_path: Path) -> None:
    write_config(tmp_path)
    remote = issue_payload(42, body="Fresh body.")
    runner = FakeRunner(
        {
            gh_issue_view_args(42): result(gh_issue_view_args(42), stdout=json.dumps(remote)),
            **relationship_responses(42),
        }
    )
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
    assert [request.args for request in runner.requests] == [
        gh_issue_view_args(42),
        gh_api_args("repos/studykit/studykit-plugins/issues/42"),
        gh_api_args("repos/studykit/studykit-plugins/issues/42/parent"),
        gh_api_args("repos/studykit/studykit-plugins/issues/42/sub_issues", paginate=True),
        gh_api_args("repos/studykit/studykit-plugins/issues/42/dependencies/blocked_by", paginate=True),
        gh_api_args("repos/studykit/studykit-plugins/issues/42/dependencies/blocking", paginate=True),
    ]
    cached = GitHubIssueCache.for_project(tmp_path, configured_repo=repo()).read_issue(repo(), 42)
    assert cached["body"] == "Fresh body."
    relationships = GitHubIssueCache.for_project(tmp_path, configured_repo=repo()).read_relationships(repo(), 42)
    assert relationships["parent"]["number"] == 40
    assert relationships["children"][0]["number"] == 43
    assert relationships["dependencies"]["blocked_by"][0]["number"] == 41
    assert payload["issues"][0]["relationships"] == "parent #40; children #43; blocked_by #41"


def test_cache_fetch_uses_jira_cache_hit_without_remote_read(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    site = jira_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(
        site,
        jira_issue_payload(body="Cached Jira body."),
        remote_links=remote_links_payload(),
        fetched_at="2026-05-15T01:00:00Z",
    )
    runner = FakeRunner({})
    stdout = io.StringIO()

    code = cache_fetch_main(
        ["--project", str(tmp_path), "--json", "tm-1234"],
        stdout=stdout,
        runner=runner,
    )

    payload = json.loads(stdout.getvalue())
    assert code == 0
    assert set(payload) == {"operation", "role", "kind", "cache_policy", "issues"}
    assert payload["kind"] == "jira"
    assert payload["issues"][0]["issue"] == "TM-1234"
    assert payload["issues"][0]["issue_dir"] == ".workflow-cache/jira/jira.daumkakao.com/issues/TM-1234/"
    assert payload["issues"][0]["issue_file"] == "snapshot.md"
    assert payload["issues"][0]["cache_hit"] is True
    assert payload["issues"][0]["relationships"] == (
        "parent TM-1200; children TM-1237; blocked_by TM-1233; "
        "blocking TM-1235; external_links 1"
    )
    assert runner.requests == []


def test_cache_fetch_plain_output_uses_jira_snapshot_path(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    site = jira_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(site, jira_issue_payload(), remote_links=[])
    stdout = io.StringIO()

    code = cache_fetch_main(
        ["--project", str(tmp_path), "tm-1234"],
        stdout=stdout,
        runner=FakeRunner({}),
    )

    assert code == 0
    assert "- TM-1234 → `.workflow-cache/jira/jira.daumkakao.com/issues/TM-1234/snapshot.md`" in stdout.getvalue()
    assert "#TM-1234" not in stdout.getvalue()


def test_cache_fetch_refresh_reads_remote_jira_and_updates_cache(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    runner = FakeRunner(
        {
            curl_args(jira_issue_url()): result(
                curl_args(jira_issue_url()),
                stdout=json.dumps(jira_issue_payload(body="Fresh Jira body.")),
            ),
            curl_args(jira_remote_links_url()): result(
                curl_args(jira_remote_links_url()),
                stdout=json.dumps(remote_links_payload()),
            ),
        }
    )
    stdout = io.StringIO()

    code = cache_fetch_main(
        ["--project", str(tmp_path), "--json", "--cache-policy", "refresh", "TM-1234"],
        stdout=stdout,
        runner=runner,
    )

    payload = json.loads(stdout.getvalue())
    assert code == 0
    assert payload["cache_policy"] == "refresh"
    assert payload["kind"] == "jira"
    assert "repository" not in payload
    assert payload["issues"][0]["issue"] == "TM-1234"
    assert payload["issues"][0]["cache_hit"] is False
    assert payload["issues"][0]["issue_file"] == "snapshot.md"
    assert [request.args for request in runner.requests] == [
        curl_args(jira_issue_url()),
        curl_args(jira_remote_links_url()),
    ]
    cached = JiraDataCenterIssueCache.for_project(tmp_path).read_issue(jira_site(tmp_path), "TM-1234")
    assert cached["body"] == "Fresh Jira body."
