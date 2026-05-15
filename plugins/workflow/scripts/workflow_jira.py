#!/usr/bin/env python3
"""Shared Jira Data Center provider utilities and cache projections."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

from workflow_cache import (
    CACHE_ROOT_NAME,
    SCHEMA_VERSION,
    WorkflowCacheCorrupt,
    WorkflowCacheError,
    WorkflowCacheMiss,
    _atomic_write_text,
    _dump_yaml,
    _read_yaml_mapping,
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
    return JiraDataCenterSite(
        base_url=base_url,
        authority=authority,
        api_version=api_version.strip().strip("/") or "2",
        project=project.upper() if project else None,
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

    def has_issue_projection(self, site: JiraDataCenterSite, issue_key: str) -> bool:
        return self.issue_json_file(site, issue_key).is_file()

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
    lines = ['header = "Accept: application/json"']
    personal_token = _first_env("JIRA_PERSONAL_TOKEN", "JIRA_PAT")
    username = _first_env("JIRA_USERNAME", "JIRA_USER")
    password = _first_env("JIRA_PASSWORD")
    if personal_token:
        lines.append(f'header = "Authorization: Bearer {_curl_quote(personal_token)}"')
    elif username and password:
        lines.append(f'user = "{_curl_quote(username)}:{_curl_quote(password)}"')
    return "\n".join(lines) + "\n"


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _curl_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


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
