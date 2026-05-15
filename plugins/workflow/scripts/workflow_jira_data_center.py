#!/usr/bin/env python3
"""Jira Data Center native issue provider."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from workflow_cache import (
    FreshnessMetadata,
    WorkflowCacheError,
    WorkflowFreshnessConflict,
    require_provider_freshness,
)
from workflow_command import CommandRunner
from workflow_jira import (
    JiraDataCenterIssueCache,
    JiraProviderError,
    filter_jira_payload,
    jira_data_center_comments_path,
    jira_data_center_issue_path,
    jira_data_center_remote_links_path,
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

        project_key = _optional_string(request.payload.get("project") or request.payload.get("project_key")) or site.project
        issue_type = _optional_string(request.payload.get("issue_type") or request.payload.get("issuetype")) or site.issue_type
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
            fields["summary"] = str(request.payload["title"])
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
            fields["summary"] = str(raw_fields.get("summary") or "")
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

    def _require_write_freshness(
        self,
        request: ProviderRequest,
        site: Any,
        cache: JiraDataCenterIssueCache,
        issue_key: str,
        *,
        target: str,
    ) -> None:
        freshness_flag = request.payload.get("freshness_check")
        if freshness_flag is None:
            freshness_flag = request.payload.get("check_freshness")
        if freshness_flag is not None and not _truthy(freshness_flag):
            return
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
