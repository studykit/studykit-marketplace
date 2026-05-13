#!/usr/bin/env python3
"""Provider interface scaffold for workflow issue and knowledge operations.

The provider layer owns dispatch across provider kinds and transports. Native
wrappers are preferred first, and MCP providers are fallback transports.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from authoring_guard import evaluate_authoring_guard
from authoring_ledger import LedgerError
from authoring_resolver import ResolverError
from workflow_command import CommandRunner
from workflow_cache import (
    FreshnessMetadata,
    GitHubIssueCache,
    WorkflowCacheError,
    WorkflowFreshnessConflict,
    require_provider_freshness,
)
from workflow_config import ProviderConfig, WorkflowConfig, normalize_role
from workflow_github import (
    DEFAULT_ISSUE_FIELDS,
    close_issue,
    comment_issue,
    create_issue,
    edit_issue_body,
    issue_body_edit_history,
    issue_events,
    issue_timeline,
    normalize_issue_number,
    reopen_issue,
    resolve_github_repository,
    view_issue,
)

ROLE_ISSUE = "issue"
ROLE_KNOWLEDGE = "knowledge"

TRANSPORT_NATIVE = "native"
TRANSPORT_MCP = "mcp"
TRANSPORT_PRIORITY = (TRANSPORT_NATIVE, TRANSPORT_MCP)

ISSUE_READ_OPERATIONS = frozenset({"get", "search", "comments", "logs"})
ISSUE_WRITE_OPERATIONS = frozenset(
    {
        "create",
        "update",
        "add_comment",
        "set_parent",
        "set_dependency",
        "close",
        "reopen",
    }
)
ISSUE_PROVIDER_OPERATIONS = ISSUE_READ_OPERATIONS | ISSUE_WRITE_OPERATIONS

KNOWLEDGE_READ_OPERATIONS = frozenset({"get", "search", "metadata", "links", "comments"})
KNOWLEDGE_WRITE_OPERATIONS = frozenset(
    {"create", "update", "set_metadata", "link", "add_comment"}
)
KNOWLEDGE_PROVIDER_OPERATIONS = KNOWLEDGE_READ_OPERATIONS | KNOWLEDGE_WRITE_OPERATIONS

CACHE_POLICY_DEFAULT = "default"
CACHE_POLICY_REFRESH = "refresh"
CACHE_POLICY_BYPASS = "bypass"
CACHE_POLICIES = {CACHE_POLICY_DEFAULT, CACHE_POLICY_REFRESH, CACHE_POLICY_BYPASS}


class ProviderError(RuntimeError):
    """Base error for provider dispatch failures."""


class ProviderOperationError(ProviderError):
    """Raised when a provider operation is unsupported or malformed."""


class ProviderNotFoundError(ProviderError):
    """Raised when no provider transport is registered for a role and kind."""


class ProviderGuardError(ProviderError):
    """Raised when an authoring guard blocks or cannot evaluate a write."""


class ProviderFreshnessError(ProviderError):
    """Raised when a provider write is blocked by stale cache metadata."""


@dataclass(frozen=True)
class ProviderContext:
    """Context shared by provider operations.

    ``cache_policy`` is a stable insertion point for the local provider read
    cache planned in #39. This scaffold preserves the value but does not
    implement caching.
    """

    project: Path
    artifact_type: str
    session_id: str | None = None
    state_dir: Path | None = None
    cache_policy: str = CACHE_POLICY_DEFAULT

    def __post_init__(self) -> None:
        if self.cache_policy not in CACHE_POLICIES:
            choices = ", ".join(sorted(CACHE_POLICIES))
            raise ProviderOperationError(
                f"unsupported cache policy: {self.cache_policy}. Use one of: {choices}"
            )

    def to_json(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "project": str(self.project),
            "artifact_type": self.artifact_type,
            "cache_policy": self.cache_policy,
        }
        if self.session_id:
            result["session_id"] = self.session_id
        if self.state_dir is not None:
            result["state_dir"] = str(self.state_dir)
        return result


@dataclass(frozen=True)
class ProviderRequest:
    """One provider operation request."""

    role: str
    kind: str
    operation: str
    context: ProviderContext
    payload: Mapping[str, Any] = field(default_factory=dict)
    transport: str | None = None

    def with_transport(self, transport: str) -> ProviderRequest:
        return replace(self, transport=transport)

    @property
    def normalized_role(self) -> str:
        return normalize_role(self.role)

    @property
    def is_write(self) -> bool:
        if self.normalized_role == ROLE_ISSUE:
            return self.operation in ISSUE_WRITE_OPERATIONS
        return self.operation in KNOWLEDGE_WRITE_OPERATIONS

    def to_json(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "role": self.normalized_role,
            "kind": self.kind,
            "operation": self.operation,
            "context": self.context.to_json(),
            "payload": dict(self.payload),
        }
        if self.transport:
            result["transport"] = self.transport
        return result


@dataclass(frozen=True)
class ProviderResponse:
    """Structured provider operation response."""

    role: str
    kind: str
    transport: str
    operation: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    cache_policy: str = CACHE_POLICY_DEFAULT

    def to_json(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "kind": self.kind,
            "transport": self.transport,
            "operation": self.operation,
            "payload": dict(self.payload),
            "cache_policy": self.cache_policy,
        }


GuardCallback = Callable[[ProviderRequest], None]


class ProviderTransport:
    """Base class for provider transport adapters."""

    role: str
    kind: str
    transport: str
    operations: frozenset[str]

    def __init__(self, *, kind: str, transport: str):
        self.kind = kind
        self.transport = transport

    def call(self, request: ProviderRequest) -> ProviderResponse:
        self._validate_request(request)
        handler = getattr(self, request.operation, None)
        if handler is None or not callable(handler):
            raise ProviderOperationError(
                f"{self.role} provider {self.kind}/{self.transport} does not implement "
                f"operation: {request.operation}"
            )
        payload = handler(request)
        if not isinstance(payload, Mapping):
            raise ProviderOperationError("provider operation returned non-mapping payload")
        return ProviderResponse(
            role=self.role,
            kind=self.kind,
            transport=self.transport,
            operation=request.operation,
            payload=payload,
            cache_policy=request.context.cache_policy,
        )

    def _validate_request(self, request: ProviderRequest) -> None:
        if request.normalized_role != self.role:
            raise ProviderOperationError(
                f"provider role mismatch: expected {self.role}, got {request.normalized_role}"
            )
        if request.kind != self.kind:
            raise ProviderOperationError(f"provider kind mismatch: expected {self.kind}, got {request.kind}")
        if request.operation not in self.operations:
            raise ProviderOperationError(
                f"unsupported {self.role} provider operation: {request.operation}"
            )


class IssueProvider(ProviderTransport):
    """Issue provider interface.

    Covered operations: create, update, get, search, comments, logs,
    add_comment, set_parent, set_dependency, close, and reopen.
    """

    role = ROLE_ISSUE
    operations = ISSUE_PROVIDER_OPERATIONS

    def create(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("issue create is not implemented")

    def update(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("issue update is not implemented")

    def get(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("issue get is not implemented")

    def search(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("issue search is not implemented")

    def comments(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("issue comments is not implemented")

    def logs(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("issue logs is not implemented")

    def add_comment(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("issue add_comment is not implemented")

    def set_parent(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("issue set_parent is not implemented")

    def set_dependency(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("issue set_dependency is not implemented")

    def close(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("issue close is not implemented")

    def reopen(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("issue reopen is not implemented")


class KnowledgeProvider(ProviderTransport):
    """Knowledge provider interface.

    Covered operations: create, update, get, search, metadata, links,
    comments, set_metadata, link, and add_comment.
    """

    role = ROLE_KNOWLEDGE
    operations = KNOWLEDGE_PROVIDER_OPERATIONS

    def create(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("knowledge create is not implemented")

    def update(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("knowledge update is not implemented")

    def get(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("knowledge get is not implemented")

    def search(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("knowledge search is not implemented")

    def metadata(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("knowledge metadata is not implemented")

    def links(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("knowledge links is not implemented")

    def comments(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("knowledge comments is not implemented")

    def set_metadata(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("knowledge set_metadata is not implemented")

    def link(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("knowledge link is not implemented")

    def add_comment(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("knowledge add_comment is not implemented")


class GitHubIssueNativeProvider(IssueProvider):
    """Native GitHub Issues provider backed by ``workflow_github.py``."""

    def __init__(self, *, runner: CommandRunner | None = None):
        super().__init__(kind="github", transport=TRANSPORT_NATIVE)
        self.runner = runner

    def get(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue = _required_payload_value(request, "issue")
        include_body = bool(request.payload.get("include_body", True))
        include_comments = bool(request.payload.get("include_comments", True))
        include_relationships = bool(request.payload.get("include_relationships", True))
        repo = resolve_github_repository(request.context.project, runner=self.runner)
        cache = GitHubIssueCache.for_project(request.context.project, configured_repo=repo)

        if request.context.cache_policy == CACHE_POLICY_DEFAULT:
            try:
                return cache.read_issue(
                    repo,
                    issue,
                    include_body=include_body,
                    include_comments=include_comments,
                    include_relationships=include_relationships,
                )
            except WorkflowCacheError:
                pass

        raw_fields = request.payload.get("fields")
        fields = DEFAULT_ISSUE_FIELDS
        if isinstance(raw_fields, (list, tuple)):
            fields = tuple(str(field) for field in raw_fields)
        payload = view_issue(issue, project=request.context.project, fields=fields, runner=self.runner)
        if request.context.cache_policy != CACHE_POLICY_BYPASS:
            cache.write_issue_bundle(repo, payload)
        return payload

    def create(self, request: ProviderRequest) -> Mapping[str, Any]:
        repo = resolve_github_repository(request.context.project, runner=self.runner)
        cache = GitHubIssueCache.for_project(request.context.project, configured_repo=repo)
        pending_local_id = _optional_string(
            request.payload.get("pending_local_id") or request.payload.get("local_id")
        )

        if pending_local_id:
            draft = cache.read_pending_issue_draft(repo, pending_local_id)
            title = draft.title
            body = draft.body
            labels = draft.labels
            state = draft.state
            state_reason = draft.state_reason
        else:
            title = str(_required_payload_value(request, "title"))
            body = str(_required_payload_value(request, "body"))
            labels = tuple(_string_list(request.payload.get("labels")))
            state = str(request.payload.get("state") or "open")
            state_reason = _optional_string(request.payload.get("state_reason") or request.payload.get("stateReason"))

        created = create_issue(
            title=title,
            body=body,
            labels=labels,
            state=state,
            state_reason=state_reason,
            project=request.context.project,
            guard=_already_guarded,
            runner=self.runner,
        )
        issue_number = normalize_issue_number(created["issue"])
        refreshed = view_issue(issue_number, project=request.context.project, runner=self.runner)
        write_result = cache.write_issue_bundle(repo, refreshed)

        pending_result: dict[str, str | None] | None = None
        if pending_local_id:
            pending_result = cache.finalize_pending_issue_creation(repo, pending_local_id, issue_number)

        return {
            **created,
            "cache_refreshed": True,
            "cache": write_result.to_json(),
            "pending_local_id": pending_local_id,
            "pending_finalized": pending_result is not None,
            "pending": pending_result,
        }

    def update(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue = _required_payload_value(request, "issue")
        body = _required_payload_value(request, "body")
        self._require_write_freshness(request, issue, default_target="issue")
        return edit_issue_body(
            issue,
            body=str(body),
            project=request.context.project,
            guard=_already_guarded,
            runner=self.runner,
        )

    def add_comment(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue = _required_payload_value(request, "issue")
        body = _required_payload_value(request, "body")
        self._require_write_freshness(request, issue, default_target="comments")
        return comment_issue(
            issue,
            body=str(body),
            project=request.context.project,
            guard=_already_guarded,
            runner=self.runner,
        )

    def close(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue = _required_payload_value(request, "issue")
        reason = str(request.payload.get("reason") or "completed")
        comment = request.payload.get("comment")
        self._require_write_freshness(request, issue, default_target="issue")
        return close_issue(
            issue,
            project=request.context.project,
            reason=reason,
            comment=str(comment) if comment is not None else None,
            guard=_already_guarded,
            runner=self.runner,
        )

    def reopen(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue = _required_payload_value(request, "issue")
        comment = request.payload.get("comment")
        self._require_write_freshness(request, issue, default_target="issue")
        return reopen_issue(
            issue,
            project=request.context.project,
            comment=str(comment) if comment is not None else None,
            guard=_already_guarded,
            runner=self.runner,
        )

    def logs(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue = _required_payload_value(request, "issue")
        include = request.payload.get("include") or ("timeline", "events", "body_edits")
        if isinstance(include, str):
            include = (include,)
        if not isinstance(include, (list, tuple)):
            raise ProviderOperationError("logs include must be a string or list")

        payload: dict[str, Any] = {}
        for item in include:
            normalized = str(item).replace("-", "_")
            if normalized == "timeline":
                payload["timeline"] = issue_timeline(
                    issue,
                    project=request.context.project,
                    runner=self.runner,
                )
            elif normalized == "events":
                payload["events"] = issue_events(
                    issue,
                    project=request.context.project,
                    runner=self.runner,
                )
            elif normalized in {"body_edits", "body_edit_history"}:
                payload["body_edit_history"] = issue_body_edit_history(
                    issue,
                    project=request.context.project,
                    runner=self.runner,
                )
            else:
                raise ProviderOperationError(f"unsupported GitHub issue log stream: {item}")
        return payload

    def comments(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue = self.get(request)
        return {"comments": issue.get("comments", [])}

    def _require_write_freshness(
        self,
        request: ProviderRequest,
        issue: Any,
        *,
        default_target: str,
    ) -> None:
        spec = _freshness_spec(request.payload, default_target=default_target)
        if spec is None:
            return

        issue_number = normalize_issue_number(issue)
        artifact = f"GitHub issue #{issue_number} {spec['target']}"
        if spec["pending_new"]:
            require_provider_freshness(
                None,
                provider_updated_at=None,
                artifact=artifact,
                pending_new=True,
            )
            return

        repo = resolve_github_repository(request.context.project, runner=self.runner)
        cache = GitHubIssueCache.for_project(request.context.project, configured_repo=repo)
        metadata: FreshnessMetadata | None
        try:
            metadata = cache.read_freshness_metadata(repo, issue_number, target=spec["target"])
        except WorkflowCacheError:
            metadata = FreshnessMetadata(
                source_updated_at=None,
                fetched_at=None,
                path=cache.freshness_file(repo, issue_number, spec["target"]),
                target=spec["target"],
            )

        provider_updated_at = self._provider_freshness_timestamp(
            issue_number,
            request=request,
            target=spec["target"],
        )
        try:
            require_provider_freshness(
                metadata,
                provider_updated_at=provider_updated_at,
                artifact=artifact,
            )
        except WorkflowFreshnessConflict as exc:
            raise ProviderFreshnessError(str(exc)) from exc

    def _provider_freshness_timestamp(
        self,
        issue: str,
        *,
        request: ProviderRequest,
        target: str,
    ) -> str | None:
        fields = ("number", "updatedAt")
        if target == "comments":
            fields = ("number", "updatedAt", "comments")

        payload = view_issue(
            issue,
            project=request.context.project,
            fields=fields,
            runner=self.runner,
        )
        if target == "comments":
            return _latest_provider_comment_timestamp(payload.get("comments")) or _optional_string(
                payload.get("updatedAt")
            )
        return _optional_string(payload.get("updatedAt"))


class ProviderRegistry:
    """Registry of provider transports keyed by role, kind, and transport."""

    def __init__(self) -> None:
        self._providers: dict[tuple[str, str, str], ProviderTransport] = {}

    def register(self, provider: ProviderTransport) -> None:
        key = (provider.role, provider.kind, provider.transport)
        self._providers[key] = provider

    def resolve(
        self,
        *,
        role: str,
        kind: str,
        transport: str | None = None,
    ) -> ProviderTransport:
        normalized_role = normalize_role(role)
        transports = (transport,) if transport else TRANSPORT_PRIORITY
        for candidate_transport in transports:
            provider = self._providers.get((normalized_role, kind, candidate_transport))
            if provider is not None:
                return provider
        priority = ", ".join(transports)
        raise ProviderNotFoundError(
            f"no provider registered for role={normalized_role}, kind={kind}, transport={priority}"
        )


class ProviderDispatcher:
    """Dispatch provider operations through the registered transport layer."""

    def __init__(
        self,
        registry: ProviderRegistry,
        *,
        guard: GuardCallback | None = None,
    ):
        self.registry = registry
        self.guard = guard

    def dispatch(self, request: ProviderRequest) -> ProviderResponse:
        provider = self.registry.resolve(
            role=request.role,
            kind=request.kind,
            transport=request.transport,
        )
        dispatched_request = request.with_transport(provider.transport)
        if dispatched_request.is_write:
            self._guard_write(dispatched_request)
        return provider.call(dispatched_request)

    def _guard_write(self, request: ProviderRequest) -> None:
        if self.guard is None:
            raise ProviderGuardError("provider write requires an authoring guard")
        self.guard(request)


def default_provider_registry(*, runner: CommandRunner | None = None) -> ProviderRegistry:
    """Build the default provider registry.

    Implemented native transports are registered here. MCP fallback transports
    are intentionally resolved through the same registry once MCP adapters are
    available.
    """

    registry = ProviderRegistry()
    registry.register(GitHubIssueNativeProvider(runner=runner))
    return registry


def request_from_config(
    config: WorkflowConfig,
    *,
    role: str,
    operation: str,
    artifact_type: str,
    payload: Mapping[str, Any] | None = None,
    session_id: str | None = None,
    state_dir: Path | None = None,
    transport: str | None = None,
    cache_policy: str = CACHE_POLICY_DEFAULT,
) -> ProviderRequest:
    """Build a provider request from a loaded workflow config."""

    normalized_role = normalize_role(role)
    provider_config = _provider_config_for_role(config, normalized_role)
    return ProviderRequest(
        role=normalized_role,
        kind=provider_config.kind,
        operation=operation,
        context=ProviderContext(
            project=config.root,
            artifact_type=artifact_type,
            session_id=session_id,
            state_dir=state_dir,
            cache_policy=cache_policy,
        ),
        payload=payload or {},
        transport=transport,
    )


def authoring_guard_callback() -> GuardCallback:
    """Return a guard callback that enforces the authoring read ledger."""

    def guard(request: ProviderRequest) -> None:
        session_id = request.context.session_id
        if not session_id:
            raise ProviderGuardError("provider write requires a session id for authoring guard")
        try:
            result = evaluate_authoring_guard(
                request.context.artifact_type,
                project=request.context.project,
                session_id=session_id,
                role=request.normalized_role,
                provider=request.kind,
                state_dir=request.context.state_dir,
                require_config=True,
            )
        except (ResolverError, LedgerError) as exc:
            raise ProviderGuardError(f"authoring guard failed: {exc}") from exc

        if result["ok"]:
            return

        missing = "\n".join(f"- {path}" for path in result["missing_authoring_files"])
        raise ProviderGuardError(
            "provider write blocked because required authoring files have not been read.\n"
            f"{missing}"
        )

    return guard


def _provider_config_for_role(config: WorkflowConfig, role: str) -> ProviderConfig:
    if role == ROLE_ISSUE:
        return config.issues
    if role == ROLE_KNOWLEDGE:
        return config.knowledge
    raise ProviderOperationError(f"unsupported provider role: {role}")


def _required_payload_value(request: ProviderRequest, key: str) -> Any:
    value = request.payload.get(key)
    if value is None or value == "":
        raise ProviderOperationError(f"{request.operation} requires payload.{key}")
    return value


def _freshness_spec(payload: Mapping[str, Any], *, default_target: str) -> dict[str, Any] | None:
    raw = payload.get("freshness_check")
    if raw is None:
        raw = payload.get("check_freshness")
    if raw is None:
        raw = payload.get("freshness")
    if raw is None or raw is False:
        return None

    enabled = True
    target: Any = payload.get("freshness_target") or payload.get("freshness_scope") or default_target
    pending_new = _truthy(payload.get("pending_new")) or _truthy(payload.get("pending_new_artifact"))
    pending_new = pending_new or payload.get("provider_artifact_exists") is False

    if isinstance(raw, Mapping):
        if raw.get("enabled") is not None:
            enabled = _truthy(raw.get("enabled"))
        target = raw.get("target") or raw.get("scope") or target
        pending_new = (
            pending_new
            or _truthy(raw.get("pending_new"))
            or _truthy(raw.get("pending_new_artifact"))
            or raw.get("provider_artifact_exists") is False
        )
    elif isinstance(raw, str):
        normalized_raw = raw.strip().lower()
        if normalized_raw in {"0", "false", "no", "off"}:
            return None
        if normalized_raw not in {"1", "true", "yes", "on"}:
            target = raw

    if not enabled:
        return None

    normalized_target = _normalize_freshness_target(str(target))
    if normalized_target not in {"issue", "comments", "relationships"}:
        raise ProviderOperationError(f"unsupported freshness target: {target}")
    return {"target": normalized_target, "pending_new": pending_new}


def _normalize_freshness_target(target: str) -> str:
    normalized = target.strip().lower().replace("-", "_")
    aliases = {
        "body": "issue",
        "issue_body": "issue",
        "comment": "comments",
        "issue_comments": "comments",
        "relationship": "relationships",
        "issue_relationships": "relationships",
    }
    return aliases.get(normalized, normalized)


def _latest_provider_comment_timestamp(value: Any) -> str | None:
    comments = value
    if isinstance(comments, Mapping):
        nodes = comments.get("nodes")
        if isinstance(nodes, list):
            comments = nodes
    if not isinstance(comments, list):
        return None

    values = [
        str(timestamp)
        for comment in comments
        if isinstance(comment, Mapping)
        for timestamp in (
            comment.get("updatedAt"),
            comment.get("updated_at"),
            comment.get("createdAt"),
            comment.get("created_at"),
        )
        if timestamp
    ]
    if not values:
        return None
    return max(values)


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, Mapping):
        nodes = value.get("nodes")
        if nodes is not None:
            return _string_list(nodes)
        name = value.get("name")
        return [str(name)] if name else []
    if isinstance(value, list | tuple | set):
        labels: list[str] = []
        for item in value:
            labels.extend(_string_list(item))
        return labels
    return [str(value)]


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _already_guarded(_operation: str, _payload: Mapping[str, Any]) -> None:
    """No-op guard used after ``ProviderDispatcher`` has checked a write."""

    return None
