#!/usr/bin/env python3
"""Parse and normalize provider-native workflow references."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse

from workflow_command import CommandRunner, WorkflowCommandError
from workflow_config import ProviderConfig, WorkflowConfig, normalize_role
from workflow_github import GitHubRepository, GitHubRepositoryError, parse_github_remote_url
from workflow_github import resolve_github_repository

GITHUB_HASH_RE = re.compile(r"^#(?P<number>[1-9]\d*)$")
GITHUB_REPO_RE = re.compile(
    r"^(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)#(?P<number>[1-9]\d*)$"
)
GITHUB_ISSUE_URL_RE = re.compile(
    r"^https?://(?P<host>[^/\s]+)/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/issues/"
    r"(?P<number>[1-9]\d*)(?:[/?#].*)?$",
    re.IGNORECASE,
)
JIRA_KEY_RE = re.compile(r"^(?P<project>[A-Z][A-Z0-9]+)-(?P<number>[1-9]\d*)$", re.IGNORECASE)
WIKI_PATH_RE = re.compile(r"^(?:\./)?(?P<path>wiki/[^/\s]+/.+)$")
CONFLUENCE_PAGE_PATH_RE = re.compile(
    r"/wiki/spaces/(?P<space>[^/]+)/pages/(?P<page_id>\d+)(?:/(?P<title>[^/?#]+))?"
)


class ProviderReferenceError(ValueError):
    """Raised when a workflow provider reference cannot be normalized."""


class ProviderReferenceAmbiguityError(ProviderReferenceError):
    """Raised when a reference needs more provider context."""


class ProviderReferenceMismatchError(ProviderReferenceError):
    """Raised when a reference does not match the configured provider role."""


@dataclass(frozen=True)
class ProviderReference:
    """Resolved provider-native reference identity."""

    input: str
    provider: str
    kind: str
    authority: str
    native: Mapping[str, Any]
    display: str
    url: str | None = None
    ref: str | None = None
    title: str | None = None
    status: str | None = None
    aliases: tuple[str, ...] = field(default_factory=tuple)
    version: str | None = None

    def to_json(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "input": self.input,
            "provider": self.provider,
            "kind": self.kind,
            "authority": self.authority,
            "native": dict(self.native),
            "display": self.display,
        }
        if self.url is not None:
            payload["url"] = self.url
        if self.title is not None:
            payload["title"] = self.title
        if self.status is not None:
            payload["status"] = self.status
        if self.aliases:
            payload["aliases"] = list(self.aliases)
        if self.version is not None:
            payload["version"] = self.version
        if self.ref is not None:
            payload["ref"] = self.ref
        return payload


def normalize_provider_reference(
    reference: str,
    config: WorkflowConfig,
    *,
    role: str | None = None,
    allow_bare_issue_number: bool = False,
    runner: CommandRunner | None = None,
) -> ProviderReference:
    """Resolve one author-facing provider reference using workflow config.

    ``role`` may be ``issue`` or ``knowledge``. When omitted, the parser infers
    the role from explicit provider syntax and validates it against the matching
    configured provider.
    """

    raw = reference.strip()
    if not raw:
        raise ProviderReferenceAmbiguityError("provider reference is empty")

    normalized_role = normalize_role(role) if role is not None else None

    github_issue = _parse_github_issue(raw, config, role=normalized_role, runner=runner)
    if github_issue is not None:
        return github_issue

    if raw.isdigit():
        if allow_bare_issue_number:
            return _github_issue_reference(raw, config, role=normalized_role, runner=runner)
        raise ProviderReferenceAmbiguityError(
            f"bare numeric reference '{raw}' is ambiguous; use #number for GitHub issues"
        )

    jira_issue = _parse_jira_issue(raw, config, role=normalized_role)
    if jira_issue is not None:
        return jira_issue

    wiki_page = _parse_github_wiki_page(raw, config, role=normalized_role, runner=runner)
    if wiki_page is not None:
        return wiki_page

    confluence_page = _parse_confluence_page(raw, config, role=normalized_role)
    if confluence_page is not None:
        return confluence_page

    if normalized_role == "knowledge" and config.knowledge.kind == "confluence":
        return _confluence_display_reference(raw, config)

    raise ProviderReferenceAmbiguityError(f"could not determine provider reference type: {reference}")


def _parse_github_issue(
    raw: str,
    config: WorkflowConfig,
    *,
    role: str | None,
    runner: CommandRunner | None,
) -> ProviderReference | None:
    match = GITHUB_HASH_RE.match(raw)
    if match:
        return _github_issue_reference(raw, config, role=role, runner=runner)

    match = GITHUB_REPO_RE.match(raw)
    if match:
        _ensure_provider_role(config, role, expected_role="issue", provider="github", raw=raw)
        repo = GitHubRepository(
            host=_github_authority_for_role(config, "issue", runner=runner),
            owner=match.group("owner"),
            name=match.group("repo").removesuffix(".git"),
        )
        return _github_issue_identity(raw, repo, int(match.group("number")), display=raw)

    match = GITHUB_ISSUE_URL_RE.match(raw)
    if match:
        _ensure_provider_role(config, role, expected_role="issue", provider="github", raw=raw)
        repo = GitHubRepository(
            host=_normalize_authority(match.group("host")),
            owner=match.group("owner"),
            name=match.group("repo").removesuffix(".git"),
        )
        number = int(match.group("number"))
        base_repo = _optional_github_repo_for_role(config, "issue", runner=runner)
        display = (
            f"#{number}"
            if base_repo is not None and _same_github_repo(repo, base_repo)
            else f"{repo.owner}/{repo.name}#{number}"
        )
        return _github_issue_identity(raw, repo, number, display=display)

    return None


def _github_issue_reference(
    raw: str,
    config: WorkflowConfig,
    *,
    role: str | None,
    runner: CommandRunner | None,
) -> ProviderReference:
    number_text = raw[1:] if raw.startswith("#") else raw
    _ensure_provider_role(config, role, expected_role="issue", provider="github", raw=raw)
    repo = _github_repo_for_role(config, "issue", runner=runner)
    return _github_issue_identity(raw, repo, int(number_text), display=f"#{int(number_text)}")


def _github_issue_identity(raw: str, repo: GitHubRepository, number: int, *, display: str) -> ProviderReference:
    authority = _normalize_authority(repo.host)
    native = {"owner": repo.owner, "repo": repo.name, "number": number}
    return ProviderReference(
        input=raw,
        provider="github",
        kind="issue",
        authority=authority,
        native=native,
        url=f"https://{authority}/{repo.owner}/{repo.name}/issues/{number}",
        display=display,
        ref=f"workflowref:github:issue:{authority}/{repo.owner}/{repo.name}/{number}",
    )


def _parse_jira_issue(raw: str, config: WorkflowConfig, *, role: str | None) -> ProviderReference | None:
    match = JIRA_KEY_RE.match(raw)
    if not match:
        return None

    _ensure_provider_role(config, role, expected_role="issue", provider="jira", raw=raw)
    key = f"{match.group('project').upper()}-{int(match.group('number'))}"
    settings = config.issues.settings
    site = _authority_from_settings(settings, "site", "host", "hostname", "base_url", "url")
    if site is None:
        site = "jira"
    authority = _normalize_authority(site)
    native: dict[str, Any] = {
        "key": key,
        "project": match.group("project").upper(),
        "number": int(match.group("number")),
    }
    issue_id = _string_setting(settings, "issue_id", "id")
    if issue_id:
        native["id"] = issue_id
    url = None if authority == "jira" else f"https://{authority}/browse/{key}"
    return ProviderReference(
        input=raw,
        provider="jira",
        kind="issue",
        authority=authority,
        native=native,
        url=url,
        display=key,
        ref=f"workflowref:jira:issue:{authority}/{key}",
    )


def _parse_github_wiki_page(
    raw: str,
    config: WorkflowConfig,
    *,
    role: str | None,
    runner: CommandRunner | None,
) -> ProviderReference | None:
    match = WIKI_PATH_RE.match(raw)
    if not match:
        return None

    _ensure_provider_role(config, role, expected_role="knowledge", provider="github", raw=raw)
    path = _normalize_wiki_path(match.group("path"))
    repo = _github_repo_for_role(config, "knowledge", runner=runner)
    authority = _normalize_authority(repo.host)
    branch = _string_setting(config.knowledge.settings, "branch", "ref") or "main"
    native: dict[str, Any] = {
        "owner": repo.owner,
        "repo": repo.name,
        "path": path,
        "branch": branch,
    }
    return ProviderReference(
        input=raw,
        provider="github",
        kind="page",
        authority=authority,
        native=native,
        url=f"https://{authority}/{repo.owner}/{repo.name}/blob/{quote(branch, safe='')}/{quote(path, safe='/')}",
        display=path,
        ref=f"workflowref:github:page:{authority}/{repo.owner}/{repo.name}/{path}",
    )


def _parse_confluence_page(raw: str, config: WorkflowConfig, *, role: str | None) -> ProviderReference | None:
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None

    page_id: str | None = None
    title: str | None = None
    space: str | None = None

    match = CONFLUENCE_PAGE_PATH_RE.search(parsed.path)
    if match:
        page_id = match.group("page_id")
        space = _decode_url_segment(match.group("space"))
        if match.group("title"):
            title = _decode_url_segment(match.group("title"))
    elif parsed.path.endswith("/wiki/pages/viewpage.action"):
        page_ids = parse_qs(parsed.query).get("pageId")
        if page_ids:
            page_id = page_ids[0]

    if page_id is None:
        return None

    _ensure_provider_role(config, role, expected_role="knowledge", provider="confluence", raw=raw)
    authority = _normalize_authority(parsed.hostname)
    native: dict[str, Any] = {"page_id": page_id}
    if space:
        native["space"] = space
    configured_space = _string_setting(config.knowledge.settings, "space", "space_key")
    if configured_space and "space" not in native:
        native["space"] = configured_space
    space_id = _string_setting(config.knowledge.settings, "space_id")
    if space_id:
        native["space_id"] = space_id
    if title:
        native["title"] = title
    display = title or raw
    return ProviderReference(
        input=raw,
        provider="confluence",
        kind="page",
        authority=authority,
        native=native,
        url=raw,
        display=display,
        title=title,
        ref=f"workflowref:confluence:page:{authority}/{page_id}",
    )


def _confluence_display_reference(raw: str, config: WorkflowConfig) -> ProviderReference:
    _ensure_provider_role(config, "knowledge", expected_role="knowledge", provider="confluence", raw=raw)
    settings = config.knowledge.settings
    site = _authority_from_settings(settings, "site", "host", "hostname", "base_url", "url")
    if site is None:
        site = "confluence"
    authority = _normalize_authority(site)
    native: dict[str, Any] = {"title": raw}
    space = _string_setting(settings, "space", "space_key")
    if space:
        native["space"] = space
    space_id = _string_setting(settings, "space_id")
    if space_id:
        native["space_id"] = space_id
    return ProviderReference(
        input=raw,
        provider="confluence",
        kind="page",
        authority=authority,
        native=native,
        display=raw,
        title=raw,
    )


def _ensure_provider_role(
    config: WorkflowConfig,
    role: str | None,
    *,
    expected_role: str,
    provider: str,
    raw: str,
) -> None:
    target_role = role or expected_role
    if target_role != expected_role:
        raise ProviderReferenceMismatchError(
            f"reference '{raw}' is a {expected_role} reference, not a {target_role} reference"
        )
    configured_provider = config.provider_for_role(target_role)
    if configured_provider != provider:
        raise ProviderReferenceMismatchError(
            f"reference '{raw}' uses provider '{provider}', but configured {target_role} "
            f"provider is '{configured_provider}'"
        )


def _github_repo_for_role(
    config: WorkflowConfig,
    role: str,
    *,
    runner: CommandRunner | None,
) -> GitHubRepository:
    repo = _optional_github_repo_for_role(config, role, runner=runner)
    if repo is not None:
        return repo
    raise ProviderReferenceAmbiguityError(
        f"GitHub repository context is required to resolve {role} reference"
    )


def _optional_github_repo_for_role(
    config: WorkflowConfig,
    role: str,
    *,
    runner: CommandRunner | None,
) -> GitHubRepository | None:
    provider_config = config.issues if role == "issue" else config.knowledge
    repo = _github_repo_from_provider_config(provider_config)
    if repo is not None:
        return repo

    if role == "knowledge" and config.issues.kind == "github":
        repo = _github_repo_from_provider_config(config.issues)
        if repo is not None:
            return repo

    try:
        return resolve_github_repository(config.root, runner=runner)
    except (GitHubRepositoryError, WorkflowCommandError):
        return None


def _github_authority_for_role(
    config: WorkflowConfig,
    role: str,
    *,
    runner: CommandRunner | None,
) -> str:
    provider_config = config.issues if role == "issue" else config.knowledge
    authority = _authority_from_settings(provider_config.settings, "host", "hostname")
    if authority is not None:
        return authority

    repo = _optional_github_repo_for_role(config, role, runner=runner)
    if repo is not None:
        return _normalize_authority(repo.host)

    return "github.com"


def _github_repo_from_provider_config(provider_config: ProviderConfig) -> GitHubRepository | None:
    settings = provider_config.settings
    host = _authority_from_settings(settings, "host", "hostname") or "github.com"
    repo_slug = _string_setting(settings, "repo", "repository", "slug")
    owner = _string_setting(settings, "owner", "org", "organization")
    name = _string_setting(settings, "name", "repo_name", "repository_name")

    if repo_slug:
        if repo_slug.startswith(("http://", "https://", "ssh://", "git@")):
            return parse_github_remote_url(repo_slug)
        parts = repo_slug.strip("/").split("/")
        if len(parts) == 2:
            owner, name = parts
        elif len(parts) > 2:
            host = parts[0]
            owner = parts[-2]
            name = parts[-1]

    if not owner or not name:
        return None
    return GitHubRepository(host=_normalize_authority(host), owner=owner, name=name.removesuffix(".git"))


def _normalize_wiki_path(path: str) -> str:
    normalized = PurePosixPath(path).as_posix().lstrip("/")
    parts = PurePosixPath(normalized).parts
    if len(parts) < 3 or parts[0] != "wiki" or any(part in {"", ".", ".."} for part in parts):
        raise ProviderReferenceAmbiguityError(f"invalid GitHub wiki page path: {path}")
    return normalized


def _same_github_repo(left: GitHubRepository, right: GitHubRepository) -> bool:
    return (
        left.host.lower(),
        left.owner.lower(),
        left.name.removesuffix(".git").lower(),
    ) == (
        right.host.lower(),
        right.owner.lower(),
        right.name.removesuffix(".git").lower(),
    )


def _authority_from_settings(settings: Mapping[str, Any], *keys: str) -> str | None:
    value = _string_setting(settings, *keys)
    if value is None:
        return None
    return _normalize_authority(value)


def _string_setting(settings: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = settings.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _normalize_authority(value: str) -> str:
    text = value.strip()
    parsed = urlparse(text if "://" in text else f"https://{text}")
    authority = parsed.netloc or parsed.path.split("/", 1)[0]
    return authority.strip("/").lower()


def _decode_url_segment(value: str) -> str:
    return unquote(value).replace("+", " ")
