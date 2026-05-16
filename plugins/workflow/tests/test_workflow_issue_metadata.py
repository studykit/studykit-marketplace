"""Tests for semantic workflow issue metadata updates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_cache import GitHubIssueCache  # noqa: E402
from workflow_command import CommandRequest, CommandResult  # noqa: E402
from workflow_github import DEFAULT_ISSUE_FIELDS, GitHubRepository  # noqa: E402
from workflow_issue_metadata import (  # noqa: E402
    WorkflowIssueMetadataError,
    update_issue_metadata_payload,
)


class FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CommandResult]):
        self.responses = responses
        self.requests: list[CommandRequest] = []

    def __call__(self, request: CommandRequest) -> CommandResult:
        self.requests.append(request)
        response = self.responses.get(request.args)
        if response is None:
            return CommandResult(request=request, returncode=127, stderr=f"unexpected command: {request.args}")
        return response


def result(args: tuple[str, ...], stdout: str = "", stderr: str = "", returncode: int = 0) -> CommandResult:
    return CommandResult(request=CommandRequest(args=args), returncode=returncode, stdout=stdout, stderr=stderr)


def repo() -> GitHubRepository:
    return GitHubRepository(host="github.com", owner="studykit", name="studykit-plugins")


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


def gh_api_args(*args: str) -> tuple[str, ...]:
    return ("gh", "api", *args)


def write_github_config(project: Path) -> None:
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
    site: https://jira.example.test
    project: TM
    issue_type: Task
  knowledge:
    kind: github
issue_id_format: jira
""".lstrip(),
        encoding="utf-8",
    )


def issue_payload(*, title: str = "Cached title", labels: list[str] | None = None) -> dict[str, object]:
    return {
        "number": 39,
        "title": title,
        "state": "OPEN",
        "stateReason": None,
        "body": "Cached body.",
        "labels": [{"name": label} for label in (labels or ["task", "workflow"])],
        "comments": [],
        "updatedAt": "2026-05-13T12:00:00Z",
    }


def test_github_metadata_update_writes_title_and_type_through_provider(tmp_path: Path) -> None:
    write_github_config(tmp_path)
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=repo())
    cache.write_issue_bundle(repo(), issue_payload(), fetched_at="2026-05-13T12:34:56Z")

    freshness_args = gh_issue_view_args(39, ("number", "updatedAt"))
    current_labels_args = gh_issue_view_args(39, ("number", "labels"))
    edit_args = (
        "gh",
        "issue",
        "edit",
        "39",
        "--repo",
        "studykit/studykit-plugins",
        "--title",
        "New title",
        "--add-label",
        "bug",
        "--remove-label",
        "task",
    )
    verify_args = gh_issue_view_args(39, ("title", "labels"))
    refresh_args = gh_issue_view_args(39, DEFAULT_ISSUE_FIELDS)
    rest_issue_args = gh_api_args("repos/studykit/studykit-plugins/issues/39")
    parent_args = gh_api_args("repos/studykit/studykit-plugins/issues/39/parent")
    children_args = gh_api_args("repos/studykit/studykit-plugins/issues/39/sub_issues", "--paginate")
    blocked_by_args = gh_api_args("repos/studykit/studykit-plugins/issues/39/dependencies/blocked_by", "--paginate")
    blocking_args = gh_api_args("repos/studykit/studykit-plugins/issues/39/dependencies/blocking", "--paginate")
    refreshed = issue_payload(title="New title", labels=["bug", "workflow"])
    runner = FakeRunner(
        {
            freshness_args: result(freshness_args, stdout=json.dumps({"number": 39, "updatedAt": "2026-05-13T12:00:00Z"})),
            current_labels_args: result(
                current_labels_args,
                stdout=json.dumps({"number": 39, "labels": [{"name": "task"}, {"name": "workflow"}]}),
            ),
            edit_args: result(edit_args),
            verify_args: result(
                verify_args,
                stdout=json.dumps(
                    {
                        "title": "New title",
                        "labels": [{"name": "bug"}, {"name": "workflow"}],
                    }
                ),
            ),
            refresh_args: result(refresh_args, stdout=json.dumps(refreshed)),
            rest_issue_args: result(
                rest_issue_args,
                stdout=json.dumps({"id": 3900, "number": 39, "updated_at": "2026-05-13T12:00:00Z"}),
            ),
            parent_args: result(parent_args, stderr="not found", returncode=404),
            children_args: result(children_args, stdout="[]"),
            blocked_by_args: result(blocked_by_args, stdout="[]"),
            blocking_args: result(blocking_args, stdout="[]"),
        }
    )

    payload = update_issue_metadata_payload(
        project=tmp_path,
        issue="#39",
        artifact_type="task",
        title="New title",
        workflow_type="bug",
        runner=runner,
    )

    assert payload["operation"] == "update_issue_metadata"
    assert payload["kind"] == "github"
    assert payload["updated"] == ["title", "type"]
    assert [request.args for request in runner.requests] == [
        freshness_args,
        current_labels_args,
        edit_args,
        verify_args,
        refresh_args,
        rest_issue_args,
        parent_args,
        children_args,
        blocked_by_args,
        blocking_args,
    ]
    cached = cache.read_issue(repo(), 39, include_body=False, include_comments=False, include_relationships=False)
    assert cached["title"] == "New title"
    assert sorted(cached["labels"]) == ["bug", "workflow"]


def test_github_metadata_update_rejects_unmapped_status(tmp_path: Path) -> None:
    write_github_config(tmp_path)

    with pytest.raises(WorkflowIssueMetadataError, match="status writes require explicit metadata mapping"):
        update_issue_metadata_payload(
            project=tmp_path,
            issue="#39",
            artifact_type="task",
            status="done",
        )


def test_jira_metadata_update_rejects_type_without_safe_mapping(tmp_path: Path) -> None:
    write_jira_config(tmp_path)

    with pytest.raises(WorkflowIssueMetadataError, match="type writes require explicit safe type-change config"):
        update_issue_metadata_payload(
            project=tmp_path,
            issue="TM-1234",
            artifact_type="task",
            workflow_type="bug",
        )
