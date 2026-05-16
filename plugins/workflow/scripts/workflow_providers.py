#!/usr/bin/env python3
"""Provider interface scaffold for workflow issue and knowledge operations.

The provider layer owns dispatch across provider kinds and transports. Native
wrappers are preferred first, and MCP providers are fallback transports.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from workflow_command import CommandRunner
from workflow_cache import (
    FreshnessMetadata,
    GitHubIssueCache,
    PendingIssueRelationshipOperation,
    WorkflowCacheError,
    WorkflowFreshnessConflict,
    require_provider_freshness,
)
from workflow_config import ProviderConfig, WorkflowConfig, WorkflowConfigError, load_workflow_config, normalize_role
from workflow_github import (
    DEFAULT_ISSUE_FIELDS,
    add_issue_dependency,
    add_sub_issue,
    close_issue,
    comment_issue,
    create_issue,
    edit_issue,
    issue_relationships,
    issue_body_edit_history,
    issue_events,
    issue_timeline,
    normalize_issue_number,
    remove_issue_dependency,
    remove_sub_issue,
    reopen_issue,
    resolve_github_repository,
    view_issue,
)
from workflow_refs import ProviderReferenceError, normalize_provider_reference

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
        "apply_relationships",
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



@dataclass(frozen=True)
class _ResolvedRelationshipOperation:
    action: str
    relationship: str
    target_issue: str
    replace_parent: bool = False

    def to_json(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "relationship": self.relationship,
            "target_issue": self.target_issue,
            "replace_parent": self.replace_parent,
        }


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

    def apply_relationships(self, request: ProviderRequest) -> Mapping[str, Any]:
        raise ProviderOperationError("issue apply_relationships is not implemented")

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
            payload_for_cache = self._payload_with_relationship_projection(
                request,
                issue=issue,
                payload=payload,
            )
            cache.write_issue_bundle(repo, payload_for_cache)
        return payload

    def _payload_with_relationship_projection(
        self,
        request: ProviderRequest,
        *,
        issue: Any,
        payload: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Add provider-native relationships before writing relationship frontmatter.

        `gh issue view` does not expose the issue relationship REST resources
        that back the relationship projection. Cache writes therefore need an
        explicit relationship read even when the caller does not ask to return
        relationships in the provider response.
        """

        if _payload_has_relationship_projection(payload):
            return payload
        relationships = issue_relationships(
            issue,
            project=request.context.project,
            runner=self.runner,
        )
        return {**payload, **relationships}

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
            runner=self.runner,
        )
        issue_number = normalize_issue_number(created["issue"])
        refreshed = view_issue(issue_number, project=request.context.project, runner=self.runner)
        write_result = cache.write_issue_bundle(
            repo,
            self._payload_with_relationship_projection(
                request,
                issue=issue_number,
                payload=refreshed,
            ),
        )

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
        if _truthy(request.payload.get("from_cache")) or _truthy(request.payload.get("cache_write_back")):
            return self._update_from_cache(request, issue)

        title = request.payload.get("title")
        body = request.payload.get("body")
        labels = request.payload.get("labels")
        if title is None and body is None and labels is None:
            raise ProviderOperationError("GitHub issue update requires from_cache or at least one of title, body, labels")
        self._require_write_freshness(request, issue, default_target="issue")
        issue_number = normalize_issue_number(issue)
        repo = resolve_github_repository(request.context.project, runner=self.runner)
        cache = GitHubIssueCache.for_project(request.context.project, configured_repo=repo)
        current_labels: tuple[str, ...] | None = None
        if labels is not None:
            current = view_issue(
                issue_number,
                project=request.context.project,
                fields=("number", "labels"),
                runner=self.runner,
            )
            current_labels = tuple(_string_list(current.get("labels")))
        edited = edit_issue(
            issue_number,
            title=str(title) if title is not None else None,
            body=str(body) if body is not None else None,
            labels=tuple(_string_list(labels)) if labels is not None else None,
            current_labels=current_labels,
            project=request.context.project,
            runner=self.runner,
        )
        refreshed = view_issue(issue_number, project=request.context.project, runner=self.runner)
        write_result = cache.write_issue_bundle(
            repo,
            self._payload_with_relationship_projection(
                request,
                issue=issue_number,
                payload=refreshed,
            ),
        )
        return {
            "operation": "update_issue",
            "issue": issue_number,
            "verified": bool(edited.get("verified")),
            "edit": dict(edited),
            "cache_refreshed": True,
            "cache": write_result.to_json(),
        }

    def _update_from_cache(self, request: ProviderRequest, issue: Any) -> Mapping[str, Any]:
        issue_number = normalize_issue_number(issue)
        repo = resolve_github_repository(request.context.project, runner=self.runner)
        cache = GitHubIssueCache.for_project(request.context.project, configured_repo=repo)
        projection = cache.read_issue(
            repo,
            issue_number,
            include_body=True,
            include_comments=False,
            include_relationships=False,
        )
        provider_current = self._require_cached_issue_write_freshness(request, repo, cache, issue_number)
        current_labels = tuple(_string_list(provider_current.get("labels")))

        edited = edit_issue(
            issue_number,
            title=str(projection.get("title") or ""),
            body=str(projection.get("body") or ""),
            labels=tuple(_string_list(projection.get("labels"))),
            current_labels=current_labels,
            project=request.context.project,
            runner=self.runner,
        )

        state_result: Mapping[str, Any] | None = None
        desired_state = str(projection.get("state") or "").upper()
        current_state = str(provider_current.get("state") or "").upper()
        if desired_state == "CLOSED" and current_state != "CLOSED":
            state_result = close_issue(
                issue_number,
                project=request.context.project,
                reason=_close_reason_from_state_reason(projection.get("stateReason")),
                runner=self.runner,
            )
        elif desired_state == "OPEN" and current_state != "OPEN":
            state_result = reopen_issue(
                issue_number,
                project=request.context.project,
                runner=self.runner,
            )

        refreshed = view_issue(issue_number, project=request.context.project, runner=self.runner)
        write_result = cache.write_issue_bundle(
            repo,
            self._payload_with_relationship_projection(
                request,
                issue=issue_number,
                payload=refreshed,
            ),
        )
        return {
            "operation": "update_issue_from_cache",
            "issue": issue_number,
            "verified": bool(edited.get("verified")) and (state_result is None or bool(state_result.get("verified"))),
            "edit": dict(edited),
            "state": dict(state_result) if state_result is not None else None,
            "cache_refreshed": True,
            "cache": write_result.to_json(),
        }

    def add_comment(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue = _required_payload_value(request, "issue")
        if _truthy(request.payload.get("from_pending")) or _truthy(request.payload.get("pending_comments")):
            return self._add_pending_comments(request, issue)

        body = _required_payload_value(request, "body")
        self._require_write_freshness(request, issue, default_target="comments")
        return comment_issue(
            issue,
            body=str(body),
            project=request.context.project,
            runner=self.runner,
        )

    def _add_pending_comments(self, request: ProviderRequest, issue: Any) -> Mapping[str, Any]:
        issue_number = normalize_issue_number(issue)
        repo = resolve_github_repository(request.context.project, runner=self.runner)
        cache = GitHubIssueCache.for_project(request.context.project, configured_repo=repo)
        pending_local_id = _optional_string(
            request.payload.get("pending_local_id") or request.payload.get("local_id")
        )
        if pending_local_id:
            pending_comments = cache.read_pending_draft_comments(repo, pending_local_id)
            pending_source = "pending_issue"
        else:
            pending_comments = cache.read_pending_issue_comments(repo, issue_number)
            pending_source = "issue"

        if not pending_comments:
            if pending_local_id:
                raise ProviderOperationError(
                    f"no pending comment files found for GitHub pending issue {pending_local_id}"
                )
            raise ProviderOperationError(f"no pending comment files found for GitHub issue #{issue_number}")

        self._require_write_freshness(request, issue_number, default_target="comments")
        appended = [
            comment_issue(
                issue_number,
                body=pending.body,
                project=request.context.project,
                runner=self.runner,
            )
            for pending in pending_comments
        ]
        refreshed = view_issue(issue_number, project=request.context.project, runner=self.runner)
        write_result = cache.write_issue_bundle(repo, refreshed)
        if pending_local_id:
            removed = cache.remove_pending_draft_comments(repo, pending_local_id, pending_comments)
        else:
            removed = cache.remove_pending_issue_comments(repo, issue_number, pending_comments)

        return {
            "operation": "append_pending_comments",
            "issue": issue_number,
            "appended": len(appended),
            "pending_source": pending_source,
            "pending_files": [pending.file_name for pending in pending_comments],
            "removed_pending_files": [str(path) for path in removed],
            "cache_refreshed": True,
            "cache": write_result.to_json(),
        }

    def apply_relationships(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue = _required_payload_value(request, "issue")
        if _truthy(request.payload.get("from_pending")) or _truthy(request.payload.get("pending_relationships")):
            return self._apply_pending_relationships(request, issue)
        raise ProviderOperationError("GitHub issue apply_relationships currently requires pending_relationships")

    def set_parent(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue = normalize_issue_number(_required_payload_value(request, "issue"))
        parent = _required_payload_value(request, "parent")
        action = _relationship_action(request.payload.get("action") or request.payload.get("op") or "add")
        operations = [
            _ResolvedRelationshipOperation(
                action=action,
                relationship="parent",
                target_issue=self._resolve_github_issue_reference(request, parent),
                replace_parent=_truthy(request.payload.get("replace_parent") or request.payload.get("replaceParent")),
            )
        ]
        return self._apply_relationship_operations(request, issue, operations, pending_operations=None)

    def set_dependency(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue = normalize_issue_number(_required_payload_value(request, "issue"))
        operations: list[_ResolvedRelationshipOperation] = []
        for key, relationship in (("blocked_by", "blocked_by"), ("blockedBy", "blocked_by"), ("blocking", "blocking"), ("blocks", "blocking")):
            if key not in request.payload:
                continue
            for value in _relationship_values(request.payload[key]):
                operations.append(
                    _ResolvedRelationshipOperation(
                        action=_relationship_action(request.payload.get("action") or request.payload.get("op") or "add"),
                        relationship=relationship,
                        target_issue=self._resolve_github_issue_reference(request, value),
                    )
                )
        if not operations:
            target = _required_payload_value(request, "dependency")
            operations.append(
                _ResolvedRelationshipOperation(
                    action=_relationship_action(request.payload.get("action") or request.payload.get("op") or "add"),
                    relationship="blocked_by",
                    target_issue=self._resolve_github_issue_reference(request, target),
                )
            )
        return self._apply_relationship_operations(request, issue, operations, pending_operations=None)

    def _apply_pending_relationships(self, request: ProviderRequest, issue: Any) -> Mapping[str, Any]:
        issue_number = normalize_issue_number(issue)
        repo = resolve_github_repository(request.context.project, runner=self.runner)
        cache = GitHubIssueCache.for_project(request.context.project, configured_repo=repo)
        pending_local_id = _optional_string(
            request.payload.get("pending_local_id") or request.payload.get("local_id")
        )
        if pending_local_id:
            pending_operations = cache.read_pending_draft_relationships(repo, pending_local_id)
            pending_source = "pending_issue"
        else:
            pending_operations = cache.read_pending_issue_relationships(repo, issue_number)
            pending_source = "issue"

        if not pending_operations:
            if pending_local_id:
                raise ProviderOperationError(
                    f"no pending relationship frontmatter found for GitHub pending issue {pending_local_id}"
                )
            raise ProviderOperationError(f"no pending relationship frontmatter found for GitHub issue #{issue_number}")

        operations = [
            _ResolvedRelationshipOperation(
                action=operation.action,
                relationship=operation.relationship,
                target_issue=self._resolve_github_issue_reference(request, operation.target_ref),
                replace_parent=operation.replace_parent,
            )
            for operation in pending_operations
        ]
        if not operations:
            raise ProviderOperationError(f"no GitHub relationship operations found for issue #{issue_number}")
        self._validate_relationship_operations(operations)
        freshness_payload = dict(request.payload)
        freshness_payload.setdefault("freshness_check", True)
        freshness_payload.setdefault("freshness_target", "relationships")
        self._require_write_freshness(
            replace(request, payload=freshness_payload),
            issue_number,
            default_target="relationships",
        )

        applied: list[Mapping[str, Any]] = []
        consumed_pending: list[PendingIssueRelationshipOperation] = []
        consumed_resolved: list[_ResolvedRelationshipOperation] = []
        try:
            for resolved, pending in zip(operations, pending_operations):
                applied.append(self._dispatch_relationship_operation(issue_number, resolved, request=request))
                consumed_pending.append(pending)
                consumed_resolved.append(resolved)
        except Exception as exc:
            removed = self._remove_consumed_pending_relationships(
                cache,
                repo,
                issue_number,
                pending_local_id=pending_local_id,
                consumed_pending=consumed_pending,
            )
            refresh_error: str | None = None
            relationship_location: Path | None = None
            try:
                relationship_location = self._refresh_relationship_projection(request, issue_number)
            except Exception as refresh_exc:  # pragma: no cover - defensive reporting path
                refresh_error = str(refresh_exc)
            details = (
                f"GitHub relationship apply failed after {len(applied)} provider operation(s); "
                "provider state may have partially changed. Refresh relationships and re-stage before retry."
            )
            if refresh_error:
                details += f" Relationship refresh also failed: {refresh_error}"
            raise ProviderOperationError(details) from exc

        relationship_location = self._refresh_relationship_projection(request, issue_number)
        removed = self._remove_consumed_pending_relationships(
            cache,
            repo,
            issue_number,
            pending_local_id=pending_local_id,
            consumed_pending=consumed_pending,
        )
        return {
            "operation": "apply_relationships",
            "issue": issue_number,
            "applied": len(applied),
            "operations": [operation.to_json() for operation in operations],
            "provider_results": [dict(item) for item in applied],
            "pending_operations": [operation.to_json() for operation in pending_operations],
            "consumed_operations": [operation.to_json() for operation in consumed_resolved],
            "cache_refreshed": True,
            "relationship_location": str(relationship_location),
            "pending_source": pending_source,
            "pending_file": pending_operations[0].file_name,
            "removed_pending_files": [str(path) for path in removed],
        }

    def _remove_consumed_pending_relationships(
        self,
        cache: GitHubIssueCache,
        repo: Any,
        issue_number: str,
        *,
        pending_local_id: str | None,
        consumed_pending: list[PendingIssueRelationshipOperation],
    ) -> list[Path]:
        if not consumed_pending:
            return []
        if pending_local_id:
            return cache.remove_pending_draft_relationships(repo, pending_local_id, consumed_pending)
        return cache.remove_pending_issue_relationships(repo, issue_number, consumed_pending)

    def _apply_relationship_operations(
        self,
        request: ProviderRequest,
        issue_number: str,
        operations: list[_ResolvedRelationshipOperation],
        *,
        pending_operations: list[PendingIssueRelationshipOperation] | None,
    ) -> dict[str, Any]:
        if not operations:
            raise ProviderOperationError(f"no GitHub relationship operations found for issue #{issue_number}")
        self._validate_relationship_operations(operations)
        freshness_payload = dict(request.payload)
        freshness_payload.setdefault("freshness_check", True)
        freshness_payload.setdefault("freshness_target", "relationships")
        self._require_write_freshness(
            replace(request, payload=freshness_payload),
            issue_number,
            default_target="relationships",
        )

        applied: list[Mapping[str, Any]] = []
        for operation in operations:
            applied.append(self._dispatch_relationship_operation(issue_number, operation, request=request))

        relationship_location = self._refresh_relationship_projection(request, issue_number)
        return {
            "operation": "apply_relationships",
            "issue": issue_number,
            "applied": len(applied),
            "operations": [operation.to_json() for operation in operations],
            "provider_results": [dict(item) for item in applied],
            "pending_operations": [operation.to_json() for operation in pending_operations or []],
            "cache_refreshed": True,
            "relationship_location": str(relationship_location),
        }

    def _refresh_relationship_projection(self, request: ProviderRequest, issue_number: str) -> Path:
        repo = resolve_github_repository(request.context.project, runner=self.runner)
        cache = GitHubIssueCache.for_project(request.context.project, configured_repo=repo)
        relationships = issue_relationships(
            issue_number,
            project=request.context.project,
            runner=self.runner,
        )
        return cache.write_relationships_projection(repo, issue_number, relationships)

    def _validate_relationship_operations(self, operations: list[_ResolvedRelationshipOperation]) -> None:
        supported = {"parent", "child", "blocked_by", "blocking"}
        for operation in operations:
            if operation.relationship not in supported:
                raise ProviderOperationError(
                    f"unsupported GitHub relationship operation: {operation.relationship}"
                )
            if operation.action not in {"add", "remove"}:
                raise ProviderOperationError(
                    f"unsupported GitHub relationship action: {operation.action}"
                )

    def _dispatch_relationship_operation(
        self,
        issue_number: str,
        operation: _ResolvedRelationshipOperation,
        *,
        request: ProviderRequest,
    ) -> Mapping[str, Any]:
        if operation.relationship == "parent":
            if operation.action == "add":
                return add_sub_issue(
                    operation.target_issue,
                    issue_number,
                    project=request.context.project,
                            replace_parent=operation.replace_parent,
                    runner=self.runner,
                )
            return remove_sub_issue(
                operation.target_issue,
                issue_number,
                project=request.context.project,
                runner=self.runner,
            )

        if operation.relationship == "child":
            if operation.action == "add":
                return add_sub_issue(
                    issue_number,
                    operation.target_issue,
                    project=request.context.project,
                            replace_parent=operation.replace_parent,
                    runner=self.runner,
                )
            return remove_sub_issue(
                issue_number,
                operation.target_issue,
                project=request.context.project,
                runner=self.runner,
            )

        if operation.relationship == "blocked_by":
            if operation.action == "add":
                return add_issue_dependency(
                    issue_number,
                    operation.target_issue,
                    project=request.context.project,
                            runner=self.runner,
                )
            return remove_issue_dependency(
                issue_number,
                operation.target_issue,
                project=request.context.project,
                runner=self.runner,
            )

        if operation.relationship == "blocking":
            if operation.action == "add":
                return add_issue_dependency(
                    operation.target_issue,
                    issue_number,
                    project=request.context.project,
                            runner=self.runner,
                )
            return remove_issue_dependency(
                operation.target_issue,
                issue_number,
                project=request.context.project,
                runner=self.runner,
            )

        raise ProviderOperationError(f"unsupported GitHub relationship operation: {operation.relationship}")

    def _resolve_github_issue_reference(self, request: ProviderRequest, value: Any) -> str:
        raw = str(value).strip()
        if not raw:
            raise ProviderOperationError("GitHub relationship target issue reference is empty")
        config = _optional_workflow_config(request.context.project)
        if config is None:
            return normalize_issue_number(raw)
        try:
            ref = normalize_provider_reference(
                raw,
                config,
                role="issue",
                allow_bare_issue_number=True,
                runner=self.runner,
            )
        except ProviderReferenceError as exc:
            raise ProviderOperationError(str(exc)) from exc
        repo = resolve_github_repository(request.context.project, runner=self.runner)
        native = ref.native
        ref_repo = (
            str(ref.authority).lower(),
            str(native.get("owner") or "").lower(),
            str(native.get("repo") or "").lower(),
        )
        current_repo = (repo.host.lower(), repo.owner.lower(), repo.name.lower())
        if ref.provider != "github" or ref.kind != "issue" or ref_repo != current_repo:
            raise ProviderOperationError(
                f"GitHub relationship target must be in the configured repository: {raw}"
            )
        return normalize_issue_number(native.get("number") or "")

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

    def _require_cached_issue_write_freshness(
        self,
        request: ProviderRequest,
        repo: GitHubRepository,
        cache: GitHubIssueCache,
        issue_number: str,
    ) -> Mapping[str, Any]:
        artifact = f"GitHub issue #{issue_number} issue"
        try:
            metadata = cache.read_freshness_metadata(repo, issue_number, target="issue")
        except WorkflowCacheError:
            metadata = FreshnessMetadata(
                source_updated_at=None,
                fetched_at=None,
                path=cache.freshness_file(repo, issue_number, "issue"),
                target="issue",
            )

        provider_current = view_issue(
            issue_number,
            project=request.context.project,
            fields=("number", "updatedAt", "labels", "state", "stateReason"),
            runner=self.runner,
        )
        try:
            require_provider_freshness(
                metadata,
                provider_updated_at=_optional_string(provider_current.get("updatedAt")),
                artifact=artifact,
            )
        except WorkflowFreshnessConflict as exc:
            raise ProviderFreshnessError(str(exc)) from exc
        return provider_current

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

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    def dispatch(self, request: ProviderRequest) -> ProviderResponse:
        provider = self.registry.resolve(
            role=request.role,
            kind=request.kind,
            transport=request.transport,
        )
        dispatched_request = request.with_transport(provider.transport)
        return provider.call(dispatched_request)


def default_provider_registry(*, runner: CommandRunner | None = None) -> ProviderRegistry:
    """Build the default provider registry.

    Implemented native transports are registered here. MCP fallback transports
    are intentionally resolved through the same registry once MCP adapters are
    available.
    """

    registry = ProviderRegistry()
    registry.register(GitHubIssueNativeProvider(runner=runner))
    from workflow_jira_data_center import JiraDataCenterIssueNativeProvider

    registry.register(JiraDataCenterIssueNativeProvider(runner=runner))
    return registry


def request_from_config(
    config: WorkflowConfig,
    *,
    role: str,
    operation: str,
    artifact_type: str,
    payload: Mapping[str, Any] | None = None,
    session_id: str | None = None,
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
            cache_policy=cache_policy,
        ),
        payload=payload or {},
        transport=transport,
    )


def _provider_config_for_role(config: WorkflowConfig, role: str) -> ProviderConfig:
    if role == ROLE_ISSUE:
        return config.issues
    if role == ROLE_KNOWLEDGE:
        return config.knowledge
    raise ProviderOperationError(f"unsupported provider role: {role}")


def _optional_workflow_config(project: Path) -> WorkflowConfig | None:
    try:
        return load_workflow_config(project)
    except WorkflowConfigError as exc:
        raise ProviderOperationError(str(exc)) from exc


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


def _payload_has_relationship_projection(payload: Mapping[str, Any]) -> bool:
    """Return true when a provider payload already carries relationship data."""

    relationship_keys = {
        "parent",
        "parentIssue",
        "parent_issue",
        "children",
        "subIssues",
        "sub_issues",
        "dependencies",
        "blocked_by",
        "blockedBy",
        "blocking",
        "blocks",
        "related",
    }
    return any(key in payload for key in relationship_keys)


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


def _close_reason_from_state_reason(value: Any) -> str:
    text = _optional_string(value)
    if text and text.strip().lower().replace("_", "-") in {"not-planned", "not planned"}:
        return "not planned"
    return "completed"


def _relationship_action(value: Any) -> str:
    normalized = str(value).strip().lower().replace("-", "_")
    aliases = {
        "set": "add",
        "create": "add",
        "append": "add",
        "delete": "remove",
        "unset": "remove",
    }
    action = aliases.get(normalized, normalized)
    if action not in {"add", "remove"}:
        raise ProviderOperationError(f"unsupported GitHub relationship action: {value}")
    return action


def _relationship_values(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, list | tuple | set):
        return list(value)
    return [value]


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
