#!/usr/bin/env python3
"""Jira Data Center native issue provider."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from workflow_cache import WorkflowCacheError
from workflow_command import CommandRunner
from workflow_jira import (
    JiraDataCenterIssueCache,
    JiraProviderError,
    filter_jira_payload,
    jira_data_center_issue_path,
    jira_data_center_remote_links_path,
    jira_get_json,
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


def _required_payload_value(request: ProviderRequest, key: str) -> Any:
    value = request.payload.get(key)
    if value is None or value == "":
        raise ProviderOperationError(f"{request.operation} requires payload.{key}")
    return value
