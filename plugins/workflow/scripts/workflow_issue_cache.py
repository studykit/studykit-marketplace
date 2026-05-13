#!/usr/bin/env python3
"""Shared GitHub issue reference parsing and workflow cache fetch helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from workflow_cache import GitHubIssueCache
from workflow_command import CommandRunner
from workflow_config import WorkflowConfig
from workflow_github import GitHubRepository, normalize_issue_number
from workflow_providers import CACHE_POLICY_DEFAULT, ProviderDispatcher, default_provider_registry
from workflow_providers import request_from_config

MAX_ISSUE_REFS = 20

ISSUE_HASH_RE = re.compile(r"(?<![\w#])#([1-9]\d*)\b")
ISSUE_REPO_RE = re.compile(
    r"(?<![\w/.-])(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)#(?P<num>[1-9]\d*)\b",
    re.IGNORECASE,
)
ISSUE_URL_RE = re.compile(
    r"https?://(?P<host>[^/\s]+)/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/issues/(?P<num>[1-9]\d*)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class IssueCacheContext:
    """Concise context for one cache-aware GitHub issue read."""

    number: str
    relative_issue_dir: str
    title: str
    state: str
    cache_hit: bool | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "issue": self.number,
            "relative_issue_dir": self.relative_issue_dir,
            "title": self.title,
            "state": self.state,
            "cache_hit": self.cache_hit,
        }


def issue_numbers_from_references(
    references: Sequence[str],
    *,
    repo: GitHubRepository | None = None,
    issue_id_format: str = "github",
    allow_bare_numbers: bool = True,
    max_refs: int = MAX_ISSUE_REFS,
) -> list[str]:
    """Extract unique issue numbers from explicit shell-tool references."""

    numbers: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        if len(numbers) >= max_refs:
            return
        try:
            normalized = normalize_issue_number(raw)
        except Exception:
            return
        if normalized in seen:
            return
        seen.add(normalized)
        numbers.append(normalized)

    for reference in references:
        if allow_bare_numbers:
            before = len(numbers)
            add(reference)
            if len(numbers) > before:
                continue
        for number in extract_issue_numbers(
            reference,
            repo=repo,
            issue_id_format=issue_id_format,
            max_refs=max_refs - len(numbers),
        ):
            add(number)

    return numbers


def extract_issue_numbers(
    text: str,
    *,
    repo: GitHubRepository | None = None,
    issue_id_format: str = "github",
    max_refs: int = MAX_ISSUE_REFS,
) -> list[str]:
    """Extract same-repository issue references in first-seen order."""

    if issue_id_format != "github":
        return []

    numbers: list[str] = []
    seen: set[str] = set()
    candidates: list[tuple[int, str]] = []

    def add(raw: str) -> None:
        if len(numbers) >= max_refs:
            return
        try:
            normalized = normalize_issue_number(raw)
        except Exception:
            return
        if normalized in seen:
            return
        seen.add(normalized)
        numbers.append(normalized)

    for match in ISSUE_URL_RE.finditer(text):
        if repo is not None and not same_github_repo(
            repo,
            host=match.group("host"),
            owner=match.group("owner"),
            repo_name=match.group("repo"),
        ):
            continue
        candidates.append((match.start(), match.group("num")))

    for match in ISSUE_REPO_RE.finditer(text):
        if repo is not None and not same_github_repo(
            repo,
            host=repo.host,
            owner=match.group("owner"),
            repo_name=match.group("repo"),
        ):
            continue
        candidates.append((match.start(), match.group("num")))

    for match in ISSUE_HASH_RE.finditer(text):
        candidates.append((match.start(), match.group(1)))

    for _, raw in sorted(candidates, key=lambda item: item[0]):
        add(raw)

    return numbers


def cache_issue_references(
    config: WorkflowConfig,
    issue_numbers: Sequence[str],
    *,
    repo: GitHubRepository,
    cache_policy: str = CACHE_POLICY_DEFAULT,
    runner: CommandRunner | None = None,
    strict: bool = False,
) -> list[IssueCacheContext]:
    """Read issues through the provider cache path and return cache context."""

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))
    cache = GitHubIssueCache.for_project(config.root, configured_repo=repo)
    issue_base = github_issue_cache_base(config, repo)
    contexts: list[IssueCacheContext] = []

    for number in issue_numbers:
        try:
            normalized = normalize_issue_number(number)
            request = request_from_config(
                config,
                role="issue",
                operation="get",
                artifact_type="task",
                payload={
                    "issue": normalized,
                    "include_body": False,
                    "include_comments": False,
                    "include_relationships": False,
                },
                cache_policy=cache_policy,
            )
            response = dispatcher.dispatch(request)
            issue_dir = cache.issue_dir(repo, normalized)
            relative_issue_dir = issue_dir.relative_to(issue_base).as_posix() + "/"
            contexts.append(
                IssueCacheContext(
                    number=normalized,
                    relative_issue_dir=relative_issue_dir,
                    title=str(response.payload.get("title") or ""),
                    state=str(response.payload.get("state") or "").upper(),
                    cache_hit=cache_hit_from_payload(response.payload, default=False),
                )
            )
        except Exception:
            if strict:
                raise
            continue

    return contexts


def github_issue_cache_base(config: WorkflowConfig, repo: GitHubRepository) -> Path:
    """Return the issue-number parent directory for the configured repo cache."""

    cache = GitHubIssueCache.for_project(config.root, configured_repo=repo)
    return cache.issue_dir(repo, "1").parent


def cache_hit_from_payload(payload: Mapping[str, Any], *, default: bool | None = None) -> bool | None:
    cache_data = payload.get("cache")
    if isinstance(cache_data, Mapping):
        hit = cache_data.get("hit")
        if isinstance(hit, bool):
            return hit
    return default


def format_issue_cache_context(contexts: Sequence[IssueCacheContext]) -> str:
    """Render issue cache context using issue-cache-base-relative paths."""

    lines = ["Workflow issue cache:"]
    for context in contexts:
        details: list[str] = []
        state = context.state.strip()
        if state:
            details.append(state.lower())
        title = compact_title(context.title)
        if title:
            details.append(title)
        suffix = f" — {' — '.join(details)}" if details else ""
        lines.append(f"- #{context.number} → `{context.relative_issue_dir}`{suffix}")
    return "\n".join(lines)


def format_issue_cache_json(
    contexts: Sequence[IssueCacheContext],
    *,
    config: WorkflowConfig,
    repo: GitHubRepository,
    cache_policy: str,
) -> dict[str, Any]:
    """Build compact JSON for agent-facing cache fetch output."""

    return {
        "operation": "cache_fetch",
        "role": "issue",
        "kind": "github",
        "repository": repo.to_json(),
        "cache_policy": cache_policy,
        "cache_base": display_project_path(github_issue_cache_base(config, repo), config.root, trailing_slash=True),
        "issues": [context.to_json() for context in contexts],
    }


def compact_title(value: str, *, limit: int = 96) -> str:
    title = " ".join(value.split())
    if len(title) <= limit:
        return title
    return title[: limit - 1].rstrip() + "…"


def display_project_path(path: Path, project: Path, *, trailing_slash: bool = False) -> str:
    resolved = path.expanduser().resolve(strict=False)
    try:
        display = resolved.relative_to(project.expanduser().resolve(strict=False)).as_posix()
    except ValueError:
        display = str(resolved)
    if trailing_slash and not display.endswith("/"):
        display += "/"
    return display


def same_github_repo(
    repo: GitHubRepository,
    *,
    host: str,
    owner: str,
    repo_name: str,
) -> bool:
    return (
        host.lower(),
        owner.lower(),
        repo_name.removesuffix(".git").lower(),
    ) == (
        repo.host.lower(),
        repo.owner.lower(),
        repo.name.lower(),
    )
