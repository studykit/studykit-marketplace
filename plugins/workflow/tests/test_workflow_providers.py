"""Tests for workflow provider interface dispatch."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_config import parse_workflow_config  # noqa: E402
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
        },
        path=tmp_path / "workflow.config.yml",
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
