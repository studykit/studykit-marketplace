"""Tests for workflow provider interface dispatch."""

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

from workflow_cache import GitHubIssueCache  # noqa: E402
from workflow_command import CommandRequest, CommandResult  # noqa: E402
from workflow_config import parse_workflow_config  # noqa: E402
from workflow_github import DEFAULT_ISSUE_FIELDS, GitHubRepository  # noqa: E402
from workflow_providers import (  # noqa: E402
    CACHE_POLICY_REFRESH,
    ISSUE_PROVIDER_OPERATIONS,
    KNOWLEDGE_PROVIDER_OPERATIONS,
    TRANSPORT_MCP,
    TRANSPORT_NATIVE,
    TRANSPORT_PRIORITY,
    IssueProvider,
    KnowledgeProvider,
    ProviderContext,
    ProviderDispatcher,
    ProviderFreshnessError,
    ProviderOperationError,
    ProviderRegistry,
    ProviderRequest,
    default_provider_registry,
    request_from_config,
)


class RecordingIssueProvider(IssueProvider):
    def __init__(self, *, transport: str, events: list[str]):
        super().__init__(kind="fake", transport=transport)
        self.events = events

    def get(self, request: ProviderRequest) -> Mapping[str, Any]:
        self.events.append(f"{self.transport}:get")
        return {"transport": self.transport, "payload": dict(request.payload)}

    def update(self, request: ProviderRequest) -> Mapping[str, Any]:
        self.events.append(f"{self.transport}:update")
        return {"transport": self.transport, "updated": request.payload.get("id")}


class RecordingKnowledgeProvider(KnowledgeProvider):
    def __init__(self, *, transport: str, events: list[str]):
        super().__init__(kind="fake", transport=transport)
        self.events = events

    def get(self, request: ProviderRequest) -> Mapping[str, Any]:
        self.events.append(f"{self.transport}:get")
        return {"transport": self.transport, "payload": dict(request.payload)}

    def link(self, request: ProviderRequest) -> Mapping[str, Any]:
        self.events.append(f"{self.transport}:link")
        return {"transport": self.transport, "linked": True}


@pytest.fixture
def context(tmp_path: Path) -> ProviderContext:
    return ProviderContext(project=tmp_path, artifact_type="task", session_id="s1")


def issue_request(operation: str, context: ProviderContext, **payload: Any) -> ProviderRequest:
    return ProviderRequest(
        role="issue",
        kind="fake",
        operation=operation,
        context=context,
        payload=payload,
    )


def knowledge_request(operation: str, context: ProviderContext, **payload: Any) -> ProviderRequest:
    return ProviderRequest(
        role="knowledge",
        kind="fake",
        operation=operation,
        context=context,
        payload=payload,
    )


def git_args(project: Path, *args: str) -> tuple[str, ...]:
    return ("git", "-C", str(project.resolve(strict=False)), *args)


def gh_issue_freshness_args(issue: int | str) -> tuple[str, ...]:
    return (
        "gh",
        "issue",
        "view",
        str(issue),
        "--repo",
        "studykit/studykit-plugins",
        "--json",
        "number,updatedAt",
    )


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


def gh_api_args(*args: str) -> tuple[str, ...]:
    return ("gh", "api", *args)


def github_repo() -> GitHubRepository:
    return GitHubRepository(host="github.com", owner="studykit", name="studykit-plugins")


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


def cached_issue_payload(*, updated_at: str = "2026-05-13T12:00:00Z") -> dict[str, object]:
    return {
        "number": 39,
        "title": "Write-back freshness checks",
        "state": "OPEN",
        "stateReason": None,
        "body": "Cached body.",
        "labels": [],
        "updatedAt": updated_at,
        "comments": [],
    }


def created_issue_payload() -> dict[str, object]:
    return {
        "number": 51,
        "title": "Draft issue",
        "state": "OPEN",
        "stateReason": None,
        "body": "Draft body.\n",
        "labels": [{"name": "task"}, {"name": "workflow"}],
        "updatedAt": "2026-05-14T00:00:00Z",
        "comments": [],
    }


def writeback_issue_payload() -> dict[str, object]:
    return {
        "number": 39,
        "title": "Cached write-back title",
        "state": "CLOSED",
        "stateReason": "COMPLETED",
        "body": "Cached write-back body.",
        "labels": [{"name": "task"}, {"name": "workflow"}],
        "updatedAt": "2026-05-13T12:00:00Z",
        "comments": [],
    }


def commented_issue_payload() -> dict[str, object]:
    return {
        "number": 39,
        "title": "Issue with comment",
        "state": "OPEN",
        "stateReason": None,
        "body": "Issue body.",
        "labels": [],
        "updatedAt": "2026-05-14T00:10:00Z",
        "comments": [
            {
                "id": "IC_kwDOQplzFM8AAAABCKrz_g",
                "url": "https://github.com/studykit/studykit-plugins/issues/39#issuecomment-4440388606",
                "author": {"login": "studykit"},
                "body": "Pending comment body.\n",
                "createdAt": "2026-05-14T00:00:00Z",
                "updatedAt": "2026-05-14T00:00:00Z",
            }
        ],
    }


def test_provider_operation_sets_cover_issue_and_knowledge_contracts() -> None:
    assert ISSUE_PROVIDER_OPERATIONS >= {
        "create",
        "update",
        "get",
        "search",
        "comments",
        "logs",
        "add_comment",
        "set_parent",
        "set_dependency",
        "apply_relationships",
    }
    assert KNOWLEDGE_PROVIDER_OPERATIONS >= {
        "create",
        "update",
        "get",
        "search",
        "metadata",
        "links",
        "comments",
        "set_metadata",
        "link",
        "add_comment",
    }


def test_transport_priority_prefers_native_before_mcp() -> None:
    assert TRANSPORT_PRIORITY == (TRANSPORT_NATIVE, TRANSPORT_MCP)


def test_dispatch_prefers_native_transport(context: ProviderContext) -> None:
    events: list[str] = []
    registry = ProviderRegistry()
    registry.register(RecordingIssueProvider(transport=TRANSPORT_MCP, events=events))
    registry.register(RecordingIssueProvider(transport=TRANSPORT_NATIVE, events=events))
    dispatcher = ProviderDispatcher(registry)

    response = dispatcher.dispatch(issue_request("get", context, id="T-1"))

    assert response.transport == TRANSPORT_NATIVE
    assert response.payload["transport"] == TRANSPORT_NATIVE
    assert events == ["native:get"]


def test_dispatch_uses_mcp_fallback_when_native_is_absent(context: ProviderContext) -> None:
    events: list[str] = []
    registry = ProviderRegistry()
    registry.register(RecordingIssueProvider(transport=TRANSPORT_MCP, events=events))
    dispatcher = ProviderDispatcher(registry)

    response = dispatcher.dispatch(issue_request("get", context, id="T-1"))

    assert response.transport == TRANSPORT_MCP
    assert events == ["mcp:get"]


def test_explicit_transport_overrides_priority(context: ProviderContext) -> None:
    events: list[str] = []
    registry = ProviderRegistry()
    registry.register(RecordingIssueProvider(transport=TRANSPORT_MCP, events=events))
    registry.register(RecordingIssueProvider(transport=TRANSPORT_NATIVE, events=events))
    dispatcher = ProviderDispatcher(registry)
    request = issue_request("get", context, id="T-1")

    response = dispatcher.dispatch(request.with_transport(TRANSPORT_MCP))

    assert response.transport == TRANSPORT_MCP
    assert events == ["mcp:get"]


def test_write_operations_dispatch_to_provider(context: ProviderContext) -> None:
    events: list[str] = []
    registry = ProviderRegistry()
    registry.register(RecordingIssueProvider(transport=TRANSPORT_NATIVE, events=events))
    dispatcher = ProviderDispatcher(registry)

    response = dispatcher.dispatch(issue_request("update", context, id="T-1"))

    assert response.payload["updated"] == "T-1"
    assert events == ["native:update"]


def test_github_issue_update_can_request_freshness_check_before_mutation(tmp_path: Path) -> None:
    GitHubIssueCache.for_project(tmp_path).write_issue_bundle(
        github_repo(),
        cached_issue_payload(),
        fetched_at="2026-05-13T12:34:56Z",
    )
    events: list[str] = []

    def runner(request: CommandRequest) -> CommandResult:
        if request.args == git_args(tmp_path, "remote", "get-url", "origin"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            )
        if request.args == gh_issue_freshness_args(39):
            events.append("freshness")
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps({"number": 39, "updatedAt": "2026-05-13T12:00:00Z"}),
            )
        if request.args[:3] == ("gh", "issue", "edit"):
            events.append("edit")
            body_file = Path(request.args[request.args.index("--body-file") + 1])
            assert body_file.read_text(encoding="utf-8") == "Updated body."
            assert events == ["freshness", "edit"]
            return CommandResult(request=request, returncode=0)
        if request.args == gh_issue_view_args(39, "body"):
            events.append("verify")
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps({"body": "Updated body."}),
            )
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))

    response = dispatcher.dispatch(
        ProviderRequest(
            role="issue",
            kind="github",
            operation="update",
            context=ProviderContext(project=tmp_path, artifact_type="task", session_id="s1"),
            payload={"issue": 39, "body": "Updated body.", "freshness_check": True},
        )
    )

    assert response.payload["operation"] == "edit_issue_body"
    assert response.payload["verified"] is True
    assert events == ["freshness", "edit", "verify"]


def test_github_issue_update_blocks_stale_freshness_before_mutation(tmp_path: Path) -> None:
    GitHubIssueCache.for_project(tmp_path).write_issue_bundle(
        github_repo(),
        cached_issue_payload(),
        fetched_at="2026-05-13T12:34:56Z",
    )
    events: list[str] = []

    def runner(request: CommandRequest) -> CommandResult:
        if request.args == git_args(tmp_path, "remote", "get-url", "origin"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            )
        if request.args == gh_issue_freshness_args(39):
            events.append("freshness")
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps({"number": 39, "updatedAt": "2026-05-13T13:00:00Z"}),
            )
        if request.args[:3] == ("gh", "issue", "edit"):
            events.append("edit")
            return CommandResult(request=request, returncode=0)
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))

    with pytest.raises(ProviderFreshnessError, match="Refresh the provider cache before writing"):
        dispatcher.dispatch(
            ProviderRequest(
                role="issue",
                kind="github",
                operation="update",
                context=ProviderContext(project=tmp_path, artifact_type="task", session_id="s1"),
                payload={"issue": 39, "body": "Updated body.", "freshness_check": True},
            )
        )

    assert events == ["freshness"]


def test_github_issue_update_from_cache_projection_checks_freshness_and_refreshes_cache(
    tmp_path: Path,
) -> None:
    GitHubIssueCache.for_project(tmp_path).write_issue_bundle(
        github_repo(),
        writeback_issue_payload(),
        fetched_at="2026-05-13T12:34:56Z",
    )
    events: list[str] = []

    def runner(request: CommandRequest) -> CommandResult:
        if request.args == git_args(tmp_path, "remote", "get-url", "origin"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            )
        if request.args == gh_issue_view_args(39, "number,updatedAt,labels,state,stateReason"):
            events.append("freshness")
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps(
                    {
                        "number": 39,
                        "updatedAt": "2026-05-13T12:00:00Z",
                        "labels": [{"name": "task"}, {"name": "old"}],
                        "state": "OPEN",
                        "stateReason": None,
                    }
                ),
            )
        if request.args[:3] == ("gh", "issue", "edit"):
            events.append("edit")
            body_file = Path(request.args[request.args.index("--body-file") + 1])
            assert body_file.read_text(encoding="utf-8") == "Cached write-back body."
            assert request.args[request.args.index("--title") + 1] == "Cached write-back title"
            assert ("--add-label", "workflow") in zip(request.args, request.args[1:])
            assert ("--remove-label", "old") in zip(request.args, request.args[1:])
            assert events == ["freshness", "edit"]
            return CommandResult(request=request, returncode=0)
        if request.args == gh_issue_view_args(39, "title,body,labels"):
            events.append("verify-edit")
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps(
                    {
                        "title": "Cached write-back title",
                        "body": "Cached write-back body.",
                        "labels": [{"name": "task"}, {"name": "workflow"}],
                    }
                ),
            )
        if request.args == (
            "gh",
            "issue",
            "close",
            "39",
            "--repo",
            "studykit/studykit-plugins",
            "--reason",
            "completed",
        ):
            events.append("close")
            return CommandResult(request=request, returncode=0)
        if request.args == gh_issue_view_args(39, "state,stateReason"):
            events.append("verify-state")
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps({"state": "CLOSED", "stateReason": "COMPLETED"}),
            )
        if request.args == gh_issue_view_args(39, ",".join(DEFAULT_ISSUE_FIELDS)):
            events.append("refresh")
            return CommandResult(request=request, returncode=0, stdout=json.dumps(writeback_issue_payload()))
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))

    response = dispatcher.dispatch(
        ProviderRequest(
            role="issue",
            kind="github",
            operation="update",
            context=ProviderContext(project=tmp_path, artifact_type="task", session_id="s1"),
            payload={"issue": 39, "from_cache": True},
        )
    )

    assert response.payload["operation"] == "update_issue_from_cache"
    assert response.payload["issue"] == "39"
    assert response.payload["verified"] is True
    assert response.payload["cache_refreshed"] is True
    assert GitHubIssueCache.for_project(tmp_path).read_issue(github_repo(), 39)["body"] == "Cached write-back body."
    assert events == ["freshness", "edit", "verify-edit", "close", "verify-state", "refresh"]


def test_github_issue_update_from_cache_blocks_stale_projection_before_mutation(
    tmp_path: Path,
) -> None:
    GitHubIssueCache.for_project(tmp_path).write_issue_bundle(
        github_repo(),
        writeback_issue_payload(),
        fetched_at="2026-05-13T12:34:56Z",
    )
    events: list[str] = []

    def runner(request: CommandRequest) -> CommandResult:
        if request.args == git_args(tmp_path, "remote", "get-url", "origin"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            )
        if request.args == gh_issue_view_args(39, "number,updatedAt,labels,state,stateReason"):
            events.append("freshness")
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps(
                    {
                        "number": 39,
                        "updatedAt": "2026-05-13T13:00:00Z",
                        "labels": [{"name": "task"}],
                        "state": "OPEN",
                        "stateReason": None,
                    }
                ),
            )
        if request.args[:3] == ("gh", "issue", "edit"):
            events.append("edit")
            return CommandResult(request=request, returncode=0)
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))

    with pytest.raises(ProviderFreshnessError, match="Refresh the provider cache before writing"):
        dispatcher.dispatch(
            ProviderRequest(
                role="issue",
                kind="github",
                operation="update",
                context=ProviderContext(project=tmp_path, artifact_type="task", session_id="s1"),
                payload={"issue": 39, "from_cache": True},
            )
        )

    assert events == ["freshness"]


def test_github_issue_create_from_pending_draft_refreshes_cache_and_finalizes_pending(
    tmp_path: Path,
) -> None:
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=github_repo())
    draft_path = cache.pending_issue_file(github_repo(), "draft-1")
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
    events: list[str] = []

    def runner(request: CommandRequest) -> CommandResult:
        if request.args == git_args(tmp_path, "remote", "get-url", "origin"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            )
        if request.args[:3] == ("gh", "issue", "create"):
            events.append("create")
            body_file = Path(request.args[request.args.index("--body-file") + 1])
            assert body_file.read_text(encoding="utf-8") == "Draft body.\n"
            assert request.args[request.args.index("--title") + 1] == "Draft issue"
            assert request.args.count("--label") == 2
            assert events == ["create"]
            return CommandResult(
                request=request,
                returncode=0,
                stdout="https://github.com/studykit/studykit-plugins/issues/51\n",
            )
        if request.args == gh_issue_view_args(51, "title,body,labels,state,stateReason"):
            events.append("verify")
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
        if request.args == gh_issue_view_args(51, ",".join(DEFAULT_ISSUE_FIELDS)):
            events.append("refresh")
            return CommandResult(request=request, returncode=0, stdout=json.dumps(created_issue_payload()))
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))

    response = dispatcher.dispatch(
        ProviderRequest(
            role="issue",
            kind="github",
            operation="create",
            context=ProviderContext(project=tmp_path, artifact_type="task", session_id="s1"),
            payload={"pending_local_id": "draft-1"},
        )
    )

    assert response.payload["operation"] == "create_issue"
    assert response.payload["issue"] == "51"
    assert response.payload["verified"] is True
    assert response.payload["cache_refreshed"] is True
    assert response.payload["pending_finalized"] is True
    assert cache.read_issue(github_repo(), 51)["body"] == "Draft body.\n"
    assert not draft_path.exists()
    assert Path(response.payload["pending"]["archived_issue"]).is_file()
    assert events == ["create", "verify", "refresh"]


def test_github_issue_add_comment_from_pending_files_dispatches_and_refreshes_cache(
    tmp_path: Path,
) -> None:
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=github_repo())
    cache.write_issue_bundle(github_repo(), cached_issue_payload(), fetched_at="2026-05-14T00:00:00Z")
    pending_dir = cache.comments_pending_dir(github_repo(), 39)
    pending_dir.mkdir(parents=True)
    pending_file = pending_dir / "2026-05-14T000000Z-local.md"
    pending_file.write_text(
        """---
schema_version: 1
---

Pending comment body.
""",
        encoding="utf-8",
    )
    events: list[str] = []

    def runner(request: CommandRequest) -> CommandResult:
        if request.args == git_args(tmp_path, "remote", "get-url", "origin"):
            return CommandResult(
                request=request,
                returncode=0,
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            )
        if request.args[:3] == ("gh", "issue", "comment"):
            events.append("comment")
            body_file = Path(request.args[request.args.index("--body-file") + 1])
            assert body_file.read_text(encoding="utf-8") == "Pending comment body.\n"
            assert events == ["comment"]
            return CommandResult(request=request, returncode=0)
        if request.args == gh_issue_view_args(39, ",".join(DEFAULT_ISSUE_FIELDS)):
            events.append("refresh")
            return CommandResult(request=request, returncode=0, stdout=json.dumps(commented_issue_payload()))
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))

    response = dispatcher.dispatch(
        ProviderRequest(
            role="issue",
            kind="github",
            operation="add_comment",
            context=ProviderContext(project=tmp_path, artifact_type="task", session_id="s1"),
            payload={"issue": 39, "from_pending": True},
        )
    )

    assert response.payload["operation"] == "append_pending_comments"
    assert response.payload["issue"] == "39"
    assert response.payload["appended"] == 1
    assert response.payload["cache_refreshed"] is True
    assert response.payload["pending_files"] == ["2026-05-14T000000Z-local.md"]
    assert not pending_file.exists()
    cached = cache.read_comments(github_repo(), 39)
    assert cached["comments"][0]["id"] == "4440388606"
    assert cached["comments"][0]["body"] == "Pending comment body.\n"
    assert events == ["comment", "refresh"]


def test_github_issue_apply_relationships_from_pending_file_dispatches_refreshes_and_cleans(
    tmp_path: Path,
) -> None:
    write_config(tmp_path)
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=github_repo())
    cache.write_issue_bundle(
        github_repo(),
        {**cached_issue_payload(updated_at="2026-05-14T00:00:00Z"), "number": 44},
        fetched_at="2026-05-14T00:00:00Z",
    )
    pending_path = cache.relationships_pending_file(github_repo(), 44)
    pending_path.write_text(
        """
schema_version: 1
operations:
  - action: add
    relationship: parent
    issue: "#36"
  - action: add
    relationship: blocked_by
    issue: "#33"
""".lstrip(),
        encoding="utf-8",
    )
    events: list[str] = []
    issue_44_reads = 0

    def rest_issue(number: int, issue_id: int, *, updated_at: str = "2026-05-14T00:00:00Z") -> dict[str, object]:
        return {
            "id": issue_id,
            "number": number,
            "title": f"Issue {number}",
            "state": "open",
            "state_reason": None,
            "updated_at": updated_at,
        }

    def runner(request: CommandRequest) -> CommandResult:
        nonlocal issue_44_reads
        if request.args == gh_issue_view_args(44, "number,updatedAt"):
            events.append("freshness")
            return CommandResult(request=request, returncode=0, stdout=json.dumps({"number": 44, "updatedAt": "2026-05-14T00:00:00Z"}))
        if request.args == gh_api_args("repos/studykit/studykit-plugins/issues/44"):
            issue_44_reads += 1
            events.append("issue-44-id" if issue_44_reads == 1 else "relationships-issue")
            return CommandResult(request=request, returncode=0, stdout=json.dumps(rest_issue(44, 4400)))
        if request.args == gh_api_args("repos/studykit/studykit-plugins/issues/33"):
            events.append("issue-33-id")
            return CommandResult(request=request, returncode=0, stdout=json.dumps(rest_issue(33, 3300)))
        if request.args == gh_api_args(
            "-X",
            "POST",
            "repos/studykit/studykit-plugins/issues/36/sub_issues",
            "-F",
            "sub_issue_id=4400",
            "-F",
            "replace_parent=true",
        ):
            events.append("add-parent")
            return CommandResult(request=request, returncode=0, stdout=json.dumps(rest_issue(44, 4400)))
        if request.args == gh_api_args(
            "-X",
            "POST",
            "repos/studykit/studykit-plugins/issues/44/dependencies/blocked_by",
            "-F",
            "issue_id=3300",
        ):
            events.append("add-dependency")
            return CommandResult(request=request, returncode=0, stdout=json.dumps(rest_issue(33, 3300)))
        if request.args == gh_api_args("repos/studykit/studykit-plugins/issues/44/parent"):
            events.append("relationships-parent")
            return CommandResult(request=request, returncode=0, stdout=json.dumps(rest_issue(36, 3600)))
        if request.args == gh_api_args("repos/studykit/studykit-plugins/issues/44/sub_issues", "--paginate"):
            events.append("relationships-children")
            return CommandResult(request=request, returncode=0, stdout="[]")
        if request.args == gh_api_args("repos/studykit/studykit-plugins/issues/44/dependencies/blocked_by", "--paginate"):
            events.append("relationships-blocked-by")
            return CommandResult(request=request, returncode=0, stdout=json.dumps([rest_issue(33, 3300)]))
        if request.args == gh_api_args("repos/studykit/studykit-plugins/issues/44/dependencies/blocking", "--paginate"):
            events.append("relationships-blocking")
            return CommandResult(request=request, returncode=0, stdout="[]")
        return CommandResult(request=request, returncode=127, stderr=f"unexpected command: {request.args}")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))

    response = dispatcher.dispatch(
        ProviderRequest(
            role="issue",
            kind="github",
            operation="apply_relationships",
            context=ProviderContext(project=tmp_path, artifact_type="task", session_id="s1"),
            payload={"issue": 44, "from_pending": True},
        )
    )

    assert response.payload["operation"] == "apply_relationships"
    assert response.payload["issue"] == "44"
    assert response.payload["applied"] == 2
    assert response.payload["cache_refreshed"] is True
    assert response.payload["pending_file"] == "relationships-pending.yml"
    assert not pending_path.exists()
    relationships = cache.read_relationships(github_repo(), 44)
    assert relationships["parent"]["number"] == 36
    assert relationships["dependencies"]["blocked_by"][0]["number"] == 33
    assert events == [
        "freshness",
        "issue-44-id",
        "add-parent",
        "issue-33-id",
        "add-dependency",
        "relationships-issue",
        "relationships-parent",
        "relationships-children",
        "relationships-blocked-by",
        "relationships-blocking",
    ]


def test_github_issue_apply_relationships_rejects_unsupported_without_mutation(tmp_path: Path) -> None:
    write_config(tmp_path)
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=github_repo())
    cache.write_issue_bundle(
        github_repo(),
        {**cached_issue_payload(updated_at="2026-05-14T00:00:00Z"), "number": 44},
        fetched_at="2026-05-14T00:00:00Z",
    )
    pending_path = cache.relationships_pending_file(github_repo(), 44)
    pending_path.write_text(
        """
schema_version: 1
operations:
  - action: add
    relationship: related
    issue: "#33"
""".lstrip(),
        encoding="utf-8",
    )
    events: list[str] = []

    def runner(request: CommandRequest) -> CommandResult:
        events.append("mutation" if request.args[:3] == ("gh", "api", "-X") else "read")
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))

    with pytest.raises(ProviderOperationError, match="unsupported GitHub relationship operation"):
        dispatcher.dispatch(
            ProviderRequest(
                role="issue",
                kind="github",
                operation="apply_relationships",
                context=ProviderContext(project=tmp_path, artifact_type="task", session_id="s1"),
                payload={"issue": 44, "from_pending": True},
            )
        )

    assert "mutation" not in events
    assert pending_path.exists()


def test_read_operations_dispatch_to_provider(context: ProviderContext) -> None:
    events: list[str] = []
    registry = ProviderRegistry()
    registry.register(RecordingIssueProvider(transport=TRANSPORT_NATIVE, events=events))
    dispatcher = ProviderDispatcher(registry)

    response = dispatcher.dispatch(issue_request("get", context, id="T-1"))

    assert response.payload["payload"]["id"] == "T-1"
    assert events == ["native:get"]


def test_knowledge_provider_dispatch_uses_same_registry(context: ProviderContext) -> None:
    events: list[str] = []
    registry = ProviderRegistry()
    registry.register(RecordingKnowledgeProvider(transport=TRANSPORT_NATIVE, events=events))

    dispatcher = ProviderDispatcher(registry)

    response = dispatcher.dispatch(knowledge_request("link", context, source="A", target="B"))

    assert response.role == "knowledge"
    assert response.payload["linked"] is True
    assert events == ["native:link"]


def test_cache_policy_is_preserved_for_future_cache_layer(tmp_path: Path) -> None:
    events: list[str] = []
    registry = ProviderRegistry()
    registry.register(RecordingIssueProvider(transport=TRANSPORT_NATIVE, events=events))
    dispatcher = ProviderDispatcher(registry)
    context = ProviderContext(
        project=tmp_path,
        artifact_type="task",
        cache_policy=CACHE_POLICY_REFRESH,
    )

    response = dispatcher.dispatch(issue_request("get", context, id="T-1"))

    assert response.cache_policy == CACHE_POLICY_REFRESH


def test_request_from_config_selects_provider_for_role(tmp_path: Path) -> None:
    config = parse_workflow_config(
        {
            "version": 1,
            "providers": {
                "issues": {"kind": "github"},
                "knowledge": {"kind": "confluence"},
            },
            "issue_id_format": "github",
        },
        path=tmp_path / ".workflow/config.yml",
    )

    issue = request_from_config(config, role="issue", operation="get", artifact_type="task")
    knowledge = request_from_config(
        config,
        role="knowledge",
        operation="get",
        artifact_type="spec",
    )

    assert issue.kind == "github"
    assert knowledge.kind == "confluence"


def test_default_registry_registers_github_native_issue_provider() -> None:
    registry = default_provider_registry()

    provider = registry.resolve(role="issue", kind="github")

    assert provider.transport == TRANSPORT_NATIVE
