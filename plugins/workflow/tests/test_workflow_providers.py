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
    ProviderGuardError,
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


def github_repo() -> GitHubRepository:
    return GitHubRepository(host="github.com", owner="studykit", name="studykit-plugins")


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


def test_write_operations_call_guard_before_provider(context: ProviderContext) -> None:
    events: list[str] = []
    registry = ProviderRegistry()
    registry.register(RecordingIssueProvider(transport=TRANSPORT_NATIVE, events=events))

    def guard(request: ProviderRequest) -> None:
        events.append(f"guard:{request.operation}")

    dispatcher = ProviderDispatcher(registry, guard=guard)

    response = dispatcher.dispatch(issue_request("update", context, id="T-1"))

    assert response.payload["updated"] == "T-1"
    assert events == ["guard:update", "native:update"]


def test_write_operations_require_guard(context: ProviderContext) -> None:
    events: list[str] = []
    registry = ProviderRegistry()
    registry.register(RecordingIssueProvider(transport=TRANSPORT_NATIVE, events=events))
    dispatcher = ProviderDispatcher(registry)

    with pytest.raises(ProviderGuardError):
        dispatcher.dispatch(issue_request("update", context, id="T-1"))

    assert events == []


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
            assert events == ["guard:update", "freshness", "edit"]
            return CommandResult(request=request, returncode=0)
        if request.args == gh_issue_view_args(39, "body"):
            events.append("verify")
            return CommandResult(
                request=request,
                returncode=0,
                stdout=json.dumps({"body": "Updated body."}),
            )
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    def guard(request: ProviderRequest) -> None:
        events.append(f"guard:{request.operation}")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner), guard=guard)

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
    assert events == ["guard:update", "freshness", "edit", "verify"]


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

    def guard(request: ProviderRequest) -> None:
        events.append(f"guard:{request.operation}")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner), guard=guard)

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

    assert events == ["guard:update", "freshness"]


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
            assert events == ["guard:update", "freshness", "edit"]
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

    def guard(request: ProviderRequest) -> None:
        events.append(f"guard:{request.operation}")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner), guard=guard)

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
    assert events == ["guard:update", "freshness", "edit", "verify-edit", "close", "verify-state", "refresh"]


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

    def guard(request: ProviderRequest) -> None:
        events.append(f"guard:{request.operation}")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner), guard=guard)

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

    assert events == ["guard:update", "freshness"]


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
            assert events == ["guard:create", "create"]
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

    def guard(request: ProviderRequest) -> None:
        events.append(f"guard:{request.operation}")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner), guard=guard)

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
    assert events == ["guard:create", "create", "verify", "refresh"]


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
            assert events == ["guard:add_comment", "comment"]
            return CommandResult(request=request, returncode=0)
        if request.args == gh_issue_view_args(39, ",".join(DEFAULT_ISSUE_FIELDS)):
            events.append("refresh")
            return CommandResult(request=request, returncode=0, stdout=json.dumps(commented_issue_payload()))
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    def guard(request: ProviderRequest) -> None:
        events.append(f"guard:{request.operation}")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner), guard=guard)

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
    assert events == ["guard:add_comment", "comment", "refresh"]


def test_read_operations_do_not_require_guard(context: ProviderContext) -> None:
    events: list[str] = []
    registry = ProviderRegistry()
    registry.register(RecordingIssueProvider(transport=TRANSPORT_NATIVE, events=events))
    dispatcher = ProviderDispatcher(registry)

    response = dispatcher.dispatch(issue_request("get", context, id="T-1"))

    assert response.payload["payload"]["id"] == "T-1"
    assert events == ["native:get"]


def test_knowledge_provider_dispatch_uses_same_registry_and_guard(context: ProviderContext) -> None:
    events: list[str] = []
    registry = ProviderRegistry()
    registry.register(RecordingKnowledgeProvider(transport=TRANSPORT_NATIVE, events=events))

    def guard(request: ProviderRequest) -> None:
        events.append(f"guard:{request.operation}")

    dispatcher = ProviderDispatcher(registry, guard=guard)

    response = dispatcher.dispatch(knowledge_request("link", context, source="A", target="B"))

    assert response.role == "knowledge"
    assert response.payload["linked"] is True
    assert events == ["guard:link", "native:link"]


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
