#!/usr/bin/env python3
"""Jira Data Center native issue provider."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any
from urllib.parse import urlparse

from workflow_cache import (
    FreshnessMetadata,
    PendingIssueRelationshipOperation,
    WorkflowCacheError,
    WorkflowFreshnessConflict,
    require_provider_freshness,
)
from workflow_command import CommandRunner
from workflow_config import WorkflowConfigError, load_workflow_config
from workflow_jira import (
    JiraDataCenterIssueCache,
    JiraProviderError,
    filter_jira_payload,
    jira_data_center_comments_path,
    jira_data_center_issue_path,
    jira_data_center_issue_link_path,
    jira_data_center_issue_links_path,
    jira_data_center_remote_link_global_id_path,
    jira_data_center_remote_link_path,
    jira_data_center_remote_links_path,
    jira_delete,
    jira_get_json,
    jira_send_json,
    normalize_jira_data_center_issue,
    normalize_jira_issue_key,
    normalize_jira_remote_links,
    resolve_jira_data_center_site,
)
from workflow_providers import (
    CACHE_POLICY_BYPASS,
    CACHE_POLICY_DEFAULT,
    TRANSPORT_NATIVE,
    IssueProvider,
    ProviderFreshnessError,
    ProviderOperationError,
    ProviderRequest,
)


JIRA_REVIEW_ISSUE_TYPE = "Task"
JIRA_REVIEW_TITLE_PREFIX = "[Review] "
JIRA_RESEARCH_TITLE_PREFIX = "[Research] "
JIRA_SPIKE_ISSUE_TYPE = "Task"
JIRA_SPIKE_TITLE_PREFIX = "[Spike] "
JIRA_ARTIFACT_ISSUE_TYPES = {
    "bug": "Bug",
    "epic": "Epic",
    "research": "Task",
    "review": JIRA_REVIEW_ISSUE_TYPE,
    "task": "Task",
    "usecase": "Story",
    "spike": JIRA_SPIKE_ISSUE_TYPE,
}


@dataclass(frozen=True)
class _JiraRelationshipMapping:
    relationship: str
    surface: str
    link_type: str | None = None
    direction: str | None = None
    field: str | None = None
    write_to: str | None = None
    value: str | None = None
    remote_relationship: str | None = None
    application_type: str | None = None
    application_name: str | None = None

    def to_json(self) -> dict[str, str]:
        result = {"relationship": self.relationship, "surface": self.surface}
        for key in (
            "link_type",
            "direction",
            "field",
            "write_to",
            "value",
            "remote_relationship",
            "application_type",
            "application_name",
        ):
            value = getattr(self, key)
            if value is not None:
                result[key] = value
        return result


@dataclass(frozen=True)
class _ResolvedJiraRelationshipOperation:
    action: str
    relationship: str
    target_ref: str
    mapping: _JiraRelationshipMapping
    target_issue: str | None = None
    link_id: str | None = None
    remote_url: str | None = None
    remote_title: str | None = None
    remote_global_id: str | None = None
    field_issue: str | None = None
    field_value: Any = None

    def to_json(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "action": self.action,
            "relationship": self.relationship,
            "target_ref": self.target_ref,
            "mapping": self.mapping.to_json(),
        }
        for key in (
            "target_issue",
            "link_id",
            "remote_url",
            "remote_title",
            "remote_global_id",
            "field_issue",
        ):
            value = getattr(self, key)
            if value is not None:
                result[key] = value
        if self.field_value is not None:
            result["field_value"] = self.field_value
        return result


class JiraDataCenterIssueNativeProvider(IssueProvider):
    """Native Jira Data Center issue provider backed by REST API v2 by default."""

    def __init__(self, *, runner: CommandRunner | None = None):
        super().__init__(kind="jira", transport=TRANSPORT_NATIVE)
        self.runner = runner

    def get(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue_key = normalize_jira_issue_key(_required_payload_value(request, "issue"))
        include_body = bool(request.payload.get("include_body", True))
        include_comments = bool(request.payload.get("include_comments", True))
        include_relationships = bool(request.payload.get("include_relationships", True))
        include_remote_links = bool(request.payload.get("include_remote_links", True))

        try:
            site = resolve_jira_data_center_site(request.context.project)
            cache = JiraDataCenterIssueCache.for_project(request.context.project)
            if request.context.cache_policy == CACHE_POLICY_DEFAULT:
                try:
                    return cache.read_issue(
                        site,
                        issue_key,
                        include_body=include_body,
                        include_comments=include_comments,
                        include_relationships=include_relationships,
                    )
                except WorkflowCacheError:
                    pass

            raw_issue = get_issue(site, issue_key, runner=self.runner)
            remote_links = get_remote_links(site, issue_key, runner=self.runner) if include_remote_links else []
            payload = normalize_jira_data_center_issue(raw_issue, site=site, remote_links=remote_links)

            if request.context.cache_policy != CACHE_POLICY_BYPASS:
                cache.write_issue_bundle(site, raw_issue, remote_links=remote_links)

            return filter_jira_payload(
                payload,
                include_body=include_body,
                include_comments=include_comments,
                include_relationships=include_relationships,
            )
        except JiraProviderError as exc:
            raise ProviderOperationError(str(exc)) from exc

    def comments(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue = self.get(request)
        return {"comments": issue.get("comments", [])}

    def create(self, request: ProviderRequest) -> Mapping[str, Any]:
        site = resolve_jira_data_center_site(request.context.project)
        cache = JiraDataCenterIssueCache.for_project(request.context.project)
        pending_local_id = _optional_string(
            request.payload.get("pending_local_id") or request.payload.get("local_id")
        )

        if pending_local_id:
            draft = cache.read_pending_issue_draft(site, pending_local_id)
            title = draft.title
            body = draft.body
            labels = draft.labels
        else:
            title = str(_required_payload_value(request, "title"))
            body = str(_required_payload_value(request, "body"))
            labels = tuple(_string_list(request.payload.get("labels")))

        title = _jira_issue_title(request, title)
        project_key = _optional_string(request.payload.get("project") or request.payload.get("project_key")) or site.project
        issue_type = (
            _jira_artifact_issue_type(request)
            or _optional_string(request.payload.get("issue_type") or request.payload.get("issuetype"))
            or site.issue_type
        )
        if not project_key:
            raise ProviderOperationError("Jira issue create requires provider project or payload.project")
        if not issue_type:
            raise ProviderOperationError("Jira issue create requires provider issue_type or payload.issue_type")

        created = create_issue(
            site,
            project_key=project_key,
            issue_type=issue_type,
            title=title,
            body=body,
            labels=labels,
            runner=self.runner,
        )
        issue_key = normalize_jira_issue_key(created.get("key") or created.get("issue") or "")
        write_result = self._refresh_cache(site, cache, issue_key)
        pending_result = None
        if pending_local_id:
            pending_result = cache.finalize_pending_issue_creation(site, pending_local_id, issue_key)
        return {
            "operation": "create_issue",
            "issue": issue_key,
            "key": issue_key,
            "verified": True,
            "cache_refreshed": True,
            "cache": write_result,
            "pending_local_id": pending_local_id,
            "pending_finalized": pending_result is not None,
            "pending": pending_result,
        }

    def update(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue_key = normalize_jira_issue_key(_required_payload_value(request, "issue"))
        if _truthy(request.payload.get("from_cache")) or _truthy(request.payload.get("cache_write_back")):
            return self._update_from_cache(request, issue_key)

        fields: dict[str, Any] = {}
        if request.payload.get("title") is not None:
            title = str(request.payload["title"])
            fields["summary"] = _jira_issue_title(request, title)
        if request.payload.get("body") is not None:
            fields["description"] = str(request.payload["body"])
        if request.payload.get("labels") is not None:
            fields["labels"] = _string_list(request.payload.get("labels"))
        if not fields:
            raise ProviderOperationError("Jira issue update requires from_cache or at least one of title, body, labels")
        return self._update_fields(request, issue_key, fields, operation="update_issue")

    def _update_from_cache(self, request: ProviderRequest, issue_key: str) -> Mapping[str, Any]:
        site = resolve_jira_data_center_site(request.context.project)
        cache = JiraDataCenterIssueCache.for_project(request.context.project)
        raw_issue = cache.read_issue_json(site, issue_key)
        raw_fields = raw_issue.get("fields") if isinstance(raw_issue.get("fields"), Mapping) else {}
        assert isinstance(raw_fields, Mapping)
        fields: dict[str, Any] = {}
        if raw_fields.get("summary") is not None:
            title = str(raw_fields.get("summary") or "")
            fields["summary"] = _jira_issue_title(request, title)
        if raw_fields.get("description") is not None:
            fields["description"] = str(raw_fields.get("description") or "")
        if raw_fields.get("labels") is not None:
            fields["labels"] = _string_list(raw_fields.get("labels"))
        if not fields:
            raise ProviderOperationError(f"cached Jira issue {issue_key} has no writable fields")
        return self._update_fields(request, issue_key, fields, operation="update_issue_from_cache")

    def _update_fields(
        self,
        request: ProviderRequest,
        issue_key: str,
        fields: Mapping[str, Any],
        *,
        operation: str,
    ) -> Mapping[str, Any]:
        site = resolve_jira_data_center_site(request.context.project)
        cache = JiraDataCenterIssueCache.for_project(request.context.project)
        self._require_write_freshness(request, site, cache, issue_key, target="issue")
        update_issue(site, issue_key, fields=fields, runner=self.runner)
        write_result = self._refresh_cache(site, cache, issue_key)
        return {
            "operation": operation,
            "issue": issue_key,
            "key": issue_key,
            "verified": True,
            "cache_refreshed": True,
            "cache": write_result,
        }

    def add_comment(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue_key = normalize_jira_issue_key(_required_payload_value(request, "issue"))
        if _truthy(request.payload.get("from_pending")) or _truthy(request.payload.get("pending_comments")):
            return self._add_pending_comments(request, issue_key)

        body = str(_required_payload_value(request, "body"))
        return self._append_comment(request, issue_key, body)

    def apply_relationships(self, request: ProviderRequest) -> Mapping[str, Any]:
        issue_key = normalize_jira_issue_key(_required_payload_value(request, "issue"))
        if _truthy(request.payload.get("from_pending")) or _truthy(request.payload.get("pending_relationships")):
            return self._apply_pending_relationships(request, issue_key)
        raise ProviderOperationError("Jira issue apply_relationships currently requires pending_relationships")

    def _add_pending_comments(self, request: ProviderRequest, issue_key: str) -> Mapping[str, Any]:
        site = resolve_jira_data_center_site(request.context.project)
        cache = JiraDataCenterIssueCache.for_project(request.context.project)
        pending_comments = cache.read_pending_issue_comments(site, issue_key)
        if not pending_comments:
            raise ProviderOperationError(f"no pending comment files found for Jira issue {issue_key}")

        self._require_write_freshness(request, site, cache, issue_key, target="comments")
        appended = [add_comment(site, issue_key, body=pending.body, runner=self.runner) for pending in pending_comments]
        write_result = self._refresh_cache(site, cache, issue_key)
        removed = cache.remove_pending_issue_comments(site, issue_key, pending_comments)
        return {
            "operation": "append_pending_comments",
            "issue": issue_key,
            "key": issue_key,
            "appended": len(appended),
            "pending_source": "issue",
            "pending_files": [pending.file_name for pending in pending_comments],
            "removed_pending_files": [str(path) for path in removed],
            "cache_refreshed": True,
            "cache": write_result,
        }

    def _append_comment(self, request: ProviderRequest, issue_key: str, body: str) -> Mapping[str, Any]:
        site = resolve_jira_data_center_site(request.context.project)
        cache = JiraDataCenterIssueCache.for_project(request.context.project)
        self._require_write_freshness(request, site, cache, issue_key, target="comments")
        created = add_comment(site, issue_key, body=body, runner=self.runner)
        write_result = self._refresh_cache(site, cache, issue_key)
        return {
            "operation": "add_comment",
            "issue": issue_key,
            "key": issue_key,
            "comment": dict(created) if isinstance(created, Mapping) else {},
            "cache_refreshed": True,
            "cache": write_result,
        }

    def _apply_pending_relationships(self, request: ProviderRequest, issue_key: str) -> Mapping[str, Any]:
        site = resolve_jira_data_center_site(request.context.project)
        cache = JiraDataCenterIssueCache.for_project(request.context.project)
        pending_local_id = _optional_string(
            request.payload.get("pending_local_id") or request.payload.get("local_id")
        )
        if pending_local_id:
            pending_operations = cache.read_pending_draft_relationships(site, pending_local_id)
            pending_source = "pending_issue"
        else:
            pending_operations = cache.read_pending_issue_relationships(site, issue_key)
            pending_source = "issue"

        if not pending_operations:
            if pending_local_id:
                raise ProviderOperationError(
                    f"no pending relationship file found for Jira pending issue {pending_local_id}"
                )
            raise ProviderOperationError(f"no pending relationship file found for Jira issue {issue_key}")

        result = self._apply_relationship_operations(request, site, cache, issue_key, pending_operations)
        if pending_local_id:
            removed = cache.remove_pending_draft_relationships(site, pending_local_id, pending_operations)
        else:
            removed = cache.remove_pending_issue_relationships(site, issue_key, pending_operations)
        return {
            **result,
            "pending_source": pending_source,
            "pending_file": pending_operations[0].file_name,
            "removed_pending_files": [str(path) for path in removed],
        }

    def _apply_relationship_operations(
        self,
        request: ProviderRequest,
        site: Any,
        cache: JiraDataCenterIssueCache,
        issue_key: str,
        pending_operations: list[PendingIssueRelationshipOperation],
    ) -> Mapping[str, Any]:
        if not pending_operations:
            raise ProviderOperationError(f"no Jira relationship operations found for issue {issue_key}")

        settings = _jira_issue_provider_settings(request.context.project)
        resolved = [
            _resolve_jira_relationship_operation(issue_key, operation, settings=settings)
            for operation in pending_operations
        ]
        provider_current = self._require_write_freshness(request, site, cache, issue_key, target="relationships")
        prepared = self._prepare_relationship_removals(site, issue_key, provider_current, resolved)

        applied: list[Mapping[str, Any]] = []
        for operation in prepared:
            applied.append(self._dispatch_relationship_operation(site, operation))

        write_result = self._refresh_cache(site, cache, issue_key)
        return {
            "operation": "apply_relationships",
            "issue": issue_key,
            "key": issue_key,
            "applied": len(applied),
            "operations": [operation.to_json() for operation in prepared],
            "provider_results": [dict(item) for item in applied],
            "pending_operations": [operation.to_json() for operation in pending_operations],
            "cache_refreshed": True,
            "cache": dict(write_result),
        }

    def _prepare_relationship_removals(
        self,
        site: Any,
        issue_key: str,
        provider_current: Mapping[str, Any] | None,
        operations: list[_ResolvedJiraRelationshipOperation],
    ) -> list[_ResolvedJiraRelationshipOperation]:
        needs_issue = any(operation.action == "remove" and operation.mapping.surface == "issue_link" for operation in operations)
        current_issue = provider_current if provider_current is not None else None
        if needs_issue and current_issue is None:
            current_issue = get_issue(site, issue_key, runner=self.runner)

        needs_remote_links = any(
            operation.action == "remove" and operation.mapping.surface == "remote_link" for operation in operations
        )
        current_remote_links = get_remote_links(site, issue_key, runner=self.runner) if needs_remote_links else []

        prepared: list[_ResolvedJiraRelationshipOperation] = []
        for operation in operations:
            if operation.action == "remove" and operation.mapping.surface == "issue_link":
                assert current_issue is not None
                link_id = _find_issue_link_id(current_issue, operation)
                if link_id is None:
                    raise ProviderOperationError(
                        f"Jira issue link not found for {operation.relationship} {operation.target_ref}"
                    )
                operation = replace(operation, link_id=link_id)
            elif operation.action == "remove" and operation.mapping.surface == "remote_link":
                if not any(link.get("global_id") == operation.remote_global_id for link in current_remote_links):
                    raise ProviderOperationError(
                        f"Jira remote link not found for {operation.relationship} {operation.target_ref}"
                    )
            prepared.append(operation)
        return prepared

    def _dispatch_relationship_operation(
        self,
        site: Any,
        operation: _ResolvedJiraRelationshipOperation,
    ) -> Mapping[str, Any]:
        if operation.mapping.surface == "issue_link":
            if operation.action == "add":
                assert operation.target_issue is not None
                return create_issue_link(
                    site,
                    source_issue=operation.field_issue or "",
                    target_issue=operation.target_issue,
                    link_type=operation.mapping.link_type or "",
                    direction=operation.mapping.direction or "",
                    runner=self.runner,
                )
            assert operation.link_id is not None
            return delete_issue_link(site, operation.link_id, runner=self.runner)

        if operation.mapping.surface == "remote_link":
            assert operation.remote_url is not None
            assert operation.remote_title is not None
            assert operation.remote_global_id is not None
            if operation.action == "add":
                return create_remote_link(
                    site,
                    issue_key=operation.field_issue or "",
                    url=operation.remote_url,
                    title=operation.remote_title,
                    global_id=operation.remote_global_id,
                    relationship=operation.mapping.remote_relationship or operation.relationship.replace("_", " "),
                    application_type=operation.mapping.application_type,
                    application_name=operation.mapping.application_name,
                    runner=self.runner,
                )
            return delete_remote_link_by_global_id(
                site,
                issue_key=operation.field_issue or "",
                global_id=operation.remote_global_id,
                runner=self.runner,
            )

        if operation.mapping.surface == "field":
            assert operation.mapping.field is not None
            assert operation.field_issue is not None
            value = operation.field_value if operation.action == "add" else None
            return update_issue(site, operation.field_issue, fields={operation.mapping.field: value}, runner=self.runner)

        raise ProviderOperationError(f"unsupported Jira relationship surface: {operation.mapping.surface}")

    def _require_write_freshness(
        self,
        request: ProviderRequest,
        site: Any,
        cache: JiraDataCenterIssueCache,
        issue_key: str,
        *,
        target: str,
    ) -> Mapping[str, Any] | None:
        freshness_flag = request.payload.get("freshness_check")
        if freshness_flag is None:
            freshness_flag = request.payload.get("check_freshness")
        if freshness_flag is not None and not _truthy(freshness_flag):
            return None
        artifact = f"Jira issue {issue_key} {target}"
        try:
            metadata = cache.read_freshness_metadata(site, issue_key, target=target)
        except WorkflowCacheError:
            metadata = FreshnessMetadata(
                source_updated_at=None,
                fetched_at=None,
                path=cache.metadata_file(site, issue_key),
                target=target,
            )
        provider_current = get_issue(site, issue_key, runner=self.runner)
        provider_updated_at = _provider_updated_at(provider_current)
        try:
            require_provider_freshness(metadata, provider_updated_at=provider_updated_at, artifact=artifact)
        except WorkflowFreshnessConflict as exc:
            raise ProviderFreshnessError(str(exc)) from exc
        return provider_current

    def _refresh_cache(
        self,
        site: Any,
        cache: JiraDataCenterIssueCache,
        issue_key: str,
    ) -> Mapping[str, str]:
        raw_issue = get_issue(site, issue_key, runner=self.runner)
        remote_links = get_remote_links(site, issue_key, runner=self.runner)
        return cache.write_issue_bundle(site, raw_issue, remote_links=remote_links)


def get_issue(
    site: Any,
    issue_key: str,
    *,
    runner: CommandRunner | None = None,
) -> Mapping[str, Any]:
    """Read one Jira Data Center issue REST object."""

    raw_issue = jira_get_json(site, jira_data_center_issue_path(site, issue_key), runner=runner)
    if not isinstance(raw_issue, Mapping):
        raise JiraProviderError(f"Jira Data Center issue response was not an object: {issue_key}")
    return raw_issue


def get_remote_links(
    site: Any,
    issue_key: str,
    *,
    runner: CommandRunner | None = None,
) -> list[dict[str, Any]]:
    """Read Jira Data Center remote links for one issue."""

    raw_links = jira_get_json(site, jira_data_center_remote_links_path(site, issue_key), runner=runner)
    return normalize_jira_remote_links(raw_links)


def create_issue(
    site: Any,
    *,
    project_key: str,
    issue_type: str,
    title: str,
    body: str,
    labels: tuple[str, ...] = (),
    runner: CommandRunner | None = None,
) -> Mapping[str, Any]:
    payload: dict[str, Any] = {
        "fields": {
            "project": {"key": project_key},
            "summary": title,
            "description": body,
            "issuetype": {"name": issue_type},
        }
    }
    if labels:
        payload["fields"]["labels"] = list(labels)
    result = jira_send_json(site, "POST", f"/rest/api/{site.api_version}/issue", payload, runner=runner)
    if not isinstance(result, Mapping):
        raise JiraProviderError("Jira create issue response was not an object")
    return result


def update_issue(
    site: Any,
    issue_key: str,
    *,
    fields: Mapping[str, Any],
    runner: CommandRunner | None = None,
) -> Mapping[str, Any]:
    result = jira_send_json(
        site,
        "PUT",
        jira_data_center_issue_path(site, issue_key),
        {"fields": dict(fields)},
        runner=runner,
    )
    if not isinstance(result, Mapping):
        return {}
    return result


def create_issue_link(
    site: Any,
    *,
    source_issue: str,
    target_issue: str,
    link_type: str,
    direction: str,
    runner: CommandRunner | None = None,
) -> Mapping[str, Any]:
    """Create one Jira issue link from source issue relationship intent."""

    source_key = normalize_jira_issue_key(source_issue)
    target_key = normalize_jira_issue_key(target_issue)
    if direction == "outward":
        outward_issue = source_key
        inward_issue = target_key
    elif direction == "inward":
        outward_issue = target_key
        inward_issue = source_key
    else:
        raise JiraProviderError(f"unsupported Jira issue link direction: {direction}")
    result = jira_send_json(
        site,
        "POST",
        jira_data_center_issue_links_path(site),
        {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_issue},
            "outwardIssue": {"key": outward_issue},
        },
        runner=runner,
    )
    if not isinstance(result, Mapping):
        return {}
    return result


def delete_issue_link(
    site: Any,
    link_id: str,
    *,
    runner: CommandRunner | None = None,
) -> Mapping[str, Any]:
    result = jira_delete(site, jira_data_center_issue_link_path(site, link_id), runner=runner)
    if not isinstance(result, Mapping):
        return {}
    return result


def create_remote_link(
    site: Any,
    *,
    issue_key: str,
    url: str,
    title: str,
    global_id: str,
    relationship: str,
    application_type: str | None = None,
    application_name: str | None = None,
    runner: CommandRunner | None = None,
) -> Mapping[str, Any]:
    payload: dict[str, Any] = {
        "globalId": global_id,
        "relationship": relationship,
        "object": {"url": url, "title": title},
    }
    if application_type or application_name:
        payload["application"] = {
            "type": application_type or "studykit.workflow",
            "name": application_name or "Workflow",
        }
    result = jira_send_json(site, "POST", jira_data_center_remote_links_path(site, issue_key), payload, runner=runner)
    if not isinstance(result, Mapping):
        return {}
    return result


def delete_remote_link_by_global_id(
    site: Any,
    *,
    issue_key: str,
    global_id: str,
    runner: CommandRunner | None = None,
) -> Mapping[str, Any]:
    result = jira_delete(site, jira_data_center_remote_link_global_id_path(site, issue_key, global_id), runner=runner)
    if not isinstance(result, Mapping):
        return {}
    return result


def delete_remote_link(
    site: Any,
    *,
    issue_key: str,
    link_id: str,
    runner: CommandRunner | None = None,
) -> Mapping[str, Any]:
    result = jira_delete(site, jira_data_center_remote_link_path(site, issue_key, link_id), runner=runner)
    if not isinstance(result, Mapping):
        return {}
    return result


def add_comment(
    site: Any,
    issue_key: str,
    *,
    body: str,
    runner: CommandRunner | None = None,
) -> Mapping[str, Any]:
    result = jira_send_json(
        site,
        "POST",
        jira_data_center_comments_path(site, issue_key),
        {"body": body},
        runner=runner,
    )
    if not isinstance(result, Mapping):
        return {}
    return result


def _required_payload_value(request: ProviderRequest, key: str) -> Any:
    value = request.payload.get(key)
    if value is None or value == "":
        raise ProviderOperationError(f"{request.operation} requires payload.{key}")
    return value


def _is_review_request(request: ProviderRequest) -> bool:
    return request.context.artifact_type.strip().lower() == "review"


def _is_research_request(request: ProviderRequest) -> bool:
    return request.context.artifact_type.strip().lower() == "research"


def _is_spike_request(request: ProviderRequest) -> bool:
    return request.context.artifact_type.strip().lower() == "spike"


def _jira_artifact_issue_type(request: ProviderRequest) -> str | None:
    return JIRA_ARTIFACT_ISSUE_TYPES.get(request.context.artifact_type.strip().lower())


def _jira_issue_title(request: ProviderRequest, title: str) -> str:
    if _is_review_request(request):
        return _jira_prefixed_title(title, JIRA_REVIEW_TITLE_PREFIX)
    if _is_research_request(request):
        return _jira_prefixed_title(title, JIRA_RESEARCH_TITLE_PREFIX)
    if _is_spike_request(request):
        return _jira_prefixed_title(title, JIRA_SPIKE_TITLE_PREFIX)
    return title


def _jira_review_title(title: str) -> str:
    return _jira_prefixed_title(title, JIRA_REVIEW_TITLE_PREFIX)


def _jira_prefixed_title(title: str, prefix: str) -> str:
    if title.startswith(prefix):
        return title
    marker = prefix.strip()
    if title.lower().startswith(marker.lower()):
        return f"{prefix}{title[len(marker):].lstrip()}"
    return f"{prefix}{title}"


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
        name = value.get("name")
        return [str(name)] if name else []
    if isinstance(value, list | tuple | set):
        labels: list[str] = []
        for item in value:
            if isinstance(item, Mapping):
                name = item.get("name")
                if name:
                    labels.append(str(name))
            elif item is not None:
                labels.append(str(item))
        return labels
    return [str(value)]


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no", "off"}
    return bool(value)


def _provider_updated_at(issue: Mapping[str, Any]) -> str | None:
    fields = issue.get("fields") if isinstance(issue.get("fields"), Mapping) else {}
    if not isinstance(fields, Mapping):
        return None
    value = fields.get("updated")
    return str(value).strip() if value else None


def _jira_issue_provider_settings(project: Any) -> Mapping[str, Any]:
    try:
        config = load_workflow_config(project, require=True)
    except (WorkflowConfigError, JiraProviderError) as exc:
        raise ProviderOperationError(str(exc)) from exc
    if config is None or config.issues.kind != "jira":
        raise ProviderOperationError("workflow issue provider is not configured as Jira")
    return config.issues.settings


def _resolve_jira_relationship_operation(
    source_issue: str,
    operation: PendingIssueRelationshipOperation,
    *,
    settings: Mapping[str, Any],
) -> _ResolvedJiraRelationshipOperation:
    mapping = _relationship_mapping(settings, operation.relationship)
    action = operation.action
    if action not in {"add", "remove"}:
        raise ProviderOperationError(f"unsupported Jira relationship action: {action}")

    if mapping.surface == "issue_link":
        target_issue = _jira_relationship_target_issue(operation)
        return _ResolvedJiraRelationshipOperation(
            action=action,
            relationship=operation.relationship,
            target_ref=operation.target_ref,
            target_issue=target_issue,
            field_issue=source_issue,
            mapping=mapping,
        )

    if mapping.surface == "remote_link":
        remote = _remote_link_target(operation.target_ref)
        return _ResolvedJiraRelationshipOperation(
            action=action,
            relationship=operation.relationship,
            target_ref=operation.target_ref,
            field_issue=source_issue,
            remote_url=remote["url"],
            remote_title=remote["title"],
            remote_global_id=_remote_global_id(remote["url"]),
            mapping=mapping,
        )

    if mapping.surface == "field":
        target_issue = _jira_relationship_target_issue(operation)
        field_issue = source_issue
        field_value_target = target_issue
        if mapping.write_to == "target":
            field_issue = target_issue
            field_value_target = source_issue
        field_value = _jira_field_value(field_value_target, mapping)
        return _ResolvedJiraRelationshipOperation(
            action=action,
            relationship=operation.relationship,
            target_ref=operation.target_ref,
            target_issue=target_issue,
            field_issue=field_issue,
            field_value=field_value,
            mapping=mapping,
        )

    raise ProviderOperationError(f"unsupported Jira relationship surface: {mapping.surface}")


def _relationship_mapping(settings: Mapping[str, Any], relationship: str) -> _JiraRelationshipMapping:
    raw_mappings = _relationship_mappings(settings)
    aliases = _relationship_aliases(relationship)
    raw_mapping = None
    matched_name = relationship
    for alias in aliases:
        if alias in raw_mappings:
            raw_mapping = raw_mappings[alias]
            matched_name = alias
            break
    if raw_mapping is None:
        raise ProviderOperationError(
            f"Jira relationship '{relationship}' is not configured; add providers.issues.relationship_mappings.{relationship}"
        )
    if not isinstance(raw_mapping, Mapping):
        raise ProviderOperationError(f"Jira relationship mapping for '{matched_name}' must be a mapping")

    surface = _optional_string(raw_mapping.get("surface") or raw_mapping.get("kind"))
    link_type = _optional_string(raw_mapping.get("link_type") or raw_mapping.get("linkType") or raw_mapping.get("name"))
    field = _optional_string(raw_mapping.get("field") or raw_mapping.get("field_id") or raw_mapping.get("fieldId"))
    if surface is None:
        if link_type:
            surface = "issue_link"
        elif field:
            surface = "field"
        elif _truthy(raw_mapping.get("remote_link") or raw_mapping.get("remoteLink")):
            surface = "remote_link"
    surface = _normalize_surface(surface)

    if surface == "issue_link":
        if not link_type:
            raise ProviderOperationError(f"Jira issue-link mapping for '{matched_name}' requires link_type")
        direction = _normalize_direction(raw_mapping.get("direction"))
        return _JiraRelationshipMapping(
            relationship=relationship,
            surface=surface,
            link_type=link_type,
            direction=direction,
        )

    if surface == "remote_link":
        remote_relationship = _optional_string(
            raw_mapping.get("relationship_label")
            or raw_mapping.get("relationshipLabel")
            or raw_mapping.get("remote_relationship")
            or raw_mapping.get("remoteRelationship")
            or raw_mapping.get("relationship")
        )
        return _JiraRelationshipMapping(
            relationship=relationship,
            surface=surface,
            remote_relationship=remote_relationship,
            application_type=_optional_string(raw_mapping.get("application_type") or raw_mapping.get("applicationType")),
            application_name=_optional_string(raw_mapping.get("application_name") or raw_mapping.get("applicationName")),
        )

    if surface == "field":
        if not field:
            raise ProviderOperationError(f"Jira field mapping for '{matched_name}' requires field")
        write_to = _normalize_write_to(raw_mapping.get("write_to") or raw_mapping.get("writeTo"))
        value = _normalize_field_value_kind(raw_mapping.get("value") or raw_mapping.get("value_kind") or raw_mapping.get("valueKind"))
        return _JiraRelationshipMapping(
            relationship=relationship,
            surface=surface,
            field=field,
            write_to=write_to,
            value=value,
        )

    raise ProviderOperationError(f"unsupported Jira relationship surface for '{matched_name}': {surface}")


def _relationship_mappings(settings: Mapping[str, Any]) -> Mapping[str, Any]:
    raw = settings.get("relationship_mappings") or settings.get("relationshipMappings")
    if raw is None and isinstance(settings.get("relationships"), Mapping):
        relationships = settings["relationships"]
        assert isinstance(relationships, Mapping)
        raw = relationships.get("mappings") or relationships
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ProviderOperationError("providers.issues.relationship_mappings must be a mapping")
    return raw


def _relationship_aliases(relationship: str) -> tuple[str, ...]:
    normalized = relationship.strip().lower().replace("-", "_")
    aliases = {
        "parent": ("parent",),
        "child": ("child", "children", "subtask", "subtasks"),
        "blocked_by": ("blocked_by", "blockedBy", "depends_on", "dependency"),
        "blocking": ("blocking", "blocks"),
        "related": ("related", "relates_to"),
    }
    return aliases.get(normalized, (normalized,))


def _normalize_surface(value: str | None) -> str:
    if value is None:
        raise ProviderOperationError("Jira relationship mapping requires surface, link_type, field, or remote_link")
    normalized = value.strip().lower().replace("-", "_")
    aliases = {
        "issuelink": "issue_link",
        "link": "issue_link",
        "issue": "issue_link",
        "remote": "remote_link",
        "remotelink": "remote_link",
        "field_update": "field",
        "parent_field": "field",
    }
    return aliases.get(normalized, normalized)


def _normalize_direction(value: Any) -> str:
    raw_direction = _optional_string(value)
    direction = raw_direction.lower().replace("-", "_") if raw_direction else None
    if direction not in {"outward", "inward"}:
        raise ProviderOperationError("Jira issue-link relationship mapping requires direction 'outward' or 'inward'")
    return direction


def _normalize_write_to(value: Any) -> str:
    raw_write_to = _optional_string(value)
    write_to = raw_write_to.lower().replace("-", "_") if raw_write_to else None
    if write_to not in {"source", "target"}:
        raise ProviderOperationError("Jira field relationship mapping requires write_to 'source' or 'target'")
    return write_to


def _normalize_field_value_kind(value: Any) -> str:
    raw_value_kind = _optional_string(value)
    value_kind = raw_value_kind.lower().replace("-", "_") if raw_value_kind else None
    if value_kind not in {"key", "key_object", "string"}:
        raise ProviderOperationError("Jira field relationship mapping requires value 'key', 'key_object', or 'string'")
    return value_kind


def _jira_relationship_target_issue(operation: PendingIssueRelationshipOperation) -> str:
    try:
        return normalize_jira_issue_key(operation.target_ref)
    except JiraProviderError as exc:
        raise ProviderOperationError(
            f"Jira relationship '{operation.relationship}' requires a Jira issue key target: {operation.target_ref}"
        ) from exc


def _remote_link_target(target_ref: str) -> dict[str, str]:
    text = target_ref.strip()
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ProviderOperationError(
            f"Jira remote-link relationship requires an absolute http(s) URL target: {target_ref}"
        )
    title = parsed.path.rstrip("/").rsplit("/", 1)[-1] or parsed.netloc
    return {"url": text, "title": title}


def _remote_global_id(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return f"system=studykit-workflow&id={digest}"


def _jira_field_value(issue_key: str, mapping: _JiraRelationshipMapping) -> Any:
    value_kind = mapping.value
    if value_kind == "string":
        return issue_key
    if value_kind == "key":
        return {"key": issue_key}
    if value_kind == "key_object":
        return {"key": issue_key}
    raise ProviderOperationError(f"unsupported Jira field value mapping: {value_kind}")


def _find_issue_link_id(
    issue: Mapping[str, Any],
    operation: _ResolvedJiraRelationshipOperation,
) -> str | None:
    fields = issue.get("fields") if isinstance(issue.get("fields"), Mapping) else {}
    assert isinstance(fields, Mapping)
    for link in _mapping_list(fields.get("issuelinks")):
        raw_type = link.get("type") if isinstance(link.get("type"), Mapping) else {}
        if not isinstance(raw_type, Mapping) or raw_type.get("name") != operation.mapping.link_type:
            continue
        direction_field = "outwardIssue" if operation.mapping.direction == "outward" else "inwardIssue"
        target_issue = link.get(direction_field)
        if not isinstance(target_issue, Mapping):
            continue
        try:
            key = normalize_jira_issue_key(target_issue.get("key") or "")
        except JiraProviderError:
            continue
        if key == operation.target_issue and link.get("id") is not None:
            return str(link["id"])
    return None


def _mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]
