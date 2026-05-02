"""Unit tests for ``status_cascade.py`` engines.

Covers the four cascade engines that flip related files when a primary
``status:`` change occurs on a usecase / spec / issue-family file:

  - ``uc_revising``           — UC implementing → revising resets
                                progress / failing tasks to pending.
  - ``uc_discarded``          — UC → discarded propagates to implementing
                                tasks and targeting reviews.
  - ``uc_supersedes_chain``   — UC → shipped flips same-family supersedes
                                targets shipped → superseded.
  - ``spec_supersedes_chain`` — spec → active flips same-family supersedes
                                targets {active|deprecated} → superseded.

Plus the recovery sweep ``apply_supersedes_sweep`` and
``status_model.cascade_for`` precedence.

Tests use the shared ``a4_workspace`` fixture from ``conftest.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from common import iter_family
from markdown import read_fm
from markdown_validator.refs import RefIndex
from status_cascade import (
    Report,
    apply_status_change,
    apply_supersedes_sweep,
    find_reviews_targeting,
    find_tasks_implementing,
    run_cascade,
)
from status_model import cascade_for


TODAY = "2026-05-02 14:30"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _status(p: Path) -> str:
    fm = read_fm(p)
    assert fm is not None, f"unreadable fm: {p}"
    return fm["status"]


def _updated(p: Path) -> str:
    fm = read_fm(p)
    assert fm is not None
    return str(fm["updated"])


def _make_review(
    workspace,
    id_: int,
    slug: str,
    *,
    target: Any,
    status: str = "open",
    kind: str = "finding",
    priority: str = "medium",
    source: str = "test",
) -> Path:
    """Write a review item with the body shape its frontmatter validator expects."""
    body = (
        "## Description\nx\n\n"
        "## Expected\nx\n\n"
        "## Actual\nx\n\n"
        "## Impact\nx\n"
    )
    return workspace.write(
        "review",
        id_,
        slug,
        type_override="review",
        status=status,
        kind=kind,
        target=target,
        priority=priority,
        source=source,
        body=body,
    )


# ---------------------------------------------------------------------------
# Tier 1: high-risk cascade cases
# ---------------------------------------------------------------------------


def test_uc_revising_resets_in_progress_tasks(a4_workspace) -> None:
    """Case 1 — UC implementing → revising resets progress task to pending,
    leaves complete task untouched, and refreshes ``updated:``."""
    a4_workspace.write("usecase", 1, "search", status="revising")
    t_progress = a4_workspace.write(
        "task",
        2,
        "index",
        status="progress",
        implements=["usecase/1-search"],
        updated="2026-04-01 09:00",
    )
    t_complete = a4_workspace.write(
        "task",
        3,
        "ui",
        status="complete",
        implements=["usecase/1-search"],
        updated="2026-04-01 09:00",
    )

    report = Report()
    run_cascade(
        "uc_revising",
        a4_workspace.root,
        "usecase",
        "usecase/1-search.md",
        TODAY,
        dry_run=False,
        report=report,
        index=RefIndex(a4_workspace.root),
    )

    assert _status(t_progress) == "pending"
    assert _updated(t_progress) == TODAY
    assert _status(t_complete) == "complete"
    assert _updated(t_complete) == "2026-04-01 09:00"

    flipped = [c.path for c in report.cascades]
    assert "task/2-index.md" in flipped
    assert all(s["reason"] == "not-in-reset-state" for s in report.skipped)
    assert any("3-ui.md" in s["path"] for s in report.skipped)
    assert report.errors == []


def test_uc_discarded_skips_terminal_reviews(a4_workspace) -> None:
    """Case 3 — UC → discarded flips open reviews and tasks but skips
    reviews already in ``resolved`` / ``discarded``."""
    a4_workspace.write("usecase", 1, "search", status="discarded")
    t = a4_workspace.write(
        "task",
        2,
        "index",
        status="progress",
        implements=["usecase/1-search"],
    )
    r_open = _make_review(
        a4_workspace, 3, "missing-uc", target=["usecase/1-search"], status="open"
    )
    r_resolved = _make_review(
        a4_workspace, 4, "old", target=["usecase/1-search"], status="resolved"
    )

    report = Report()
    run_cascade(
        "uc_discarded",
        a4_workspace.root,
        "usecase",
        "usecase/1-search.md",
        TODAY,
        dry_run=False,
        report=report,
        index=RefIndex(a4_workspace.root),
    )

    assert _status(t) == "discarded"
    assert _status(r_open) == "discarded"
    assert _status(r_resolved) == "resolved"

    skipped_terminal = [
        s for s in report.skipped if s["reason"] == "review-terminal"
    ]
    assert any("4-old.md" in s["path"] for s in skipped_terminal)
    assert "status='resolved'" in skipped_terminal[0]["detail"]
    assert report.errors == []


def test_supersedes_skips_cross_family_targets(a4_workspace) -> None:
    """Case 5 — UC supersedes-chain ignores non-usecase entries and only
    flips same-family targets."""
    old_uc = a4_workspace.write("usecase", 1, "old-search", status="shipped")
    cross = a4_workspace.write("spec", 2, "stack", status="active")
    a4_workspace.write(
        "usecase",
        3,
        "search",
        status="shipped",
        supersedes=["usecase/1-old-search", "spec/2-stack"],
    )

    report = Report()
    run_cascade(
        "uc_supersedes_chain",
        a4_workspace.root,
        "usecase",
        "usecase/3-search.md",
        TODAY,
        dry_run=False,
        report=report,
        index=RefIndex(a4_workspace.root),
    )

    assert _status(old_uc) == "superseded"
    assert _status(cross) == "active"

    cross_skips = [
        s for s in report.skipped if s["reason"] == "cross-family-supersedes"
    ]
    assert len(cross_skips) == 1
    assert "spec/2-stack" in cross_skips[0]["path"]
    assert report.errors == []


def test_dry_run_writes_no_disk_changes(a4_workspace) -> None:
    """Case 11 — ``dry_run=True`` populates the report but leaves files
    on disk untouched. A subsequent real run produces the same flips."""
    a4_workspace.write("usecase", 1, "search", status="revising")
    t = a4_workspace.write(
        "task",
        2,
        "index",
        status="progress",
        implements=["usecase/1-search"],
        updated="2026-04-01 09:00",
    )
    before = t.read_bytes()

    dry_report = Report()
    run_cascade(
        "uc_revising",
        a4_workspace.root,
        "usecase",
        "usecase/1-search.md",
        TODAY,
        dry_run=True,
        report=dry_report,
        index=RefIndex(a4_workspace.root),
    )

    assert t.read_bytes() == before
    assert _status(t) == "progress"
    assert any(c.path == "task/2-index.md" for c in dry_report.cascades)

    real_report = Report()
    run_cascade(
        "uc_revising",
        a4_workspace.root,
        "usecase",
        "usecase/1-search.md",
        TODAY,
        dry_run=False,
        report=real_report,
        index=RefIndex(a4_workspace.root),
    )
    assert _status(t) == "pending"
    assert [c.path for c in real_report.cascades] == [
        c.path for c in dry_report.cascades
    ]


def test_apply_status_change_preserves_log_body(a4_workspace) -> None:
    """Case 15 — ``apply_status_change`` rewrites only frontmatter
    scalars and leaves ``## Log`` body bytes untouched."""
    body = (
        "## Description\nimplement search\n\n"
        "## Files\n- src/search.py\n\n"
        "## Unit Test Strategy\npytest\n\n"
        "## Acceptance Criteria\n- works\n\n"
        "## Log\n"
        "- 2026-04-01 — picked up by alice\n"
        "- 2026-04-15 — paused, see review/9\n"
    )
    t = a4_workspace.write(
        "task", 2, "index", status="progress", body=body
    )

    apply_status_change(t, "progress", "pending", "test", dry_run=False, today=TODAY)

    new_text = t.read_text(encoding="utf-8")
    assert "## Log\n- 2026-04-01 — picked up by alice" in new_text
    assert "- 2026-04-15 — paused, see review/9\n" in new_text
    assert _status(t) == "pending"
    assert _updated(t) == TODAY


# ---------------------------------------------------------------------------
# Tier 2: ref-resolution + recovery
# ---------------------------------------------------------------------------


def test_spec_supersedes_flips_active_and_deprecated(a4_workspace) -> None:
    """Case 7 — spec supersedes-chain flips both ``active`` and
    ``deprecated`` predecessors to ``superseded``."""
    s_active = a4_workspace.write(
        "spec", 1, "stack-v1", status="active",
        body="## Description\nx\n\n## Decision\nv1\n",
    )
    s_deprecated = a4_workspace.write(
        "spec", 2, "stack-v0", status="deprecated",
        body="## Description\nx\n\n## Decision\nv0\n",
    )
    a4_workspace.write(
        "spec",
        3,
        "stack-v2",
        status="active",
        supersedes=["spec/1-stack-v1", "spec/2-stack-v0"],
        body="## Description\nx\n\n## Decision\nv2\n",
    )

    report = Report()
    run_cascade(
        "spec_supersedes_chain",
        a4_workspace.root,
        "spec",
        "spec/3-stack-v2.md",
        TODAY,
        dry_run=False,
        report=report,
        index=RefIndex(a4_workspace.root),
    )

    assert _status(s_active) == "superseded"
    assert _status(s_deprecated) == "superseded"
    assert {c.path for c in report.cascades} == {
        "spec/1-stack-v1.md",
        "spec/2-stack-v0.md",
    }
    assert report.errors == []


def test_supersedes_resolves_id_only_refs(a4_workspace) -> None:
    """Case 8 — ``supersedes:`` entries given as ``#<id>`` resolve via
    ``RefIndex`` and flip the right same-family target."""
    old_uc = a4_workspace.write("usecase", 1, "old", status="shipped")
    a4_workspace.write(
        "usecase", 2, "new", status="shipped", supersedes=["#1"]
    )

    report = Report()
    run_cascade(
        "uc_supersedes_chain",
        a4_workspace.root,
        "usecase",
        "usecase/2-new.md",
        TODAY,
        dry_run=False,
        report=report,
        index=RefIndex(a4_workspace.root),
    )

    assert _status(old_uc) == "superseded"
    assert any(c.path == "usecase/1-old.md" for c in report.cascades)


def test_supersedes_missing_id_target_records_error(a4_workspace) -> None:
    """Case 9 — id-bearing ``supersedes:`` entry that does not resolve to
    any file produces a ``missing-target`` error rather than a silent skip."""
    a4_workspace.write(
        "usecase", 2, "new", status="shipped", supersedes=["#999"]
    )

    report = Report()
    run_cascade(
        "uc_supersedes_chain",
        a4_workspace.root,
        "usecase",
        "usecase/2-new.md",
        TODAY,
        dry_run=False,
        report=report,
        index=RefIndex(a4_workspace.root),
    )

    assert report.cascades == []
    assert any("999" in e and "missing" in e for e in report.errors)


def test_apply_supersedes_sweep_recovers_missed_cascades(a4_workspace) -> None:
    """Case 13 — when the live PostToolUse hook is bypassed, the
    recovery sweep flips every missed supersedes target across UC and
    spec families. Idempotent on the second run."""
    a4_workspace.write("usecase", 1, "old", status="shipped")
    a4_workspace.write(
        "usecase", 2, "new", status="shipped", supersedes=["usecase/1-old"]
    )
    a4_workspace.write(
        "spec", 3, "stack-v1", status="active",
        body="## Description\nx\n\n## Decision\nv1\n",
    )
    a4_workspace.write(
        "spec",
        4,
        "stack-v2",
        status="active",
        supersedes=["spec/3-stack-v1"],
        body="## Description\nx\n\n## Decision\nv2\n",
    )

    reports = apply_supersedes_sweep(a4_workspace.root, dry_run=False)

    flipped_paths = {c.path for r in reports for c in r.cascades}
    assert "usecase/1-old.md" in flipped_paths
    assert "spec/3-stack-v1.md" in flipped_paths
    assert _status(a4_workspace.root / "usecase" / "1-old.md") == "superseded"
    assert _status(a4_workspace.root / "spec" / "3-stack-v1.md") == "superseded"

    second = apply_supersedes_sweep(a4_workspace.root, dry_run=False)
    assert all(r.cascades == [] for r in second)


# ---------------------------------------------------------------------------
# Tier 3: edges + idempotency
# ---------------------------------------------------------------------------


def test_uc_revising_skips_pending_task(a4_workspace) -> None:
    """Case 2 — task in ``pending`` (outside ``TASK_RESET_ON_REVISING``)
    is skipped with ``not-in-reset-state``."""
    a4_workspace.write("usecase", 1, "search", status="revising")
    t = a4_workspace.write(
        "task",
        2,
        "index",
        status="pending",
        implements=["usecase/1-search"],
    )

    report = Report()
    run_cascade(
        "uc_revising",
        a4_workspace.root,
        "usecase",
        "usecase/1-search.md",
        TODAY,
        dry_run=False,
        report=report,
        index=RefIndex(a4_workspace.root),
    )

    assert _status(t) == "pending"
    assert report.cascades == []
    assert any(s["reason"] == "not-in-reset-state" for s in report.skipped)


def test_uc_discarded_skips_already_discarded_task(a4_workspace) -> None:
    """Case 4 — task already at ``discarded`` is skipped, no infinite
    cascade."""
    a4_workspace.write("usecase", 1, "search", status="discarded")
    t = a4_workspace.write(
        "task",
        2,
        "index",
        status="discarded",
        implements=["usecase/1-search"],
    )

    report = Report()
    run_cascade(
        "uc_discarded",
        a4_workspace.root,
        "usecase",
        "usecase/1-search.md",
        TODAY,
        dry_run=False,
        report=report,
        index=RefIndex(a4_workspace.root),
    )

    assert _status(t) == "discarded"
    assert report.cascades == []
    assert any(s["reason"] == "already-discarded" for s in report.skipped)


def test_supersedes_skips_target_in_unsupersedable_status(a4_workspace) -> None:
    """Case 6 — UC target in ``implementing`` (not in
    ``SUPERSEDABLE_FROM_STATUSES['usecase']``) is skipped."""
    target = a4_workspace.write("usecase", 1, "old", status="implementing")
    a4_workspace.write(
        "usecase",
        2,
        "new",
        status="shipped",
        supersedes=["usecase/1-old"],
    )

    report = Report()
    run_cascade(
        "uc_supersedes_chain",
        a4_workspace.root,
        "usecase",
        "usecase/2-new.md",
        TODAY,
        dry_run=False,
        report=report,
        index=RefIndex(a4_workspace.root),
    )

    assert _status(target) == "implementing"
    assert report.cascades == []
    assert any(s["reason"] == "not-supersedable" for s in report.skipped)


def test_supersedes_unreadable_target_records_error(
    a4_workspace, tmp_path: Path
) -> None:
    """Case 10 — when a supersedes target file has corrupt frontmatter,
    the cascade records an error and continues with the rest of the chain."""
    good_target = a4_workspace.write("usecase", 1, "good", status="shipped")
    bad_path = a4_workspace.root / "usecase" / "5-bad.md"
    bad_path.write_text("not a valid markdown file at all\n", encoding="utf-8")
    a4_workspace.write(
        "usecase",
        2,
        "new",
        status="shipped",
        supersedes=["usecase/1-good", "usecase/5-bad"],
    )

    report = Report()
    run_cascade(
        "uc_supersedes_chain",
        a4_workspace.root,
        "usecase",
        "usecase/2-new.md",
        TODAY,
        dry_run=False,
        report=report,
        index=RefIndex(a4_workspace.root),
    )

    assert _status(good_target) == "superseded"
    assert any("5-bad" in e for e in report.errors)


def test_cascade_idempotent_on_second_run(a4_workspace) -> None:
    """Case 12 — running the same cascade twice on a now-consistent
    workspace produces no further changes."""
    a4_workspace.write("usecase", 1, "search", status="revising")
    a4_workspace.write(
        "task",
        2,
        "index",
        status="progress",
        implements=["usecase/1-search"],
    )

    first = Report()
    run_cascade(
        "uc_revising",
        a4_workspace.root,
        "usecase",
        "usecase/1-search.md",
        TODAY,
        dry_run=False,
        report=first,
        index=RefIndex(a4_workspace.root),
    )
    assert len(first.cascades) == 1

    second = Report()
    run_cascade(
        "uc_revising",
        a4_workspace.root,
        "usecase",
        "usecase/1-search.md",
        TODAY,
        dry_run=False,
        report=second,
        index=RefIndex(a4_workspace.root),
    )
    assert second.cascades == []
    assert second.errors == []


def test_cascade_for_specific_overrides_wildcard() -> None:
    """Case 14 — ``cascade_for`` returns the (family, from, to) entry
    when one exists; otherwise falls back to the (family, None, to) wildcard."""
    assert cascade_for("usecase", "implementing", "revising") == "uc_revising"
    assert cascade_for("usecase", "ready", "discarded") == "uc_discarded"
    assert cascade_for("usecase", "implementing", "discarded") == "uc_discarded"
    assert cascade_for("usecase", "draft", "ready") is None


def test_find_tasks_implementing_walks_all_four_families(a4_workspace) -> None:
    """Case 16 — ``find_tasks_implementing`` scans task / bug / spike /
    research and returns every file whose ``implements:`` matches."""
    a4_workspace.write("usecase", 1, "search", status="ready")
    paths = {
        "task": a4_workspace.write(
            "task", 2, "t", status="open", implements=["usecase/1-search"]
        ),
        "bug": a4_workspace.write(
            "bug", 3, "b", status="open", implements=["usecase/1-search"]
        ),
        "spike": a4_workspace.write(
            "spike", 4, "s", status="open", implements=["usecase/1-search"]
        ),
        "research": a4_workspace.write(
            "research", 5, "r", status="open", implements=["usecase/1-search"]
        ),
    }
    a4_workspace.write(
        "task", 6, "other", status="open", implements=["usecase/99-elsewhere"]
    )

    matched = find_tasks_implementing(
        a4_workspace.root, "usecase/1-search", RefIndex(a4_workspace.root)
    )
    assert {p.name for p in matched} == {p.name for p in paths.values()}


def test_find_reviews_targeting_accepts_string_and_list_target(
    a4_workspace,
) -> None:
    """Case 17 — ``find_reviews_targeting`` matches whether ``target:``
    is a YAML string scalar or a list of strings."""
    a4_workspace.write("usecase", 1, "search", status="ready")
    r_string = _make_review(
        a4_workspace, 2, "single-target", target="usecase/1-search"
    )
    r_list = _make_review(
        a4_workspace,
        3,
        "list-target",
        target=["usecase/1-search", "domain"],
    )
    _make_review(a4_workspace, 4, "other", target=["usecase/9-other"])

    matched = find_reviews_targeting(
        a4_workspace.root, "usecase/1-search", RefIndex(a4_workspace.root)
    )
    assert {p.name for p in matched} == {r_string.name, r_list.name}
