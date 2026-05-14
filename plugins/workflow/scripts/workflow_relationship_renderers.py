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
