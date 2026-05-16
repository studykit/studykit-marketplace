"""Tests for provider-owned pending issue draft helpers."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_cache import GitHubIssueCache  # noqa: E402
from workflow_cache_issue_drafts import main as issue_drafts_main  # noqa: E402
from workflow_cache_issue_drafts import prepare_pending_issue_draft  # noqa: E402
from workflow_cache_issue_drafts import stage_pending_issue_relationships  # noqa: E402
from workflow_command import CommandRequest, CommandResult  # noqa: E402
from workflow_github import DEFAULT_ISSUE_FIELDS  # noqa: E402
from workflow_github import GitHubRepository  # noqa: E402
from workflow_jira import JiraDataCenterIssueCache, resolve_jira_data_center_site  # noqa: E402


class FakeRunner:
    def __init__(self) -> None:
        self.requests: list[CommandRequest] = []

    def __call__(self, request: CommandRequest) -> CommandResult:
        self.requests.append(request)
        if request.args[:3] == ("gh", "issue", "create"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout="https://github.com/studykit/studykit-plugins/issues/51\n",
            )
        if request.args == _gh_issue_view_args(51, "title,body,labels,state,stateReason"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps(
                    {
                        "title": "Draft issue",
                        "body": "Draft body.\n",
                        "labels": [{"name": "task"}, {"name": "workflow"}],
                        "state": "OPEN",
                        "stateReason": None,
                    }
                ),
            )
        if request.args == _gh_issue_view_args(51, ",".join(DEFAULT_ISSUE_FIELDS)):
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps(
                    {
                        "number": 51,
                        "title": "Draft issue",
                        "state": "OPEN",
                        "stateReason": None,
                        "body": "Draft body.\n",
                        "labels": [{"name": "task"}, {"name": "workflow"}],
                        "comments": [],
                        "url": "https://github.com/studykit/studykit-plugins/issues/51",
                        "createdAt": "2026-05-14T00:00:00Z",
                        "updatedAt": "2026-05-14T00:00:00Z",
                        "closedAt": None,
                    }
                ),
            )
        if request.args == _gh_api_args("repos/studykit/studykit-plugins/issues/51"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps({"id": 5100, "number": 51, "updated_at": "2026-05-14T00:00:00Z"}),
            )
        if request.args == _gh_api_args("repos/studykit/studykit-plugins/issues/51/parent"):
            return CommandResult(request=request, returncode=404, stderr="not found")
        if request.args in {
            _gh_api_args("repos/studykit/studykit-plugins/issues/51/sub_issues", "--paginate"),
            _gh_api_args("repos/studykit/studykit-plugins/issues/51/dependencies/blocked_by", "--paginate"),
            _gh_api_args("repos/studykit/studykit-plugins/issues/51/dependencies/blocking", "--paginate"),
        }:
            return CommandResult(request=request, returncode=0, stdout="[]")
        return CommandResult(request=request, returncode=127, stderr="unexpected command")


def _write_config(project: Path) -> None:
    config_path = project / ".workflow" / "config.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        """
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
  mode: none
commit_refs:
  enabled: true
  style: provider-native
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
""".lstrip(),
        encoding="utf-8",
    )


def _repo() -> GitHubRepository:
    return GitHubRepository(host="github.com", owner="studykit", name="studykit-plugins")


def _gh_issue_view_args(issue: int | str, fields: str) -> tuple[str, ...]:
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


def _gh_api_args(*args: str) -> tuple[str, ...]:
    return ("gh", "api", *args)


def test_prepare_pending_issue_draft_writes_bodyless_provider_frontmatter(tmp_path: Path) -> None:
    _write_config(tmp_path)

    payload = prepare_pending_issue_draft(
        project=tmp_path,
        local_id="draft-1",
        artifact_type="task",
        title="Draft issue",
        labels=("workflow",),
    )

    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=_repo())
    draft = cache.read_pending_issue_draft(_repo(), "draft-1")
    issue_file = cache.pending_issue_file(_repo(), "draft-1")

    assert payload["operation"] == "prepare_pending_issue"
    assert payload["artifact_type"] == "task"
    assert payload["issue_file"] == str(issue_file)
    assert draft.title == "Draft issue"
    assert draft.labels == ("task", "workflow")
    assert draft.state == "open"
    assert draft.body == ""
    assert issue_file.read_text(encoding="utf-8").endswith("---\n\n")


def test_prepare_jira_review_pending_issue_draft_prefixes_summary(tmp_path: Path) -> None:
    _write_jira_config(tmp_path)

    payload = prepare_pending_issue_draft(
        project=tmp_path,
        local_id="review-1",
        artifact_type="review",
        title="Clarify target",
    )

    site = resolve_jira_data_center_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    draft = cache.read_pending_issue_draft(site, "review-1")

    assert payload["artifact_type"] == "review"
    assert payload["title"] == "[Review] Clarify target"
    assert draft.title == "[Review] Clarify target"


def test_stage_pending_issue_relationships_writes_operator_owned_file(tmp_path: Path) -> None:
    _write_config(tmp_path)
    prepare_pending_issue_draft(
        project=tmp_path,
        local_id="draft-1",
        artifact_type="task",
        title="Draft issue",
        labels=("task",),
    )

    payload = stage_pending_issue_relationships(
        project=tmp_path,
        local_id="draft-1",
        parent="#28",
        blocked_by=("#33",),
        blocking=("#45",),
    )

    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=_repo())
    operations = cache.read_pending_draft_relationships(_repo(), "draft-1")
    issue_file = cache.pending_issue_file(_repo(), "draft-1")

    assert payload["operation"] == "stage_pending_issue_relationships"
    assert payload["pending_location"] == str(issue_file)
    assert "relationships_file" not in payload
    assert [(item.relationship, item.target_ref) for item in operations] == [
        ("parent", "#28"),
        ("blocked_by", "#33"),
        ("blocking", "#45"),
    ]
    assert all(item.path == issue_file for item in operations)


def test_create_command_creates_provider_issue(tmp_path: Path) -> None:
    _write_config(tmp_path)
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=_repo())
    draft_path = cache.pending_issue_file(_repo(), "draft-1")
    draft_path.parent.mkdir(parents=True)
    draft_path.write_text(
        """---
title: "Draft issue"
labels:
  - task
  - workflow
state: open
---

Draft body.
""",
        encoding="utf-8",
    )
    runner = FakeRunner()
    stdout = io.StringIO()

    code = issue_drafts_main(
        [
            "--project",
            str(tmp_path),
            "create",
            "--type",
            "task",
            "--confirm-provider-create",
            "--json",
            "draft-1",
        ],
        stdout=stdout,
        runner=runner,
    )

    payload = json.loads(stdout.getvalue())
    assert code == 0
    assert payload["operation"] == "create_issue"
    assert payload["issue"] == "51"
    assert payload["pending_finalized"] is True
    assert cache.read_issue(_repo(), 51)["body"] == "Draft body.\n"
    assert not draft_path.exists()
    assert runner.requests[0].args[:3] == ("gh", "issue", "create")


def test_create_command_requires_provider_create_confirmation(tmp_path: Path) -> None:
    _write_config(tmp_path)
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=_repo())
    draft_path = cache.pending_issue_file(_repo(), "draft-1")
    draft_path.parent.mkdir(parents=True)
    draft_path.write_text(
        """---
title: "Draft issue"
labels:
  - task
state: open
---

Draft body.
""",
        encoding="utf-8",
    )
    runner = FakeRunner()
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = issue_drafts_main(
        ["--project", str(tmp_path), "create", "--type", "task", "--json", "draft-1"],
        stdout=stdout,
        stderr=stderr,
        runner=runner,
    )

    assert code == 2
    assert stdout.getvalue() == ""
    assert "--confirm-provider-create" in stderr.getvalue()
    assert draft_path.exists()
    assert runner.requests == []
