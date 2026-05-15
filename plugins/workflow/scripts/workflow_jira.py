#!/usr/bin/env python3
"""Shared Jira Data Center provider utilities and cache projections."""

from __future__ import annotations

import json
import os
import re
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

from workflow_cache import (
    CACHE_ROOT_NAME,
    SCHEMA_VERSION,
    FreshnessMetadata,
    PendingIssueComment,
    PendingIssueDraft,
    PendingIssueRelationshipOperation,
    WorkflowCacheCorrupt,
    WorkflowCacheError,
    WorkflowCacheMiss,
    _atomic_write_text,
    _dump_yaml,
    _label_names,
    _read_frontmatter_markdown,
    _read_pending_comments,
    _read_pending_relationships,
    _read_yaml_mapping,
    _remove_empty_parents,
    _require_schema,
    _safe_path_segment,
)
from workflow_command import CommandRunner, run_command
from workflow_config import ProviderConfig, WorkflowConfigError, load_workflow_config

JIRA_KEY_RE = re.compile(r"^(?P<project>[A-Z][A-Z0-9]+)-(?P<number>[1-9]\d*)$", re.IGNORECASE)
DEPLOYMENT_DATA_CENTER = "data_center"


class JiraProviderError(RuntimeError):
    """Raised when Jira provider data or configuration cannot be handled."""


@dataclass(frozen=True)
class JiraDataCenterSite:
    """Resolved Jira Data Center or Server site configuration."""

    base_url: str
    authority: str
    api_version: str = "2"
    project: str | None = None
    issue_type: str | None = None
    cache_site: str | None = None

    @property
    def deployment(self) -> str:
        return DEPLOYMENT_DATA_CENTER

    @property
    def cache_site_segment(self) -> str:
        return self.cache_site or self.authority

    def to_json(self) -> dict[str, str]:
        result = {
            "base_url": self.base_url,
            "authority": self.authority,
            "deployment": self.deployment,
            "api_version": self.api_version,
        }
        if self.project:
            result["project"] = self.project
        if self.issue_type:
            result["issue_type"] = self.issue_type
        return result


def resolve_jira_data_center_site(project: Path) -> JiraDataCenterSite:
    """Resolve Jira Data Center issue provider settings from ``.workflow/config.yml``."""

    try:
        config = load_workflow_config(project, require=True)
    except WorkflowConfigError as exc:
        raise JiraProviderError(str(exc)) from exc
    if config is None or config.issues.kind != "jira":
        raise JiraProviderError("workflow issue provider is not configured as Jira")
    return jira_data_center_site_from_provider_config(config.issues)


def jira_data_center_site_from_provider_config(provider: ProviderConfig) -> JiraDataCenterSite:
    """Resolve normalized Jira Data Center settings from an issue provider config."""

    if provider.kind != "jira":
        raise JiraProviderError(f"provider config is not Jira: {provider.kind}")

    settings = dict(provider.settings)
    deployment = _string_setting(settings, "deployment", "type", "edition")
    if deployment is not None and _normalize_deployment(deployment) != DEPLOYMENT_DATA_CENTER:
        raise JiraProviderError("Jira Cloud is out of scope for this provider; use a Data Center/on-premise site")

    raw_site = _string_setting(settings, "site", "base_url", "url", "host", "hostname")
    if raw_site is None:
        raise JiraProviderError("Jira issue provider requires a site, base_url, url, host, or hostname setting")
    base_url, authority, cache_site = _normalize_base_url(raw_site)

    api_version = _string_setting(settings, "api_version", "apiVersion", "rest_api_version") or "2"
    project = _string_setting(settings, "project", "project_key", "projectKey")
    issue_type = _string_setting(settings, "issue_type", "issueType", "issuetype", "issue_type_name")
    return JiraDataCenterSite(
        base_url=base_url,
        authority=authority,
        api_version=api_version.strip().strip("/") or "2",
        project=project.upper() if project else None,
        issue_type=issue_type,
        cache_site=cache_site,
    )


def normalize_jira_issue_key(value: Any) -> str:
    """Normalize a Jira issue key such as ``tm-1234`` to ``TM-1234``."""

    text = str(value).strip()
    match = JIRA_KEY_RE.match(text)
    if not match:
        raise JiraProviderError(f"invalid Jira issue key: {value}")
    return f"{match.group('project').upper()}-{int(match.group('number'))}"


def jira_data_center_issue_path(site: JiraDataCenterSite, issue_key: str) -> str:
    escaped_key = quote(normalize_jira_issue_key(issue_key), safe="")
    return f"/rest/api/{site.api_version}/issue/{escaped_key}"


def jira_data_center_remote_links_path(site: JiraDataCenterSite, issue_key: str) -> str:
    escaped_key = quote(normalize_jira_issue_key(issue_key), safe="")
    return f"/rest/api/{site.api_version}/issue/{escaped_key}/remotelink"


def jira_data_center_remote_link_global_id_path(site: JiraDataCenterSite, issue_key: str, global_id: str) -> str:
    escaped_key = quote(normalize_jira_issue_key(issue_key), safe="")
    return f"/rest/api/{site.api_version}/issue/{escaped_key}/remotelink?globalId={quote(global_id, safe='')}"


def jira_data_center_remote_link_path(site: JiraDataCenterSite, issue_key: str, link_id: str) -> str:
    escaped_key = quote(normalize_jira_issue_key(issue_key), safe="")
    escaped_link_id = quote(str(link_id).strip(), safe="")
    return f"/rest/api/{site.api_version}/issue/{escaped_key}/remotelink/{escaped_link_id}"


def jira_data_center_issue_links_path(site: JiraDataCenterSite) -> str:
    return f"/rest/api/{site.api_version}/issueLink"


def jira_data_center_issue_link_path(site: JiraDataCenterSite, link_id: str) -> str:
    escaped_link_id = quote(str(link_id).strip(), safe="")
    return f"/rest/api/{site.api_version}/issueLink/{escaped_link_id}"


def jira_data_center_comments_path(site: JiraDataCenterSite, issue_key: str) -> str:
    escaped_key = quote(normalize_jira_issue_key(issue_key), safe="")
    return f"/rest/api/{site.api_version}/issue/{escaped_key}/comment"


def jira_get_json(
    site: JiraDataCenterSite,
    path: str,
    *,
    runner: CommandRunner | None = None,
) -> Any:
    """Read one Jira REST resource with curl and parse JSON."""

    url = f"{site.base_url}{path}"
    result = run_command(
        ("curl", "--silent", "--show-error", "--fail", "--request", "GET", "--config", "-", url),
        input_text=_curl_config(),
        runner=runner,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise JiraProviderError(f"Jira response was not valid JSON for {url}: {exc}") from exc


def jira_send_json(
    site: JiraDataCenterSite,
    method: str,
    path: str,
    payload: Mapping[str, Any],
    *,
    runner: CommandRunner | None = None,
) -> Any:
    """Send one Jira REST JSON mutation with curl and parse any JSON response."""

    url = f"{site.base_url}{path}"
    result = run_command(
        ("curl", "--silent", "--show-error", "--fail", "--config", "-"),
        input_text=_curl_json_config(method=method, url=url, payload=payload),
        runner=runner,
    )
    stdout = result.stdout.strip()
    if not stdout:
        return {}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise JiraProviderError(f"Jira response was not valid JSON for {url}: {exc}") from exc


def jira_delete(
    site: JiraDataCenterSite,
    path: str,
    *,
    runner: CommandRunner | None = None,
) -> Any:
    """Send one Jira REST DELETE mutation and parse any JSON response."""

    url = f"{site.base_url}{path}"
    result = run_command(
        ("curl", "--silent", "--show-error", "--fail", "--config", "-"),
        input_text=_curl_method_config(method="DELETE", url=url),
        runner=runner,
    )
    stdout = result.stdout.strip()
    if not stdout:
        return {}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise JiraProviderError(f"Jira response was not valid JSON for {url}: {exc}") from exc


def normalize_jira_data_center_issue(
    issue: Mapping[str, Any],
    *,
    site: JiraDataCenterSite,
    remote_links: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Normalize Jira Data Center REST JSON into the workflow provider payload shape."""

    key = normalize_jira_issue_key(issue.get("key") or "")
    fields = issue.get("fields") if isinstance(issue.get("fields"), Mapping) else {}
    assert isinstance(fields, Mapping)

    status = fields.get("status") if isinstance(fields.get("status"), Mapping) else {}
    assert isinstance(status, Mapping)
    status_category = status.get("statusCategory") if isinstance(status.get("statusCategory"), Mapping) else {}
    assert isinstance(status_category, Mapping)

    raw_comments = fields.get("comment") if isinstance(fields.get("comment"), Mapping) else {}
    assert isinstance(raw_comments, Mapping)
    comments = [_normalize_data_center_comment(comment) for comment in _mapping_list(raw_comments.get("comments"))]

    relationships = _provider_relationships(fields, remote_links=remote_links)
    payload: dict[str, Any] = {
        "issue": key,
        "key": key,
        "id": _normalize_optional(issue.get("id")),
        "title": str(fields.get("summary") or ""),
        "body": _text_field(fields.get("description")),
        "state": _normalize_optional(status.get("name")) or "unknown",
        "stateReason": _normalize_optional(status_category.get("key")),
        "labels": [str(label) for label in fields.get("labels") or [] if label is not None],
        "createdAt": _normalize_optional(fields.get("created")),
        "updatedAt": _normalize_optional(fields.get("updated")),
        "url": f"{site.base_url}/browse/{key}",
        "jira": {**site.to_json(), "key": key},
        "comments": comments,
    }
    if payload["id"] is None:
        payload.pop("id")
    if relationships:
        payload["relationships"] = relationships
    return payload


def normalize_jira_remote_links(raw_links: Any) -> list[dict[str, Any]]:
    """Return a compact provider-native remote link projection."""

    links: list[dict[str, Any]] = []
    for item in _mapping_list(raw_links):
        raw_object = item.get("object") if isinstance(item.get("object"), Mapping) else {}
        assert isinstance(raw_object, Mapping)
        entry: dict[str, Any] = {
            "id": str(item.get("id")) if item.get("id") is not None else None,
            "global_id": _normalize_optional(item.get("globalId") or item.get("global_id")),
            "relationship": _normalize_optional(item.get("relationship")),
            "url": _normalize_optional(raw_object.get("url")),
            "title": _normalize_optional(raw_object.get("title")),
        }
        links.append({key: value for key, value in entry.items() if value is not None})
    return links


class JiraDataCenterIssueCache:
    """Repo-local Jira Data Center cache with native JSON plus an LLM snapshot."""

    def __init__(self, root: Path):
        self.root = root

    @classmethod
    def for_project(cls, project: Path) -> JiraDataCenterIssueCache:
        return cls(project.expanduser().resolve(strict=False) / CACHE_ROOT_NAME)

    def issue_dir(self, site: JiraDataCenterSite, issue_key: str) -> Path:
        return (
            self.root
            / "jira"
            / _safe_path_segment(site.cache_site_segment)
            / "issues"
            / _safe_path_segment(normalize_jira_issue_key(issue_key))
        )

    def snapshot_file(self, site: JiraDataCenterSite, issue_key: str) -> Path:
        return self.issue_dir(site, issue_key) / "snapshot.md"

    def metadata_file(self, site: JiraDataCenterSite, issue_key: str) -> Path:
        return self.issue_dir(site, issue_key) / "metadata.yml"

    def issue_json_file(self, site: JiraDataCenterSite, issue_key: str) -> Path:
        return self.issue_dir(site, issue_key) / "issue.json"

    def remote_links_json_file(self, site: JiraDataCenterSite, issue_key: str) -> Path:
        return self.issue_dir(site, issue_key) / "remote-links.json"

    def pending_issue_dir(self, site: JiraDataCenterSite, local_id: str) -> Path:
        return (
            self.root
            / "jira"
            / _safe_path_segment(site.cache_site_segment)
            / "issues-pending"
            / _safe_path_segment(local_id)
        )

    def pending_issue_file(self, site: JiraDataCenterSite, local_id: str) -> Path:
        return self.pending_issue_dir(site, local_id) / "issue.md"

    def created_issue_archive_dir(self, site: JiraDataCenterSite, local_id: str, issue_key: str) -> Path:
        key = normalize_jira_issue_key(issue_key)
        return (
            self.root
            / "jira"
            / _safe_path_segment(site.cache_site_segment)
            / "issues-created"
            / f"{_safe_path_segment(key)}-{_safe_path_segment(local_id)}"
        )

    def comments_pending_dir(self, site: JiraDataCenterSite, issue_key: str) -> Path:
        return self.issue_dir(site, issue_key) / "comments-pending"

    def relationships_pending_file(self, site: JiraDataCenterSite, issue_key: str) -> Path:
        return self.issue_dir(site, issue_key) / "relationships-pending.yml"

    def pending_issue_relationships_pending_file(self, site: JiraDataCenterSite, local_id: str) -> Path:
        return self.pending_issue_dir(site, local_id) / "relationships-pending.yml"

    def has_issue_projection(self, site: JiraDataCenterSite, issue_key: str) -> bool:
        return self.issue_json_file(site, issue_key).is_file()

    def read_pending_issue_draft(self, site: JiraDataCenterSite, local_id: str) -> PendingIssueDraft:
        path = self.pending_issue_file(site, local_id)
        if not path.is_file():
            raise WorkflowCacheMiss(f"Jira pending issue draft does not exist: {path}")

        frontmatter, body = _read_frontmatter_markdown(path)
        if frontmatter.get("schema_version") is not None:
            _require_schema(frontmatter, path)

        title = str(frontmatter.get("title") or "").strip()
        if not title:
            raise WorkflowCacheCorrupt(f"Jira pending issue draft is missing title: {path}")
        return PendingIssueDraft(
            local_id=_safe_path_segment(local_id),
            path=path,
            title=title,
            body=body,
            labels=tuple(_label_names(frontmatter.get("labels"))),
            state=str(frontmatter.get("state") or "open").strip().lower(),
            state_reason=_normalize_optional(frontmatter.get("state_reason") or frontmatter.get("stateReason")),
        )

    def read_pending_issue_comments(self, site: JiraDataCenterSite, issue_key: str) -> list[PendingIssueComment]:
        key = normalize_jira_issue_key(issue_key)
        return _read_pending_comments(
            self.comments_pending_dir(site, key),
            target_kind="issue",
            target_id=key,
        )

    def read_pending_issue_relationships(
        self,
        site: JiraDataCenterSite,
        issue_key: str,
    ) -> list[PendingIssueRelationshipOperation]:
        """Read pending relationship operations for an existing Jira issue projection."""

        key = normalize_jira_issue_key(issue_key)
        return _read_pending_relationships(
            self.relationships_pending_file(site, key),
            target_kind="issue",
            target_id=key,
        )

    def read_pending_draft_relationships(
        self,
        site: JiraDataCenterSite,
        local_id: str,
    ) -> list[PendingIssueRelationshipOperation]:
        """Read pending relationship operations for a pending Jira issue projection."""

        safe_local_id = _safe_path_segment(local_id)
        return _read_pending_relationships(
            self.pending_issue_relationships_pending_file(site, safe_local_id),
            target_kind="pending_issue",
            target_id=safe_local_id,
        )

    def read_freshness_metadata(
        self,
        site: JiraDataCenterSite,
        issue_key: str,
        *,
        target: str = "issue",
    ) -> FreshnessMetadata:
        path = self.metadata_file(site, issue_key)
        if not path.is_file():
            raise WorkflowCacheMiss(f"Jira freshness cache does not exist: {path}")
        data = _read_yaml_mapping(path)
        _require_schema(data, path)
        return FreshnessMetadata(
            source_updated_at=_normalize_optional(data.get("source_updated_at")),
            fetched_at=_normalize_optional(data.get("fetched_at")),
            path=path,
            target=target,
        )

    def read_issue(
        self,
        site: JiraDataCenterSite,
        issue_key: str,
        *,
        include_body: bool = True,
        include_comments: bool = True,
        include_relationships: bool = True,
    ) -> dict[str, Any]:
        """Read a cached Jira Data Center issue projection."""

        key = normalize_jira_issue_key(issue_key)
        issue_path = self.issue_json_file(site, key)
        metadata_path = self.metadata_file(site, key)
        if not issue_path.is_file():
            raise WorkflowCacheMiss(f"Jira issue cache does not exist: {issue_path}")
        if not metadata_path.is_file():
            raise WorkflowCacheMiss(f"Jira metadata cache does not exist: {metadata_path}")

        try:
            metadata = _read_yaml_mapping(metadata_path)
            _require_schema(metadata, metadata_path)
            issue = _read_json_mapping(issue_path)
            remote_links = _read_json_list_if_exists(self.remote_links_json_file(site, key))
            payload = normalize_jira_data_center_issue(issue, site=site, remote_links=remote_links)
            payload["cache"] = {
                "hit": True,
                "issue_dir": str(self.issue_dir(site, key)),
                "snapshot": str(self.snapshot_file(site, key)),
                "metadata_file": str(metadata_path),
                "issue_json": str(issue_path),
                "remote_links_json": str(self.remote_links_json_file(site, key)),
                "fetchedAt": metadata.get("fetched_at"),
                "sourceUpdatedAt": metadata.get("source_updated_at"),
            }
            return filter_jira_payload(
                payload,
                include_body=include_body,
                include_comments=include_comments,
                include_relationships=include_relationships,
            )
        except WorkflowCacheError:
            raise
        except Exception as exc:
            raise WorkflowCacheCorrupt(f"could not read Jira issue cache {issue_path}: {exc}") from exc

    def read_issue_json(self, site: JiraDataCenterSite, issue_key: str) -> Mapping[str, Any]:
        key = normalize_jira_issue_key(issue_key)
        issue_path = self.issue_json_file(site, key)
        if not issue_path.is_file():
            raise WorkflowCacheMiss(f"Jira issue cache does not exist: {issue_path}")
        return _read_json_mapping(issue_path)

    def write_issue_bundle(
        self,
        site: JiraDataCenterSite,
        issue: Mapping[str, Any],
        *,
        remote_links: list[Mapping[str, Any]] | None = None,
        fetched_at: str | None = None,
    ) -> dict[str, str]:
        """Write native JSON, metadata, and generated Markdown snapshot."""

        key = normalize_jira_issue_key(issue.get("key") or "")
        links = [dict(item) for item in (remote_links or [])]
        normalized = normalize_jira_data_center_issue(issue, site=site, remote_links=links)
        now = fetched_at or _utc_now()
        source_updated_at = _normalize_optional(normalized.get("updatedAt")) or now

        issue_dir = self.issue_dir(site, key)
        issue_dir.mkdir(parents=True, exist_ok=True)
        issue_path = self.issue_json_file(site, key)
        remote_links_path = self.remote_links_json_file(site, key)
        metadata_path = self.metadata_file(site, key)
        snapshot_path = self.snapshot_file(site, key)

        _atomic_write_text(issue_path, _format_json(issue))
        _atomic_write_text(remote_links_path, _format_json(links))
        _atomic_write_text(snapshot_path, render_jira_snapshot(normalized))
        _atomic_write_text(
            metadata_path,
            _dump_yaml(
                {
                    "schema_version": SCHEMA_VERSION,
                    "provider": "jira",
                    "deployment": DEPLOYMENT_DATA_CENTER,
                    "site": site.base_url,
                    "api_version": site.api_version,
                    "key": key,
                    "project": key.split("-", 1)[0],
                    "source_updated_at": source_updated_at,
                    "created_at": _normalize_optional(normalized.get("createdAt")),
                    "fetched_at": now,
                    "url": normalized.get("url"),
                    "snapshot": "snapshot.md",
                    "issue_json": "issue.json",
                    "remote_links_json": "remote-links.json",
                }
            ),
        )
        return {
            "issue_dir": str(issue_dir),
            "snapshot": str(snapshot_path),
            "metadata_file": str(metadata_path),
            "issue_json": str(issue_path),
            "remote_links_json": str(remote_links_path),
        }

    def remove_pending_issue_comments(
        self,
        site: JiraDataCenterSite,
        issue_key: str,
        comments: list[PendingIssueComment],
    ) -> list[Path]:
        key = normalize_jira_issue_key(issue_key)
        pending_dir = self.comments_pending_dir(site, key)
        removed: list[Path] = []
        for comment in comments:
            if comment.path.parent.resolve(strict=False) != pending_dir.resolve(strict=False):
                raise WorkflowCacheError(f"pending comment is outside Jira issue pending directory: {comment.path}")
            if comment.path.exists():
                comment.path.unlink()
                removed.append(comment.path)
        _remove_empty_parents(pending_dir, stop_at=self.issue_dir(site, key))
        return removed

    def remove_pending_issue_relationships(
        self,
        site: JiraDataCenterSite,
        issue_key: str,
        operations: list[PendingIssueRelationshipOperation],
    ) -> list[Path]:
        """Remove a successfully consumed Jira pending relationship file."""

        key = normalize_jira_issue_key(issue_key)
        path = self.relationships_pending_file(site, key)
        return self._remove_pending_relationship_file(path, operations, stop_at=self.issue_dir(site, key))

    def remove_pending_draft_relationships(
        self,
        site: JiraDataCenterSite,
        local_id: str,
        operations: list[PendingIssueRelationshipOperation],
    ) -> list[Path]:
        """Remove a consumed pending relationship file from a pending Jira issue projection."""

        safe_local_id = _safe_path_segment(local_id)
        path = self.pending_issue_relationships_pending_file(site, safe_local_id)
        return self._remove_pending_relationship_file(
            path,
            operations,
            stop_at=self.pending_issue_dir(site, safe_local_id),
        )

    def _remove_pending_relationship_file(
        self,
        path: Path,
        operations: list[PendingIssueRelationshipOperation],
        *,
        stop_at: Path,
    ) -> list[Path]:
        expected = path.resolve(strict=False)
        seen = False
        for operation in operations:
            seen = True
            if operation.path.resolve(strict=False) != expected:
                raise WorkflowCacheError(f"pending relationship operation is outside Jira pending file: {operation.path}")
        if not seen or not path.exists():
            return []
        path.unlink()
        _remove_empty_parents(path.parent, stop_at=stop_at)
        return [path]

    def finalize_pending_issue_creation(
        self,
        site: JiraDataCenterSite,
        local_id: str,
        issue_key: str,
    ) -> dict[str, str | None]:
        pending_dir = self.pending_issue_dir(site, local_id)
        draft_path = pending_dir / "issue.md"
        archive_dir = self.created_issue_archive_dir(site, local_id, issue_key)
        archived_issue: Path | None = None
        if draft_path.exists():
            archive_dir.mkdir(parents=True, exist_ok=True)
            archived_issue = archive_dir / "issue.md"
            os.replace(draft_path, archived_issue)

        issue_dir = self.issue_dir(site, issue_key)
        issue_dir.mkdir(parents=True, exist_ok=True)
        moved_comments = _move_path_if_exists(pending_dir / "comments-pending", issue_dir / "comments-pending")
        moved_relationships = _move_path_if_exists(
            pending_dir / "relationships-pending.yml",
            issue_dir / "relationships-pending.yml",
        )
        _remove_empty_parents(pending_dir, stop_at=self.root / "jira" / _safe_path_segment(site.cache_site_segment))
        return {
            "archived_issue": str(archived_issue) if archived_issue is not None else None,
            "comments_pending": str(moved_comments) if moved_comments is not None else None,
            "relationships_pending": str(moved_relationships) if moved_relationships is not None else None,
        }


def filter_jira_payload(
    payload: Mapping[str, Any],
    *,
    include_body: bool,
    include_comments: bool,
    include_relationships: bool,
) -> dict[str, Any]:
    """Apply read include flags to a normalized Jira issue payload."""

    result = dict(payload)
    if not include_body:
        result.pop("body", None)
    if not include_comments:
        result.pop("comments", None)
    if not include_relationships:
        result.pop("relationships", None)
    return result


def render_jira_snapshot(issue: Mapping[str, Any]) -> str:
    """Render an LLM-facing, generated Jira issue snapshot."""

    lines = [
        f"# {issue.get('key')}: {issue.get('title') or ''}".rstrip(),
        "",
        "Generated read-only Jira Data Center snapshot.",
        "",
        f"- Provider: Jira Data Center",
        f"- Site: {issue.get('jira', {}).get('base_url') if isinstance(issue.get('jira'), Mapping) else ''}",
        f"- Status: {issue.get('state') or ''}",
        f"- Updated: {issue.get('updatedAt') or ''}",
        f"- Labels: {', '.join(str(label) for label in issue.get('labels') or []) or 'none'}",
        "",
        "## Description",
        "",
        str(issue.get("body") or "").strip() or "(empty)",
        "",
        "## Comments",
        "",
    ]

    comments = issue.get("comments") if isinstance(issue.get("comments"), list) else []
    if comments:
        for comment in comments:
            if not isinstance(comment, Mapping):
                continue
            author = _author_name(comment.get("author"))
            lines.extend(
                [
                    f"### {comment.get('createdAt') or 'unknown time'} - {author}",
                    "",
                    str(comment.get("body") or "").strip() or "(empty)",
                    "",
                ]
            )
    else:
        lines.extend(["No comments cached.", ""])

    relationships = issue.get("relationships") if isinstance(issue.get("relationships"), Mapping) else {}
    assert isinstance(relationships, Mapping)
    lines.extend(["## Remote Links", ""])
    remote_links = relationships.get("remote_links") if isinstance(relationships.get("remote_links"), list) else []
    if remote_links:
        for link in remote_links:
            if not isinstance(link, Mapping):
                continue
            title = link.get("title") or link.get("url") or "remote link"
            relationship = f" ({link.get('relationship')})" if link.get("relationship") else ""
            url = f" — {link.get('url')}" if link.get("url") else ""
            lines.append(f"- {title}{relationship}{url}")
    else:
        lines.append("No remote links cached.")

    workflow = relationships.get("workflow") if isinstance(relationships.get("workflow"), Mapping) else {}
    if workflow:
        lines.extend(["", "## Workflow Relationships", ""])
        assert isinstance(workflow, Mapping)
        parent = workflow.get("parent")
        if isinstance(parent, Mapping):
            lines.append(f"- Parent: {_relationship_issue_label(parent)}")
        children = workflow.get("children") if isinstance(workflow.get("children"), list) else []
        if children:
            lines.append(f"- Children: {', '.join(_relationship_issue_label(child) for child in children if isinstance(child, Mapping))}")
        dependencies = workflow.get("dependencies") if isinstance(workflow.get("dependencies"), Mapping) else {}
        if isinstance(dependencies, Mapping):
            blocked_by = dependencies.get("blocked_by") if isinstance(dependencies.get("blocked_by"), list) else []
            blocking = dependencies.get("blocking") if isinstance(dependencies.get("blocking"), list) else []
            if blocked_by:
                lines.append(
                    f"- Blocked by: {', '.join(_relationship_issue_label(item) for item in blocked_by if isinstance(item, Mapping))}"
                )
            if blocking:
                lines.append(
                    f"- Blocking: {', '.join(_relationship_issue_label(item) for item in blocking if isinstance(item, Mapping))}"
                )
        related = workflow.get("related") if isinstance(workflow.get("related"), list) else []
        if related:
            lines.append(f"- Related: {', '.join(_relationship_issue_label(item) for item in related if isinstance(item, Mapping))}")

    issue_links = relationships.get("issue_links") if isinstance(relationships.get("issue_links"), list) else []
    if issue_links:
        lines.extend(["", "## Issue Links", ""])
        for link in issue_links:
            if not isinstance(link, Mapping):
                continue
            lines.append(f"- {_format_issue_link(link)}")

    lines.extend(["", "## Raw Cache", "", "- `issue.json`", "- `remote-links.json`", "- `metadata.yml`", ""])
    return "\n".join(lines)


def _provider_relationships(
    fields: Mapping[str, Any],
    *,
    remote_links: list[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    relationships: dict[str, Any] = {}
    if remote_links is not None:
        relationships["remote_links"] = [dict(item) for item in remote_links]

    issue_links = [_normalize_issue_link(item) for item in _mapping_list(fields.get("issuelinks"))]
    if issue_links:
        relationships["issue_links"] = issue_links

    parent = fields.get("parent")
    if isinstance(parent, Mapping):
        relationships["parent"] = _issue_stub(parent)

    subtasks = [_issue_stub(item) for item in _mapping_list(fields.get("subtasks"))]
    if subtasks:
        relationships["subtasks"] = subtasks
    workflow_relationships = _workflow_relationships(relationships)
    if workflow_relationships:
        relationships["workflow"] = workflow_relationships
    return relationships


def _normalize_issue_link(link: Mapping[str, Any]) -> dict[str, Any]:
    raw_type = link.get("type") if isinstance(link.get("type"), Mapping) else {}
    assert isinstance(raw_type, Mapping)
    entry: dict[str, Any] = {
        "id": str(link.get("id")) if link.get("id") is not None else None,
        "type": _normalize_optional(raw_type.get("name")),
        "inward": _normalize_optional(raw_type.get("inward")),
        "outward": _normalize_optional(raw_type.get("outward")),
    }
    inward_issue = link.get("inwardIssue")
    outward_issue = link.get("outwardIssue")
    if isinstance(inward_issue, Mapping):
        entry["inward_issue"] = _issue_stub(inward_issue)
    if isinstance(outward_issue, Mapping):
        entry["outward_issue"] = _issue_stub(outward_issue)
    return {key: value for key, value in entry.items() if value is not None}


def _workflow_relationships(provider_relationships: Mapping[str, Any]) -> dict[str, Any]:
    """Map Jira-native relationship fields into workflow relationship categories.

    Jira link direction is label-based. The REST payload exposes `inwardIssue`
    or `outwardIssue`; the corresponding `type.inward` or `type.outward` label
    is the only stable semantic surface for dependency mapping.
    """

    workflow: dict[str, Any] = {}

    parent = provider_relationships.get("parent")
    if isinstance(parent, Mapping):
        workflow["parent"] = _workflow_issue(parent)

    subtasks = provider_relationships.get("subtasks")
    if isinstance(subtasks, list):
        children = [_workflow_issue(item) for item in subtasks if isinstance(item, Mapping)]
        if children:
            workflow["children"] = children

    dependencies: dict[str, list[dict[str, Any]]] = {"blocked_by": [], "blocking": []}
    related: list[dict[str, Any]] = []
    issue_links = provider_relationships.get("issue_links")
    if isinstance(issue_links, list):
        for link in issue_links:
            if not isinstance(link, Mapping):
                continue
            target, direction, label = _issue_link_target_and_label(link)
            if target is None:
                continue
            mapped = _workflow_issue(target)
            mapped["source"] = "issuelinks"
            mapped["direction"] = direction
            if link.get("type"):
                mapped["link_type"] = link.get("type")
            if label:
                mapped["label"] = label

            bucket = _dependency_bucket(label)
            if bucket is None:
                related.append(mapped)
            else:
                dependencies[bucket].append(mapped)

    compact_dependencies = {name: items for name, items in dependencies.items() if items}
    if compact_dependencies:
        workflow["dependencies"] = compact_dependencies
    if related:
        workflow["related"] = related

    remote_links = provider_relationships.get("remote_links")
    if isinstance(remote_links, list):
        external_links = [_workflow_external_link(item) for item in remote_links if isinstance(item, Mapping)]
        if external_links:
            workflow["external_links"] = external_links

    return workflow


def _issue_link_target_and_label(link: Mapping[str, Any]) -> tuple[Mapping[str, Any] | None, str, str | None]:
    if isinstance(link.get("outward_issue"), Mapping):
        return link["outward_issue"], "outward", _normalize_optional(link.get("outward"))
    if isinstance(link.get("inward_issue"), Mapping):
        return link["inward_issue"], "inward", _normalize_optional(link.get("inward"))
    return None, "unknown", None


def _dependency_bucket(label: str | None) -> str | None:
    normalized = _normalize_link_label(label)
    if normalized in {"blocks", "is blocking", "is depended on by", "is required by"}:
        return "blocking"
    if normalized in {"is blocked by", "blocked by", "depends on", "requires", "is dependent on"}:
        return "blocked_by"
    return None


def _normalize_link_label(label: str | None) -> str:
    if label is None:
        return ""
    return " ".join(str(label).strip().lower().replace("_", " ").replace("-", " ").split())


def _workflow_issue(issue: Mapping[str, Any]) -> dict[str, Any]:
    key = _normalize_optional(issue.get("key"))
    result: dict[str, Any] = {
        "provider": "jira",
        "key": key,
        "issue": key,
        "id": _normalize_optional(issue.get("id")),
        "title": _normalize_optional(issue.get("summary") or issue.get("title")),
        "state": _normalize_optional(issue.get("status") or issue.get("state")),
    }
    return {name: value for name, value in result.items() if value is not None}


def _workflow_external_link(link: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source": "remote_links",
        "title": _normalize_optional(link.get("title")),
        "url": _normalize_optional(link.get("url")),
        "relationship": _normalize_optional(link.get("relationship")),
        "global_id": _normalize_optional(link.get("global_id")),
        "id": _normalize_optional(link.get("id")),
    }
    return {name: value for name, value in result.items() if value is not None}


def _issue_stub(issue: Mapping[str, Any]) -> dict[str, Any]:
    fields = issue.get("fields") if isinstance(issue.get("fields"), Mapping) else {}
    assert isinstance(fields, Mapping)
    status = fields.get("status") if isinstance(fields.get("status"), Mapping) else {}
    assert isinstance(status, Mapping)
    result: dict[str, Any] = {
        "key": _normalize_optional(issue.get("key")),
        "id": _normalize_optional(issue.get("id")),
        "summary": _normalize_optional(fields.get("summary")),
        "status": _normalize_optional(status.get("name")),
    }
    return {key: value for key, value in result.items() if value is not None}


def _normalize_data_center_comment(comment: Mapping[str, Any]) -> dict[str, Any]:
    author = comment.get("author") if isinstance(comment.get("author"), Mapping) else {}
    assert isinstance(author, Mapping)
    return {
        "id": str(comment.get("id") or ""),
        "author": {str(key): value for key, value in author.items()},
        "body": _text_field(comment.get("body")),
        "createdAt": _normalize_optional(comment.get("created")),
        "updatedAt": _normalize_optional(comment.get("updated")),
    }


def _format_issue_link(link: Mapping[str, Any]) -> str:
    type_name = link.get("type") or "link"
    if isinstance(link.get("outward_issue"), Mapping):
        issue = link["outward_issue"]
        assert isinstance(issue, Mapping)
        return f"{type_name} outward {issue.get('key')}: {issue.get('summary') or ''}".rstrip()
    if isinstance(link.get("inward_issue"), Mapping):
        issue = link["inward_issue"]
        assert isinstance(issue, Mapping)
        return f"{type_name} inward {issue.get('key')}: {issue.get('summary') or ''}".rstrip()
    return str(type_name)


def _relationship_issue_label(issue: Mapping[str, Any]) -> str:
    key = issue.get("key") or issue.get("issue") or "unknown"
    title = issue.get("title")
    return f"{key} ({title})" if title else str(key)


def _read_json_mapping(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowCacheCorrupt(f"invalid JSON cache file: {path}: {exc}") from exc
    if not isinstance(value, Mapping):
        raise WorkflowCacheCorrupt(f"JSON cache file must contain an object: {path}")
    return value


def _read_json_list_if_exists(path: Path) -> list[Mapping[str, Any]]:
    if not path.is_file():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowCacheCorrupt(f"invalid JSON cache file: {path}: {exc}") from exc
    return _mapping_list(value)


def _format_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _format_json_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _normalize_base_url(value: str) -> tuple[str, str, str]:
    raw = value.strip().rstrip("/")
    if not raw:
        raise JiraProviderError("Jira site setting is empty")
    if "://" not in raw:
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise JiraProviderError(f"unsupported Jira site URL: {value}")
    base_path = parsed.path.rstrip("/")
    base_url = f"{parsed.scheme}://{parsed.netloc}{base_path}"
    authority = parsed.netloc.lower()
    cache_site = authority if not base_path else f"{authority}{base_path.replace('/', '-')}"
    return base_url, authority, cache_site


def _normalize_deployment(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in {"", "auto", "on_premise", "on_prem", "onprem", "premise", "server", "datacenter", "data_center", "dc"}:
        return DEPLOYMENT_DATA_CENTER
    if normalized in {"cloud", "jira_cloud"}:
        return "cloud"
    raise JiraProviderError(f"unsupported Jira deployment: {value}")


def _string_setting(settings: Mapping[str, Any], *names: str) -> str | None:
    for name in names:
        value = settings.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _curl_config() -> str:
    lines = _curl_base_config_lines()
    return "\n".join(lines) + "\n"


def _curl_json_config(*, method: str, url: str, payload: Mapping[str, Any]) -> str:
    lines = _curl_method_config(method=method, url=url).rstrip("\n").splitlines()
    lines.extend(
        [
            'header = "Content-Type: application/json"',
            f'data-binary = "{_curl_quote(_format_json_compact(payload))}"',
        ]
    )
    return "\n".join(lines) + "\n"


def _curl_method_config(*, method: str, url: str) -> str:
    lines = _curl_base_config_lines()
    lines.extend(
        [
            f'request = "{_curl_quote(method.upper())}"',
            f'url = "{_curl_quote(url)}"',
        ]
    )
    return "\n".join(lines) + "\n"


def _curl_base_config_lines() -> list[str]:
    lines = ['header = "Accept: application/json"']
    personal_token = _first_env("JIRA_PERSONAL_TOKEN", "JIRA_PAT")
    username = _first_env("JIRA_USERNAME", "JIRA_USER")
    password = _first_env("JIRA_PASSWORD")
    if personal_token:
        lines.append(f'header = "Authorization: Bearer {_curl_quote(personal_token)}"')
    elif username and password:
        lines.append(f'user = "{_curl_quote(username)}:{_curl_quote(password)}"')
    return lines


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _curl_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _move_path_if_exists(source: Path, destination: Path) -> Path | None:
    if not source.exists():
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()
    os.replace(source, destination)
    return destination


def _mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text_field(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _normalize_optional(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _author_name(value: Any) -> str:
    if isinstance(value, Mapping):
        for key in ("displayName", "name", "key", "accountId"):
            raw = value.get(key)
            if raw:
                return str(raw)
    if value:
        return str(value)
    return "unknown"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
