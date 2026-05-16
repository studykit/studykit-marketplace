"""Tests for Jira Data Center workflow provider reads and cache."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_command import CommandRequest, CommandResult  # noqa: E402
from workflow_cache_relationships import stage_relationships_payload  # noqa: E402
from workflow_jira import (  # noqa: E402
    JiraDataCenterIssueCache,
    jira_data_center_site_from_provider_config,
)
from workflow_providers import (  # noqa: E402
    CACHE_POLICY_BYPASS,
    CACHE_POLICY_REFRESH,
    ProviderContext,
    ProviderDispatcher,
    ProviderFreshnessError,
    ProviderOperationError,
    ProviderRequest,
    default_provider_registry,
)
from workflow_config import load_workflow_config  # noqa: E402


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


def curl_args(url: str) -> tuple[str, ...]:
    return ("curl", "--silent", "--show-error", "--fail", "--request", "GET", "--config", "-", url)


def curl_write_args() -> tuple[str, ...]:
    return ("curl", "--silent", "--show-error", "--fail", "--config", "-")


def write_jira_config(
    project: Path,
    *,
    deployment: str = "data-center",
    relationship_mappings: str = "",
) -> None:
    path = project / ".workflow" / "config.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            f"""
version: 1
providers:
  issues:
    kind: jira
    site: https://jira.daumkakao.com
    deployment: {deployment}
    api_version: 2
    project: TM
    issue_type: Task
"""
            + relationship_mappings
            + """
  knowledge:
    kind: github
issue_id_format: jira
"""
        ).lstrip(),
        encoding="utf-8",
    )


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
            "comment": {
                "comments": [
                    {
                        "id": "20001",
                        "author": {"displayName": "Hong Gil-dong", "name": "hong"},
                        "body": "Please keep Data Center first.",
                        "created": "2026-05-15T09:30:00.000+0900",
                        "updated": "2026-05-15T09:30:00.000+0900",
                    }
                ]
            },
            "issuelinks": [
                {
                    "id": "30001",
                    "type": {"name": "Blocks", "outward": "blocks", "inward": "is blocked by"},
                    "outwardIssue": {
                        "id": "10002",
                        "key": "TM-1235",
                        "fields": {
                            "summary": "Follow-up",
                            "status": {"name": "Open"},
                        },
                    },
                },
                {
                    "id": "30002",
                    "type": {"name": "Blocks", "outward": "blocks", "inward": "is blocked by"},
                    "inwardIssue": {
                        "id": "10003",
                        "key": "TM-1233",
                        "fields": {
                            "summary": "Blocking predecessor",
                            "status": {"name": "In Progress"},
                        },
                    },
                },
                {
                    "id": "30003",
                    "type": {"name": "Relates", "outward": "relates to", "inward": "relates to"},
                    "outwardIssue": {
                        "id": "10004",
                        "key": "TM-1236",
                        "fields": {
                            "summary": "Related issue",
                            "status": {"name": "Open"},
                        },
                    },
                }
            ],
            "parent": {
                "id": "9999",
                "key": "TM-1200",
                "fields": {
                    "summary": "Parent task",
                    "status": {"name": "Open"},
                },
            },
            "subtasks": [
                {
                    "id": "10005",
                    "key": "TM-1237",
                    "fields": {
                        "summary": "Subtask",
                        "status": {"name": "To Do"},
                    },
                }
            ],
        },
    }


def remote_links_payload() -> list[dict[str, object]]:
    return [
        {
            "id": 1,
            "relationship": "mentioned in",
            "object": {
                "title": "Design note",
                "url": "https://example.com/design",
            },
        }
    ]


def issue_link_relationship_mappings() -> str:
    return """
    relationship_mappings:
      blocked_by:
        surface: issue_link
        link_type: Blocks
        direction: inward
      blocking:
        surface: issue_link
        link_type: Blocks
        direction: outward
      related:
        surface: issue_link
        link_type: Relates
        direction: outward
"""


def remote_link_relationship_mappings() -> str:
    return """
    relationship_mappings:
      related:
        surface: remote_link
        relationship_label: relates to
        application_type: studykit.workflow
        application_name: Workflow
"""


def issue_url(issue: str = "TM-1234") -> str:
    return f"https://jira.daumkakao.com/rest/api/2/issue/{issue}"


def remote_links_url(issue: str = "TM-1234") -> str:
    return f"https://jira.daumkakao.com/rest/api/2/issue/{issue}/remotelink"


def issue_link_url() -> str:
    return "https://jira.daumkakao.com/rest/api/2/issueLink"


def dispatch_get(
    project: Path,
    runner: FakeRunner,
    *,
    cache_policy: str = "default",
    include_remote_links: bool = True,
):
    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))
    return dispatcher.dispatch(
        ProviderRequest(
            role="issue",
            kind="jira",
            operation="get",
            context=ProviderContext(project=project, artifact_type="task", cache_policy=cache_policy),
            payload={"issue": "tm-1234", "include_remote_links": include_remote_links},
        )
    )


def dispatch_write(
    project: Path,
    runner: FakeRunner,
    operation: str,
    *,
    artifact_type: str = "task",
    **payload: object,
):
    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))
    return dispatcher.dispatch(
        ProviderRequest(
            role="issue",
            kind="jira",
            operation=operation,
            context=ProviderContext(project=project, artifact_type=artifact_type),
            payload=payload,
        )
    )


def jira_site(project: Path):
    config = load_workflow_config(project)
    assert config is not None
    return jira_data_center_site_from_provider_config(config.issues)


def test_data_center_provider_fetches_issue_remote_links_and_writes_llm_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_jira_config(tmp_path)
    monkeypatch.delenv("JIRA_PERSONAL_TOKEN", raising=False)
    monkeypatch.delenv("JIRA_PAT", raising=False)
    monkeypatch.delenv("JIRA_USERNAME", raising=False)
    monkeypatch.delenv("JIRA_PASSWORD", raising=False)
    runner = FakeRunner(
        {
            curl_args(issue_url()): result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
            curl_args(remote_links_url()): result(curl_args(remote_links_url()), stdout=json.dumps(remote_links_payload())),
        }
    )

    response = dispatch_get(tmp_path, runner)

    assert response.payload["key"] == "TM-1234"
    assert response.payload["title"] == "Support Jira Data Center"
    assert response.payload["body"] == "Data Center description."
    assert response.payload["jira"]["deployment"] == "data_center"
    assert response.payload["relationships"]["remote_links"][0]["url"] == "https://example.com/design"
    workflow = response.payload["relationships"]["workflow"]
    assert workflow["parent"]["key"] == "TM-1200"
    assert workflow["children"][0]["key"] == "TM-1237"
    assert workflow["dependencies"]["blocking"][0]["key"] == "TM-1235"
    assert workflow["dependencies"]["blocked_by"][0]["key"] == "TM-1233"
    assert workflow["related"][0]["key"] == "TM-1236"
    assert workflow["external_links"][0]["url"] == "https://example.com/design"
    assert [request.args for request in runner.requests] == [curl_args(issue_url()), curl_args(remote_links_url())]
    assert all(request.input_text == 'header = "Accept: application/json"\n' for request in runner.requests)

    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    site = jira_site(tmp_path)
    issue_dir = cache.issue_dir(site, "TM-1234")
    assert issue_dir == tmp_path / ".workflow-cache" / "jira" / "jira.daumkakao.com" / "issues" / "TM-1234"
    assert (issue_dir / "issue.json").is_file()
    assert (issue_dir / "remote-links.json").is_file()
    snapshot = (issue_dir / "snapshot.md").read_text(encoding="utf-8")
    assert "# TM-1234: Support Jira Data Center" in snapshot
    assert "Data Center description." in snapshot
    assert "Please keep Data Center first." in snapshot
    assert "https://example.com/design" in snapshot
    assert "Parent: TM-1200 (Parent task)" in snapshot
    assert "Blocked by: TM-1233 (Blocking predecessor)" in snapshot
    assert "Blocking: TM-1235 (Follow-up)" in snapshot


def test_default_cache_policy_uses_data_center_cache_hit_without_curl(tmp_path: Path) -> None:
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

    response = dispatch_get(tmp_path, runner)

    assert response.payload["body"] == "Cached Jira body."
    assert response.payload["cache"]["hit"] is True
    assert response.payload["cache"]["snapshot"].endswith("/snapshot.md")
    assert runner.requests == []


def test_refresh_policy_overwrites_data_center_cache(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    site = jira_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(site, jira_issue_payload(body="Stale body."), fetched_at="2026-05-15T01:00:00Z")
    runner = FakeRunner(
        {
            curl_args(issue_url()): result(
                curl_args(issue_url()),
                stdout=json.dumps(jira_issue_payload(body="Fresh body.")),
            ),
            curl_args(remote_links_url()): result(curl_args(remote_links_url()), stdout=json.dumps(remote_links_payload())),
        }
    )

    response = dispatch_get(tmp_path, runner, cache_policy=CACHE_POLICY_REFRESH)

    assert response.payload["body"] == "Fresh body."
    cached = cache.read_issue(site, "TM-1234")
    assert cached["body"] == "Fresh body."


def test_bypass_policy_reads_data_center_without_writing_cache(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    runner = FakeRunner(
        {
            curl_args(issue_url()): result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
            curl_args(remote_links_url()): result(curl_args(remote_links_url()), stdout=json.dumps(remote_links_payload())),
        }
    )

    response = dispatch_get(tmp_path, runner, cache_policy=CACHE_POLICY_BYPASS)

    assert response.payload["body"] == "Data Center description."
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    assert not cache.issue_json_file(jira_site(tmp_path), "TM-1234").exists()


def test_cloud_deployment_is_rejected_for_now(tmp_path: Path) -> None:
    write_jira_config(tmp_path, deployment="cloud")
    runner = FakeRunner({})

    with pytest.raises(ProviderOperationError, match="Jira Cloud is out of scope"):
        dispatch_get(tmp_path, runner)


def test_data_center_create_uses_pending_draft_and_refreshes_cache(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    site = jira_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    draft = cache.pending_issue_file(site, "local-1")
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(
        """---
title: Pending Jira issue
labels:
- workflow
---

Pending body.
""",
        encoding="utf-8",
    )
    relationships_pending = cache.pending_issue_relationships_pending_file(site, "local-1")
    relationships_pending.write_text("related:\n  - TM-1235\n", encoding="utf-8")
    draft_relationships = cache.read_pending_draft_relationships(site, "local-1")
    assert [(item.relationship, item.target_ref) for item in draft_relationships] == [("related", "TM-1235")]
    runner = FakeRunner(
        {
            curl_write_args(): result(curl_write_args(), stdout=json.dumps({"id": "10001", "key": "TM-1234"})),
            curl_args(issue_url()): result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
            curl_args(remote_links_url()): result(curl_args(remote_links_url()), stdout=json.dumps(remote_links_payload())),
        }
    )

    response = dispatch_write(tmp_path, runner, "create", pending_local_id="local-1")

    assert response.payload["operation"] == "create_issue"
    assert response.payload["issue"] == "TM-1234"
    assert response.payload["pending_finalized"] is True
    write_request = runner.requests[0]
    assert write_request.args == curl_write_args()
    assert 'request = "POST"' in str(write_request.input_text)
    assert 'url = "https://jira.daumkakao.com/rest/api/2/issue"' in str(write_request.input_text)
    assert '\\"summary\\":\\"Pending Jira issue\\"' in str(write_request.input_text)
    assert '\\"issuetype\\":{\\"name\\":\\"Task\\"}' in str(write_request.input_text)
    assert cache.issue_json_file(site, "TM-1234").is_file()
    assert not draft.exists()
    assert cache.created_issue_archive_dir(site, "local-1", "TM-1234").joinpath("issue.md").is_file()
    assert not relationships_pending.exists()
    assert cache.relationships_pending_file(site, "TM-1234").is_file()


def test_data_center_review_create_uses_task_type_and_review_summary_prefix(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    runner = FakeRunner(
        {
            curl_write_args(): result(curl_write_args(), stdout=json.dumps({"id": "10001", "key": "TM-1234"})),
            curl_args(issue_url()): result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
            curl_args(remote_links_url()): result(curl_args(remote_links_url()), stdout=json.dumps(remote_links_payload())),
        }
    )

    response = dispatch_write(
        tmp_path,
        runner,
        "create",
        artifact_type="review",
        title="Clarify target",
        body="## Description\n\nClarify the target.",
        issue_type="Bug",
    )

    assert response.payload["operation"] == "create_issue"
    write_request = runner.requests[0]
    assert write_request.args == curl_write_args()
    payload_text = str(write_request.input_text)
    assert '\\"summary\\":\\"[Review] Clarify target\\"' in payload_text
    assert '\\"issuetype\\":{\\"name\\":\\"Task\\"}' in payload_text


def test_data_center_spike_create_uses_task_type_and_spike_summary_prefix(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    runner = FakeRunner(
        {
            curl_write_args(): result(curl_write_args(), stdout=json.dumps({"id": "10001", "key": "TM-1234"})),
            curl_args(issue_url()): result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
            curl_args(remote_links_url()): result(curl_args(remote_links_url()), stdout=json.dumps(remote_links_payload())),
        }
    )

    response = dispatch_write(
        tmp_path,
        runner,
        "create",
        artifact_type="spike",
        title="Probe Jira issue type",
        body="## Description\n\nProbe the Jira issue type.",
        issue_type="Bug",
    )

    assert response.payload["operation"] == "create_issue"
    write_request = runner.requests[0]
    assert write_request.args == curl_write_args()
    payload_text = str(write_request.input_text)
    assert '\\"summary\\":\\"[Spike] Probe Jira issue type\\"' in payload_text
    assert '\\"issuetype\\":{\\"name\\":\\"Task\\"}' in payload_text


def test_data_center_research_create_uses_task_type_and_research_summary_prefix(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    runner = FakeRunner(
        {
            curl_write_args(): result(curl_write_args(), stdout=json.dumps({"id": "10001", "key": "TM-1234"})),
            curl_args(issue_url()): result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
            curl_args(remote_links_url()): result(curl_args(remote_links_url()), stdout=json.dumps(remote_links_payload())),
        }
    )

    response = dispatch_write(
        tmp_path,
        runner,
        "create",
        artifact_type="research",
        title="Compare issue types",
        body="## Description\n\nCompare the Jira issue types.",
    )

    assert response.payload["operation"] == "create_issue"
    write_request = runner.requests[0]
    assert write_request.args == curl_write_args()
    payload_text = str(write_request.input_text)
    assert '\\"summary\\":\\"[Research] Compare issue types\\"' in payload_text
    assert '\\"issuetype\\":{\\"name\\":\\"Task\\"}' in payload_text


def test_data_center_usecase_create_uses_story_type(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    runner = FakeRunner(
        {
            curl_write_args(): result(curl_write_args(), stdout=json.dumps({"id": "10001", "key": "TM-1234"})),
            curl_args(issue_url()): result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
            curl_args(remote_links_url()): result(curl_args(remote_links_url()), stdout=json.dumps(remote_links_payload())),
        }
    )

    response = dispatch_write(
        tmp_path,
        runner,
        "create",
        artifact_type="usecase",
        title="Shape checkout flow",
        body="## Description\n\nShape the checkout flow.",
    )

    assert response.payload["operation"] == "create_issue"
    write_request = runner.requests[0]
    assert write_request.args == curl_write_args()
    payload_text = str(write_request.input_text)
    assert '\\"summary\\":\\"Shape checkout flow\\"' in payload_text
    assert '\\"issuetype\\":{\\"name\\":\\"Story\\"}' in payload_text


@pytest.mark.parametrize(
    ("artifact_type", "expected_issue_type"),
    [
        ("task", "Task"),
        ("bug", "Bug"),
        ("epic", "Epic"),
        ("research", "Task"),
        ("usecase", "Story"),
    ],
)
def test_data_center_create_uses_artifact_issue_type(
    tmp_path: Path,
    artifact_type: str,
    expected_issue_type: str,
) -> None:
    write_jira_config(tmp_path)
    runner = FakeRunner(
        {
            curl_write_args(): result(curl_write_args(), stdout=json.dumps({"id": "10001", "key": "TM-1234"})),
            curl_args(issue_url()): result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
            curl_args(remote_links_url()): result(curl_args(remote_links_url()), stdout=json.dumps(remote_links_payload())),
        }
    )

    response = dispatch_write(
        tmp_path,
        runner,
        "create",
        artifact_type=artifact_type,
        title=f"Create {artifact_type}",
        body="## Description\n\nCreate the issue.",
        issue_type="Custom",
    )

    assert response.payload["operation"] == "create_issue"
    payload_text = str(runner.requests[0].input_text)
    assert f'\\"issuetype\\":{{\\"name\\":\\"{expected_issue_type}\\"}}' in payload_text


def test_data_center_update_from_cache_checks_freshness_and_refreshes(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    site = jira_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(
        site,
        jira_issue_payload(body="Cached write-back body."),
        remote_links=remote_links_payload(),
        fetched_at="2026-05-15T10:00:00.000+0900",
    )
    runner = FakeRunner(
        {
            curl_args(issue_url()): [
                result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload(body="Provider current."))),
                result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload(body="Cached write-back body."))),
            ],
            curl_write_args(): result(curl_write_args(), stdout=""),
            curl_args(remote_links_url()): result(curl_args(remote_links_url()), stdout=json.dumps(remote_links_payload())),
        }
    )

    response = dispatch_write(tmp_path, runner, "update", issue="TM-1234", from_cache=True)

    assert response.payload["operation"] == "update_issue_from_cache"
    write_request = runner.requests[1]
    assert write_request.args == curl_write_args()
    assert 'request = "PUT"' in str(write_request.input_text)
    assert 'url = "https://jira.daumkakao.com/rest/api/2/issue/TM-1234"' in str(write_request.input_text)
    assert '\\"description\\":\\"Cached write-back body.\\"' in str(write_request.input_text)
    assert cache.read_issue(site, "TM-1234")["body"] == "Cached write-back body."


def test_data_center_pending_comments_are_appended_and_removed(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    site = jira_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(
        site,
        jira_issue_payload(),
        remote_links=remote_links_payload(),
        fetched_at="2026-05-15T10:00:00.000+0900",
    )
    pending = cache.comments_pending_dir(site, "TM-1234") / "001.md"
    pending.parent.mkdir(parents=True, exist_ok=True)
    pending.write_text("---\n---\n\nPending comment body.\n", encoding="utf-8")
    runner = FakeRunner(
        {
            curl_args(issue_url()): [
                result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
                result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
            ],
            curl_write_args(): result(curl_write_args(), stdout=json.dumps({"id": "30001", "body": "Pending comment body."})),
            curl_args(remote_links_url()): result(curl_args(remote_links_url()), stdout=json.dumps(remote_links_payload())),
        }
    )

    response = dispatch_write(tmp_path, runner, "add_comment", issue="TM-1234", pending_comments=True)

    assert response.payload["operation"] == "append_pending_comments"
    assert response.payload["appended"] == 1
    assert response.payload["pending_files"] == ["001.md"]
    assert not pending.exists()
    write_request = runner.requests[1]
    assert 'request = "POST"' in str(write_request.input_text)
    assert 'url = "https://jira.daumkakao.com/rest/api/2/issue/TM-1234/comment"' in str(write_request.input_text)
    assert '\\"body\\":\\"Pending comment body.\\\\n\\"' in str(write_request.input_text)


def test_cache_relationships_stages_existing_jira_issue_relationship_intent(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    site = jira_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(
        site,
        jira_issue_payload(),
        remote_links=remote_links_payload(),
        fetched_at="2026-05-15T10:00:00.000+0900",
    )

    payload = stage_relationships_payload(
        project=tmp_path,
        issues=["TM-1234"],
        blocked_by=("TM-1233",),
        related=("https://github.com/studykit/studykit-plugins/issues/57",),
    )

    pending_path = cache.relationships_pending_file(site, "TM-1234")
    operations = cache.read_pending_issue_relationships(site, "TM-1234")
    assert payload["operation"] == "cache_stage_pending_relationships"
    assert payload["kind"] == "jira"
    assert payload["issue"] == "TM-1234"
    assert payload["relationships_file"] == str(pending_path)
    assert [(item.relationship, item.target_ref) for item in operations] == [
        ("blocked_by", "TM-1233"),
        ("related", "https://github.com/studykit/studykit-plugins/issues/57"),
    ]


def test_data_center_issue_link_relationships_are_applied_and_removed_from_pending_cache(tmp_path: Path) -> None:
    write_jira_config(tmp_path, relationship_mappings=issue_link_relationship_mappings())
    site = jira_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(
        site,
        jira_issue_payload(),
        remote_links=remote_links_payload(),
        fetched_at="2026-05-15T10:00:00.000+0900",
    )
    pending = cache.relationships_pending_file(site, "TM-1234")
    pending.write_text(
        """
schema_version: 1
dependencies:
  blocked_by:
    - TM-1233
  blocking:
    - TM-1235
related:
  - TM-1236
""".lstrip(),
        encoding="utf-8",
    )
    runner = FakeRunner(
        {
            curl_args(issue_url()): [
                result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
                result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
            ],
            curl_write_args(): [
                result(curl_write_args(), stdout=""),
                result(curl_write_args(), stdout=""),
                result(curl_write_args(), stdout=""),
            ],
            curl_args(remote_links_url()): result(curl_args(remote_links_url()), stdout=json.dumps(remote_links_payload())),
        }
    )

    response = dispatch_write(tmp_path, runner, "apply_relationships", issue="TM-1234", pending_relationships=True)

    assert response.payload["operation"] == "apply_relationships"
    assert response.payload["applied"] == 3
    assert response.payload["cache_refreshed"] is True
    assert not pending.exists()
    write_requests = [request for request in runner.requests if request.args == curl_write_args()]
    assert len(write_requests) == 3
    blocked_by_request = str(write_requests[0].input_text)
    assert 'request = "POST"' in blocked_by_request
    assert f'url = "{issue_link_url()}"' in blocked_by_request
    assert '\\"type\\":{\\"name\\":\\"Blocks\\"}' in blocked_by_request
    assert '\\"inwardIssue\\":{\\"key\\":\\"TM-1234\\"}' in blocked_by_request
    assert '\\"outwardIssue\\":{\\"key\\":\\"TM-1233\\"}' in blocked_by_request
    blocking_request = str(write_requests[1].input_text)
    assert '\\"inwardIssue\\":{\\"key\\":\\"TM-1235\\"}' in blocking_request
    assert '\\"outwardIssue\\":{\\"key\\":\\"TM-1234\\"}' in blocking_request
    related_request = str(write_requests[2].input_text)
    assert '\\"type\\":{\\"name\\":\\"Relates\\"}' in related_request
    assert '\\"inwardIssue\\":{\\"key\\":\\"TM-1236\\"}' in related_request


def test_data_center_remote_link_relationships_are_applied_with_stable_global_id(tmp_path: Path) -> None:
    write_jira_config(tmp_path, relationship_mappings=remote_link_relationship_mappings())
    site = jira_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(
        site,
        jira_issue_payload(),
        remote_links=remote_links_payload(),
        fetched_at="2026-05-15T10:00:00.000+0900",
    )
    pending = cache.relationships_pending_file(site, "TM-1234")
    pending.write_text(
        """
schema_version: 1
related:
  - https://github.com/studykit/studykit-plugins/issues/57
""".lstrip(),
        encoding="utf-8",
    )
    runner = FakeRunner(
        {
            curl_args(issue_url()): [
                result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
                result(curl_args(issue_url()), stdout=json.dumps(jira_issue_payload())),
            ],
            curl_write_args(): result(curl_write_args(), stdout=json.dumps({"id": 100})),
            curl_args(remote_links_url()): result(curl_args(remote_links_url()), stdout=json.dumps(remote_links_payload())),
        }
    )

    response = dispatch_write(tmp_path, runner, "apply_relationships", issue="TM-1234", pending_relationships=True)

    assert response.payload["applied"] == 1
    assert not pending.exists()
    write_request = next(request for request in runner.requests if request.args == curl_write_args())
    body = str(write_request.input_text)
    assert 'request = "POST"' in body
    assert 'url = "https://jira.daumkakao.com/rest/api/2/issue/TM-1234/remotelink"' in body
    assert '\\"globalId\\":\\"system=studykit-workflow&id=' in body
    assert '\\"relationship\\":\\"relates to\\"' in body
    assert '\\"url\\":\\"https://github.com/studykit/studykit-plugins/issues/57\\"' in body
    assert '\\"title\\":\\"57\\"' in body


def test_data_center_missing_relationship_mapping_fails_before_mutation(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    site = jira_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(
        site,
        jira_issue_payload(),
        remote_links=remote_links_payload(),
        fetched_at="2026-05-15T10:00:00.000+0900",
    )
    cache.relationships_pending_file(site, "TM-1234").write_text("blocking:\n  - TM-1235\n", encoding="utf-8")
    runner = FakeRunner({})

    with pytest.raises(ProviderOperationError, match="Jira relationship 'blocking' is not configured"):
        dispatch_write(tmp_path, runner, "apply_relationships", issue="TM-1234", pending_relationships=True)

    assert runner.requests == []


def test_data_center_bad_relationship_direction_fails_before_mutation(tmp_path: Path) -> None:
    write_jira_config(
        tmp_path,
        relationship_mappings="""
    relationship_mappings:
      blocking:
        surface: issue_link
        link_type: Blocks
        direction: sideways
""",
    )
    site = jira_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(
        site,
        jira_issue_payload(),
        remote_links=remote_links_payload(),
        fetched_at="2026-05-15T10:00:00.000+0900",
    )
    cache.relationships_pending_file(site, "TM-1234").write_text("blocking:\n  - TM-1235\n", encoding="utf-8")
    runner = FakeRunner({})

    with pytest.raises(ProviderOperationError, match="requires direction"):
        dispatch_write(tmp_path, runner, "apply_relationships", issue="TM-1234", pending_relationships=True)

    assert runner.requests == []


def test_data_center_stale_cache_blocks_write_before_put(tmp_path: Path) -> None:
    write_jira_config(tmp_path)
    site = jira_site(tmp_path)
    cache = JiraDataCenterIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(
        site,
        jira_issue_payload(body="Cached body."),
        remote_links=remote_links_payload(),
        fetched_at="2026-05-15T10:00:00.000+0900",
    )
    runner = FakeRunner(
        {
            curl_args(issue_url()): result(
                curl_args(issue_url()),
                stdout=json.dumps(jira_issue_payload(body="Newer provider body.")),
            )
        }
    )
    newer = jira_issue_payload(body="Newer provider body.")
    newer["fields"]["updated"] = "2026-05-15T11:00:00.000+0900"  # type: ignore[index]
    runner.responses[curl_args(issue_url())] = result(curl_args(issue_url()), stdout=json.dumps(newer))

    with pytest.raises(ProviderFreshnessError, match="Stale workflow cache"):
        dispatch_write(tmp_path, runner, "update", issue="TM-1234", from_cache=True)

    assert all(request.args != curl_write_args() for request in runner.requests)
