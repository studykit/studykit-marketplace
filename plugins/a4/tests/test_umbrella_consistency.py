"""Umbrella `## Children` ↔ reverse-`parent:` consistency + drift checks.

Covers ``markdown_validator.umbrella_consistency``:

  - ``umbrella-child-not-listed`` — `parent:` points at the umbrella but
    the umbrella body's `## Children` section omits the child;
  - ``umbrella-stale-listing`` — the body lists a child that no file
    points at via `parent:` (annotated bullets do not count);
  - ``umbrella-children-all-terminal`` (warning) — open umbrella, every
    child at family-terminal status (`complete` / `discarded`).
"""

from __future__ import annotations

from pathlib import Path

from conftest import A4Workspace


_UMBRELLA_BODY_HEADER = "## Description\nx\n\n## Children\n"
_UMBRELLA_BODY_FOOTER = "\n## Log\n- ok\n"


def _umbrella_body(children_lines: list[str]) -> str:
    bullets = "\n".join(children_lines) if children_lines else "- (none yet)"
    return f"{_UMBRELLA_BODY_HEADER}{bullets}{_UMBRELLA_BODY_FOOTER}"


def _run_mismatches(a4_root: Path):
    from markdown_validator import umbrella_consistency as vuc

    return vuc.run(a4_root, None)


def _has(mismatches, *, path: str, rule: str) -> bool:
    return any(m.path == path and m.rule == rule for m in mismatches)


def _by_rule(mismatches, rule: str) -> list:
    return [m for m in mismatches if m.rule == rule]


def test_clean_umbrella_no_drift(a4_workspace: A4Workspace) -> None:
    a4_workspace.write(
        "umbrella",
        1,
        "u",
        body=_umbrella_body(["- 2026-04-23 09:14 `../task/2-foo.md`"]),
    )
    a4_workspace.write("task", 2, "foo", parent="umbrella/1-u")

    mismatches = _run_mismatches(a4_workspace.root)

    assert mismatches == []


def test_child_not_listed_in_body(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("umbrella", 1, "u", body=_umbrella_body([]))
    a4_workspace.write("task", 2, "foo", parent="umbrella/1-u")

    mismatches = _run_mismatches(a4_workspace.root)

    assert _has(mismatches, path="umbrella/1-u.md", rule="umbrella-child-not-listed")
    assert not _has(mismatches, path="umbrella/1-u.md", rule="umbrella-stale-listing")


def test_body_lists_child_with_no_parent_pointer(
    a4_workspace: A4Workspace,
) -> None:
    a4_workspace.write(
        "umbrella",
        1,
        "u",
        body=_umbrella_body(["- 2026-04-23 09:14 `../task/2-foo.md`"]),
    )
    a4_workspace.write("task", 2, "foo")  # no parent

    mismatches = _run_mismatches(a4_workspace.root)

    assert _has(mismatches, path="umbrella/1-u.md", rule="umbrella-stale-listing")


def test_annotated_bullet_not_treated_as_active(
    a4_workspace: A4Workspace,
) -> None:
    a4_workspace.write(
        "umbrella",
        1,
        "u",
        body=_umbrella_body(
            [
                "- 2026-04-23 09:14 `../task/2-foo.md` — moved to umbrella/9-other 2026-05-08 14:32"
            ]
        ),
    )
    a4_workspace.write("task", 2, "foo")  # no parent

    mismatches = _run_mismatches(a4_workspace.root)

    # Annotated entry is historical — must not trigger stale-listing.
    assert _by_rule(mismatches, "umbrella-stale-listing") == []


def test_drift_warning_open_umbrella_all_terminal_children(
    a4_workspace: A4Workspace,
) -> None:
    a4_workspace.write(
        "umbrella",
        1,
        "u",
        status="open",
        body=_umbrella_body(
            [
                "- 2026-04-23 09:14 `../task/2-a.md`",
                "- 2026-04-25 14:02 `../task/3-b.md`",
            ]
        ),
    )
    a4_workspace.write(
        "task", 2, "a", status="complete", parent="umbrella/1-u"
    )
    a4_workspace.write(
        "task", 3, "b", status="discarded", parent="umbrella/1-u"
    )

    mismatches = _run_mismatches(a4_workspace.root)

    drift = _by_rule(mismatches, "umbrella-children-all-terminal")
    assert len(drift) == 1
    assert drift[0].severity == "warning"


def test_drift_silent_when_umbrella_has_no_children(
    a4_workspace: A4Workspace,
) -> None:
    a4_workspace.write("umbrella", 1, "u", status="open", body=_umbrella_body([]))

    mismatches = _run_mismatches(a4_workspace.root)

    assert _by_rule(mismatches, "umbrella-children-all-terminal") == []


def test_drift_silent_when_one_child_non_terminal(
    a4_workspace: A4Workspace,
) -> None:
    a4_workspace.write(
        "umbrella",
        1,
        "u",
        status="open",
        body=_umbrella_body(["- 2026-04-23 09:14 `../task/2-a.md`"]),
    )
    a4_workspace.write(
        "task", 2, "a", status="progress", parent="umbrella/1-u"
    )

    mismatches = _run_mismatches(a4_workspace.root)

    assert _by_rule(mismatches, "umbrella-children-all-terminal") == []


def test_drift_silent_when_umbrella_already_complete(
    a4_workspace: A4Workspace,
) -> None:
    a4_workspace.write(
        "umbrella",
        1,
        "u",
        status="complete",
        body=_umbrella_body(["- 2026-04-23 09:14 `../task/2-a.md`"]),
    )
    a4_workspace.write(
        "task", 2, "a", status="complete", parent="umbrella/1-u"
    )

    mismatches = _run_mismatches(a4_workspace.root)

    assert _by_rule(mismatches, "umbrella-children-all-terminal") == []
