"""Frontmatter `parent:` target-type and self-reference checks.

Covers `_validate_parent_target` in
``markdown_validator.frontmatter``:

  - issue-family files (task / bug / spike / research) accept any
    issue-family parent or an umbrella parent (cross-type allowed);
  - usecase and spec accept same-type parents only;
  - any file's `parent:` pointing at itself is a self-reference error.
"""

from __future__ import annotations

from pathlib import Path

from conftest import A4Workspace


def _run_violations(a4_root: Path):
    from markdown_validator import frontmatter as vfm

    violations, _ = vfm.run(a4_root, None)
    return violations


def _has(violations, *, path: str, rule: str) -> bool:
    return any(v.path == path and v.rule == rule for v in violations)


def test_task_with_spike_parent_allowed(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("spike", 1, "explore")
    a4_workspace.write("task", 2, "follow", parent="spike/1-explore")

    violations = _run_violations(a4_workspace.root)

    assert not _has(violations, path="task/2-follow.md", rule="parent-target-type")


def test_task_with_umbrella_parent_allowed(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("umbrella", 1, "search")
    a4_workspace.write("task", 2, "list", parent="umbrella/1-search")

    violations = _run_violations(a4_workspace.root)

    assert not _has(violations, path="task/2-list.md", rule="parent-target-type")


def test_bug_with_task_parent_allowed(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("task", 1, "feature")
    a4_workspace.write("bug", 2, "regression", parent="task/1-feature")

    violations = _run_violations(a4_workspace.root)

    assert not _has(violations, path="bug/2-regression.md", rule="parent-target-type")


def test_usecase_with_task_parent_rejected(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("task", 1, "impl")
    a4_workspace.write("usecase", 2, "uc", parent="task/1-impl")

    violations = _run_violations(a4_workspace.root)

    assert _has(violations, path="usecase/2-uc.md", rule="parent-target-type")


def test_usecase_with_usecase_parent_allowed(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("usecase", 1, "uc-a")
    a4_workspace.write("usecase", 2, "uc-b", parent="usecase/1-uc-a")

    violations = _run_violations(a4_workspace.root)

    assert not _has(violations, path="usecase/2-uc-b.md", rule="parent-target-type")


def test_spec_with_spec_parent_allowed(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("spec", 1, "spec-a")
    a4_workspace.write("spec", 2, "spec-b", parent="spec/1-spec-a")

    violations = _run_violations(a4_workspace.root)

    assert not _has(violations, path="spec/2-spec-b.md", rule="parent-target-type")


def test_spec_with_task_parent_rejected(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("task", 1, "impl")
    a4_workspace.write("spec", 2, "decision", parent="task/1-impl")

    violations = _run_violations(a4_workspace.root)

    assert _has(violations, path="spec/2-decision.md", rule="parent-target-type")


def test_task_self_reference_rejected(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("task", 1, "self", parent="task/1-self")

    violations = _run_violations(a4_workspace.root)

    assert _has(violations, path="task/1-self.md", rule="parent-self-reference")


def test_research_with_research_parent_allowed(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("research", 1, "topic-a")
    a4_workspace.write("research", 2, "topic-b", parent="research/1-topic-a")

    violations = _run_violations(a4_workspace.root)

    assert not _has(violations, path="research/2-topic-b.md", rule="parent-target-type")
