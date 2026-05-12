"""Epic frontmatter schema checks.

Covers the `epic` schema in ``markdown_validator.frontmatter``:

  - required fields are enforced;
  - `implements` / `spec` / `depends_on` / `artifacts` / `cycle` /
    `parent` are forbidden — any non-empty declaration is a
    `type-field-forbidden` violation;
  - empty declarations of forbidden fields are tolerated (parity with
    other types' shape rules).
"""

from __future__ import annotations

from pathlib import Path

from conftest import A4Workspace


def _run_violations(a4_root: Path):
    from markdown_validator import frontmatter as vfm

    violations, _ = vfm.run(a4_root, None)
    return violations


def _has(violations, *, path: str, rule: str, field: str | None = None) -> bool:
    for v in violations:
        if v.path != path or v.rule != rule:
            continue
        if field is not None and v.field != field:
            continue
        return True
    return False


def test_minimal_valid_epic(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("epic", 1, "ok")

    violations = _run_violations(a4_workspace.root)

    file_violations = [v for v in violations if v.path == "epic/1-ok.md"]
    assert file_violations == []


def test_epic_implements_forbidden(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("usecase", 5, "x")
    a4_workspace.write("epic", 1, "x", implements=["usecase/5-x"])

    violations = _run_violations(a4_workspace.root)

    assert _has(
        violations,
        path="epic/1-x.md",
        rule="type-field-forbidden",
        field="implements",
    )


def test_epic_spec_forbidden(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("spec", 5, "decision")
    a4_workspace.write("epic", 1, "x", spec=["spec/5-decision"])

    violations = _run_violations(a4_workspace.root)

    assert _has(
        violations,
        path="epic/1-x.md",
        rule="type-field-forbidden",
        field="spec",
    )


def test_epic_depends_on_forbidden(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("task", 5, "dep")
    a4_workspace.write("epic", 1, "x", depends_on=["task/5-dep"])

    violations = _run_violations(a4_workspace.root)

    assert _has(
        violations,
        path="epic/1-x.md",
        rule="type-field-forbidden",
        field="depends_on",
    )


def test_epic_artifacts_forbidden(a4_workspace: A4Workspace) -> None:
    a4_workspace.write(
        "epic",
        1,
        "x",
        artifacts=["artifacts/epic/1-x/note.md"],
    )

    violations = _run_violations(a4_workspace.root)

    assert _has(
        violations,
        path="epic/1-x.md",
        rule="type-field-forbidden",
        field="artifacts",
    )


def test_epic_cycle_forbidden(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("epic", 1, "x", cycle=2)

    violations = _run_violations(a4_workspace.root)

    assert _has(
        violations,
        path="epic/1-x.md",
        rule="type-field-forbidden",
        field="cycle",
    )


def test_epic_parent_forbidden(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("epic", 5, "outer")
    a4_workspace.write("epic", 1, "inner", parent="epic/5-outer")

    violations = _run_violations(a4_workspace.root)

    assert _has(
        violations,
        path="epic/1-inner.md",
        rule="type-field-forbidden",
        field="parent",
    )


def test_epic_empty_forbidden_fields_tolerated(
    a4_workspace: A4Workspace,
) -> None:
    a4_workspace.write(
        "epic",
        1,
        "x",
        implements=[],
        depends_on=[],
        spec=[],
        artifacts=[],
    )

    violations = _run_violations(a4_workspace.root)

    forbidden = [
        v
        for v in violations
        if v.path == "epic/1-x.md" and v.rule == "type-field-forbidden"
    ]
    assert forbidden == []
