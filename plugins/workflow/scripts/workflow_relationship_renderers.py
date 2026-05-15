#!/usr/bin/env python3
"""Provider-specific renderers for cached workflow relationship projections."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from workflow_github import normalize_issue_number


_GITHUB_PARENT_KEY = "parent"
_GITHUB_CHILDREN_KEY = "children"
_GITHUB_DEPENDENCIES_KEY = "dependencies"
_GITHUB_BLOCKED_BY_KEY = "blocked_by"
_GITHUB_BLOCKING_KEY = "blocking"
_GITHUB_RELATED_KEY = "related"


def render_relationship_summary(
    provider_kind: str | None,
    relationships: Mapping[str, Any],
) -> str:
    """Dispatch relationship summary rendering by issue provider kind.

    Returns an empty string for unsupported or missing provider kinds so the
    issue cache context path can omit the relationship suffix without guessing
    at another provider's schema.
    """

    if provider_kind == "github":
        return render_github_relationship_summary(relationships)
    if provider_kind == "jira":
        return render_jira_relationship_summary(relationships)
    return ""


def render_github_relationship_summary(relationships: Mapping[str, Any]) -> str:
    """Render a compact summary from the normalized GitHub `relationships.yml` schema.

    Reads only `parent`, `children`, `dependencies.blocked_by`, `dependencies.blocking`,
    and `related`. Pending-authoring aliases (`blocked`, `blocks`, `blockedBy`,
    `depends_on`) are not accepted at render time.
    """

    if not isinstance(relationships, Mapping):
        return ""

    parts: list[str] = []

    parent = _relationship_numbers(relationships.get(_GITHUB_PARENT_KEY))
    if parent:
        parts.append(f"parent {_format_issue_numbers(parent)}")

    children = _relationship_numbers(relationships.get(_GITHUB_CHILDREN_KEY))
    if children:
        parts.append(f"children {_format_issue_numbers(children)}")

    dependencies = relationships.get(_GITHUB_DEPENDENCIES_KEY)
    if isinstance(dependencies, Mapping):
        blocked_by = _relationship_numbers(dependencies.get(_GITHUB_BLOCKED_BY_KEY))
        if blocked_by:
            parts.append(f"blocked_by {_format_issue_numbers(blocked_by)}")
        blocking = _relationship_numbers(dependencies.get(_GITHUB_BLOCKING_KEY))
        if blocking:
            parts.append(f"blocking {_format_issue_numbers(blocking)}")

    related = _relationship_numbers(relationships.get(_GITHUB_RELATED_KEY))
    if related:
        parts.append(f"related {_format_issue_numbers(related)}")

    return "; ".join(parts)


def render_jira_relationship_summary(relationships: Mapping[str, Any]) -> str:
    """Render a compact summary from the Jira `relationships.workflow` projection."""

    if not isinstance(relationships, Mapping):
        return ""
    workflow = relationships.get("workflow")
    if not isinstance(workflow, Mapping):
        return ""

    parts: list[str] = []

    parent = _relationship_keys(workflow.get("parent"))
    if parent:
        parts.append(f"parent {_format_jira_keys(parent)}")

    children = _relationship_keys(workflow.get("children"))
    if children:
        parts.append(f"children {_format_jira_keys(children)}")

    dependencies = workflow.get("dependencies")
    if isinstance(dependencies, Mapping):
        blocked_by = _relationship_keys(dependencies.get("blocked_by"))
        if blocked_by:
            parts.append(f"blocked_by {_format_jira_keys(blocked_by)}")
        blocking = _relationship_keys(dependencies.get("blocking"))
        if blocking:
            parts.append(f"blocking {_format_jira_keys(blocking)}")

    related = _relationship_keys(workflow.get("related"))
    if related:
        parts.append(f"related {_format_jira_keys(related)}")

    external_links = workflow.get("external_links")
    if isinstance(external_links, list) and external_links:
        parts.append(f"external_links {len(external_links)}")

    return "; ".join(parts)


def _relationship_numbers(value: Any) -> list[str]:
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


def _format_issue_numbers(numbers: Sequence[str], *, limit: int = 5) -> str:
    visible = [f"#{number}" for number in numbers[:limit]]
    if len(numbers) > limit:
        visible.append(f"+{len(numbers) - limit}")
    return ",".join(visible)


def _relationship_keys(value: Any) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()

    def add(raw: Any) -> None:
        if raw is None:
            return
        text = str(raw).strip()
        if not text or text in seen:
            return
        seen.add(text)
        keys.append(text)

    def visit(item: Any) -> None:
        if item is None:
            return
        if isinstance(item, Mapping):
            for key in ("key", "issue"):
                if key in item:
                    add(item.get(key))
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
    return keys


def _format_jira_keys(keys: Sequence[str], *, limit: int = 5) -> str:
    visible = list(keys[:limit])
    if len(keys) > limit:
        visible.append(f"+{len(keys) - limit}")
    return ",".join(visible)
