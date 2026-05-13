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
    issue_dir: str
    title: str
    state: str
    cache_hit: bool | None = None
    relationship_summary: str = ""

    def to_json(self) -> dict[str, Any]:
        payload = {
            "issue": self.number,
            "issue_dir": self.issue_dir,
            "title": self.title,
            "state": self.state,
            "cache_hit": self.cache_hit,
        }
        if self.relationship_summary:
            payload["relationships"] = self.relationship_summary
        return payload


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
            project_issue_dir = display_project_path(issue_dir, config.root, trailing_slash=True)
            relationship_summary = cached_relationship_summary(cache, repo, normalized)
            contexts.append(
                IssueCacheContext(
                    number=normalized,
                    issue_dir=project_issue_dir,
                    title=str(response.payload.get("title") or ""),
                    state=str(response.payload.get("state") or "").upper(),
                    cache_hit=cache_hit_from_payload(response.payload, default=False),
                    relationship_summary=relationship_summary,
                )
            )
        except Exception:
            if strict:
                raise
            continue

    return contexts


def cache_hit_from_payload(payload: Mapping[str, Any], *, default: bool | None = None) -> bool | None:
    cache_data = payload.get("cache")
    if isinstance(cache_data, Mapping):
        hit = cache_data.get("hit")
        if isinstance(hit, bool):
            return hit
    return default


def format_issue_cache_context(
    contexts: Sequence[IssueCacheContext],
    *,
    include_details: bool = True,
) -> str:
    """Render issue cache context using project-relative cache issue files."""

    _ = include_details
    shared_base = shared_issue_dir_base(contexts)
    if shared_base is None:
        lines = ["Workflow issue cache:"]
    else:
        lines = [f"Workflow issue cache: `{shared_base}`"]
    for context in contexts:
        issue_path = issue_file_relative_to_base(context, shared_base)
        relationship_suffix = f" — {context.relationship_summary}" if context.relationship_summary else ""
        lines.append(f"- #{context.number} → `{issue_path}`{relationship_suffix}")
    return "\n".join(lines)


def cached_relationship_summary(cache: GitHubIssueCache, repo: GitHubRepository, issue: str) -> str:
    """Read cached relationships and return a compact relationship summary."""

    try:
        relationships = cache.read_relationships(repo, issue)
    except Exception:
        return ""
    return compact_relationship_summary(relationships)


def compact_relationship_summary(relationships: Mapping[str, Any]) -> str:
    """Render relationship YAML as compact issue-reference groups."""

    parts: list[str] = []
    parent = relationship_numbers(relationships.get("parent"))
    if parent:
        parts.append(f"parent {format_issue_numbers(parent)}")

    children = relationship_numbers(relationships.get("children"))
    if children:
        parts.append(f"children {format_issue_numbers(children)}")

    dependencies = relationships.get("dependencies")
    if isinstance(dependencies, Mapping):
        blocked_by = relationship_numbers(dependencies.get("blocked_by"))
        if blocked_by:
            parts.append(f"blocked_by {format_issue_numbers(blocked_by)}")
        blocking = relationship_numbers(dependencies.get("blocking"))
        if blocking:
            parts.append(f"blocking {format_issue_numbers(blocking)}")

    related = relationship_numbers(relationships.get("related"))
    if related:
        parts.append(f"related {format_issue_numbers(related)}")

    return "; ".join(parts)


def relationship_numbers(value: Any) -> list[str]:
    """Extract issue numbers from normalized relationship cache values."""

    numbers: list[str] = []
    seen: set[str] = set()

    def add(raw: Any) -> None:
        try:
            normalized = normalize_issue_number(raw)
        except Exception:
            return
        if normalized in seen:
            return
        seen.add(normalized)
        numbers.append(normalized)

    def visit(item: Any) -> None:
        if item is None:
            return
        if isinstance(item, Mapping):
            if "number" in item:
                add(item.get("number"))
                return
            if "issue" in item:
                add(item.get("issue"))
                return
            nodes = item.get("nodes")
            if isinstance(nodes, list):
                for node in nodes:
                    visit(node)
            return
        if isinstance(item, list | tuple | set):
            for child in item:
                visit(child)
            return
        add(item)

    visit(value)
    return numbers


def format_issue_numbers(numbers: Sequence[str], *, limit: int = 5) -> str:
    visible = [f"#{number}" for number in numbers[:limit]]
    if len(numbers) > limit:
        visible.append(f"+{len(numbers) - limit}")
    return ",".join(visible)


def shared_issue_dir_base(contexts: Sequence[IssueCacheContext]) -> str | None:
    """Return a shared issue directory prefix for multi-issue displays."""

    if len(contexts) <= 1:
        return None

    bases: list[str] = []
    for context in contexts:
        issue_dir = ensure_trailing_slash(context.issue_dir.strip())
        suffix = f"{context.number}/"
        if not issue_dir.endswith(suffix):
            return None
        bases.append(issue_dir[: -len(suffix)])

    if not bases:
        return None
    first = bases[0]
    if not first or any(base != first for base in bases):
        return None
    return first


def issue_file_relative_to_base(context: IssueCacheContext, base: str | None) -> str:
    issue_dir = ensure_trailing_slash(context.issue_dir.strip())
    issue_file = f"{issue_dir}issue.md"
    if base is None or not issue_dir.startswith(base):
        return issue_file
    relative = f"{issue_dir[len(base) :]}issue.md"
    return relative or issue_file


def ensure_trailing_slash(value: str) -> str:
    if not value or value.endswith("/"):
        return value
    return f"{value}/"


def format_issue_cache_json(
    contexts: Sequence[IssueCacheContext],
    *,
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
        "issues": [context.to_json() for context in contexts],
    }


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
