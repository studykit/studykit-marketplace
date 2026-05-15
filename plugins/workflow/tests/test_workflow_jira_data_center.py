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


def write_jira_config(project: Path, *, deployment: str = "data-center") -> None:
    path = project / ".workflow" / "config.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
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
  knowledge:
    kind: github
issue_id_format: jira
""".lstrip(),
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


def issue_url(issue: str = "TM-1234") -> str:
    return f"https://jira.daumkakao.com/rest/api/2/issue/{issue}"


def remote_links_url(issue: str = "TM-1234") -> str:
    return f"https://jira.daumkakao.com/rest/api/2/issue/{issue}/remotelink"


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


def dispatch_write(project: Path, runner: FakeRunner, operation: str, **payload: object):
    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner), guard=lambda request: None)
    return dispatcher.dispatch(
        ProviderRequest(
            role="issue",
            kind="jira",
            operation=operation,
            context=ProviderContext(project=project, artifact_type="task"),
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
