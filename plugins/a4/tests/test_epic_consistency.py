"""Epic `## Children` ↔ reverse-`parent:` consistency + drift checks.

Covers ``markdown_validator.epic_consistency``:

  - ``epic-child-not-listed`` — `parent:` points at the epic but
    the epic body's `## Children` section omits the child;
  - ``epic-stale-listing`` — the body lists a child that no file
    points at via `parent:` (annotated bullets do not count);
  - ``epic-children-all-terminal`` (warning) — open epic, every
    child at family-terminal status (`done` / `discarded`).
"""

from __future__ import annotations

from pathlib import Path

from conftest import A4Workspace


_EPIC_BODY_HEADER = "## Description\nx\n\n## Children\n"
_EPIC_BODY_FOOTER = "\n## Log\n- ok\n"


def _epic_body(children_lines: list[str]) -> str:
    bullets = "\n".join(children_lines) if children_lines else "- (none yet)"
    return f"{_EPIC_BODY_HEADER}{bullets}{_EPIC_BODY_FOOTER}"


def _run_mismatches(a4_root: Path):
    from markdown_validator import epic_consistency as vuc

    return vuc.run(a4_root, None)


def _has(mismatches, *, path: str, rule: str) -> bool:
    return any(m.path == path and m.rule == rule for m in mismatches)


def _by_rule(mismatches, rule: str) -> list:
    return [m for m in mismatches if m.rule == rule]


def test_clean_epic_no_drift(a4_workspace: A4Workspace) -> None:
    a4_workspace.write(
        "epic",
        1,
        "u",
        body=_epic_body(["- 2026-04-23 09:14 `../task/2-foo.md`"]),
    )
    a4_workspace.write("task", 2, "foo", parent="epic/1-u")

    mismatches = _run_mismatches(a4_workspace.root)

    assert mismatches == []


def test_child_not_listed_in_body(a4_workspace: A4Workspace) -> None:
    a4_workspace.write("epic", 1, "u", body=_epic_body([]))
    a4_workspace.write("task", 2, "foo", parent="epic/1-u")

    mismatches = _run_mismatches(a4_workspace.root)

    assert _has(mismatches, path="epic/1-u.md", rule="epic-child-not-listed")
    assert not _has(mismatches, path="epic/1-u.md", rule="epic-stale-listing")


def test_body_lists_child_with_no_parent_pointer(
    a4_workspace: A4Workspace,
) -> None:
    a4_workspace.write(
        "epic",
        1,
        "u",
        body=_epic_body(["- 2026-04-23 09:14 `../task/2-foo.md`"]),
    )
    a4_workspace.write("task", 2, "foo")  # no parent

    mismatches = _run_mismatches(a4_workspace.root)

    assert _has(mismatches, path="epic/1-u.md", rule="epic-stale-listing")


def test_annotated_bullet_not_treated_as_active(
    a4_workspace: A4Workspace,
) -> None:
    a4_workspace.write(
        "epic",
        1,
        "u",
        body=_epic_body(
            [
                "- 2026-04-23 09:14 `../task/2-foo.md` — moved to epic/9-other 2026-05-08 14:32"
            ]
        ),
    )
    a4_workspace.write("task", 2, "foo")  # no parent

    mismatches = _run_mismatches(a4_workspace.root)

    # Annotated entry is historical — must not trigger stale-listing.
    assert _by_rule(mismatches, "epic-stale-listing") == []


def test_drift_warning_open_epic_all_terminal_children(
    a4_workspace: A4Workspace,
) -> None:
    a4_workspace.write(
        "epic",
        1,
        "u",
        status="open",
        body=_epic_body(
            [
                "- 2026-04-23 09:14 `../task/2-a.md`",
                "- 2026-04-25 14:02 `../task/3-b.md`",
            ]
        ),
    )
    a4_workspace.write(
        "task", 2, "a", status="done", parent="epic/1-u"
    )
    a4_workspace.write(
        "task", 3, "b", status="discarded", parent="epic/1-u"
    )

    mismatches = _run_mismatches(a4_workspace.root)

    drift = _by_rule(mismatches, "epic-children-all-terminal")
    assert len(drift) == 1
    assert drift[0].severity == "warning"


def test_drift_silent_when_epic_has_no_children(
    a4_workspace: A4Workspace,
) -> None:
    a4_workspace.write("epic", 1, "u", status="open", body=_epic_body([]))

    mismatches = _run_mismatches(a4_workspace.root)

    assert _by_rule(mismatches, "epic-children-all-terminal") == []


def test_drift_silent_when_one_child_non_terminal(
    a4_workspace: A4Workspace,
) -> None:
    a4_workspace.write(
        "epic",
        1,
        "u",
        status="open",
        body=_epic_body(["- 2026-04-23 09:14 `../task/2-a.md`"]),
    )
    a4_workspace.write(
        "task", 2, "a", status="progress", parent="epic/1-u"
    )

    mismatches = _run_mismatches(a4_workspace.root)

    assert _by_rule(mismatches, "epic-children-all-terminal") == []


def test_drift_silent_when_epic_already_done(
    a4_workspace: A4Workspace,
) -> None:
    a4_workspace.write(
        "epic",
        1,
        "u",
        status="done",
        body=_epic_body(["- 2026-04-23 09:14 `../task/2-a.md`"]),
    )
    a4_workspace.write(
        "task", 2, "a", status="done", parent="epic/1-u"
    )

    mismatches = _run_mismatches(a4_workspace.root)

    assert _by_rule(mismatches, "epic-children-all-terminal") == []
