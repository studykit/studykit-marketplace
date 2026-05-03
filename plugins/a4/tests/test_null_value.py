"""Frontmatter `null-value` rule.

Covers the cross-cutting null check in
``markdown_validator.frontmatter.validate_file``: any frontmatter key
whose value parses to YAML null (``null``, ``~``, or an empty scalar
like ``parent:`` followed by nothing) is rejected. Same rule applies to
``None`` items appearing inside a list. Authors must omit the key,
supply a value, or write ``[]`` for an explicitly empty list.
"""

from __future__ import annotations

from pathlib import Path

from conftest import A4Workspace


def _run_violations(a4_root: Path):
    from markdown_validator import frontmatter as vfm

    violations, _ = vfm.run(a4_root, None)
    return violations


def _has(violations, *, path: str, rule: str, field: str) -> bool:
    return any(
        v.path == path and v.rule == rule and v.field == field for v in violations
    )


def test_parent_null_rejected(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("task", 1, "t", parent=None)

    violations = _run_violations(a4_workspace.root)

    assert _has(violations, path="task/1-t.md", rule="null-value", field="parent")


def test_parent_omitted_passes(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("task", 1, "t")

    violations = _run_violations(a4_workspace.root)

    assert not any(
        v.path == "task/1-t.md" and v.rule == "null-value" for v in violations
    )


def test_list_field_null_entry_rejected(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("task", 1, "t", depends_on=[None])

    violations = _run_violations(a4_workspace.root)

    assert _has(
        violations, path="task/1-t.md", rule="null-value", field="depends_on"
    )


def test_empty_list_passes(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("task", 1, "t", depends_on=[])

    violations = _run_violations(a4_workspace.root)

    assert not any(
        v.path == "task/1-t.md" and v.rule == "null-value" for v in violations
    )


def test_unknown_field_null_rejected(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("task", 1, "t", labels=None)

    violations = _run_violations(a4_workspace.root)

    assert _has(
        violations, path="task/1-t.md", rule="null-value", field="labels"
    )
