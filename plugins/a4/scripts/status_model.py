"""Single source of truth for the a4 status model.

Defines per-family status enums, allowed transitions, terminal /
in-progress / active classifications, kind enums, cascade-target data,
and a small predicate API for legality checks. Imported by:

  - transition_status.py        — allowed transitions, family states,
                                  cascade-target data, legality predicates
  - markdown_validator.frontmatter         — enum membership per schema
  - markdown_validator.transitions         — legality predicates
  - markdown_validator.status_consistency  — supersedes trigger map,
                                             cascade-target data
  - workspace_state.py          — terminal / in-progress / active sets
  - search.py                   — CLI flag validation

Authority: this file is canonical. The prose schema reference at
plugins/a4/references/frontmatter-schema.md mirrors this data for human
readers and must be kept in sync when the model changes.

Keys are folder names under `<a4-dir>/` (`usecase`, `task`, `review`,
`spec`, `idea`, `spark`). The validator's `spark_brainstorm` schema
maps to the `spark` folder key.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Status enums
# ---------------------------------------------------------------------------

# Full set of valid `status:` values per family.
STATUS_BY_FOLDER: dict[str, frozenset[str]] = {
    "usecase": frozenset(
        {
            "draft",
            "ready",
            "implementing",
            "revising",
            "shipped",
            "superseded",
            "discarded",
            "blocked",
        }
    ),
    "task": frozenset(
        {"open", "pending", "progress", "complete", "failing", "discarded"}
    ),
    "review": frozenset({"open", "in-progress", "resolved", "discarded"}),
    "spec": frozenset({"draft", "active", "deprecated", "superseded"}),
    "idea": frozenset({"open", "promoted", "discarded"}),
    "spark": frozenset({"open", "promoted", "discarded"}),
}


# ---------------------------------------------------------------------------
# Allowed forward transitions
# ---------------------------------------------------------------------------
#
# Only families with a mechanical writer (transition_status.py) appear
# here. `idea` and `spark` transitions are user-driven and not enforced
# by the writer; cross-file consistency is reported by
# markdown_validator.status_consistency instead.
#
# States absent as keys have no outgoing transitions (terminal).

UC_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"ready", "discarded"}),
    "ready": frozenset({"draft", "implementing", "discarded"}),
    "implementing": frozenset({"shipped", "revising", "discarded", "blocked"}),
    "revising": frozenset({"ready", "discarded"}),
    "blocked": frozenset({"ready", "discarded"}),
    "shipped": frozenset({"superseded", "discarded"}),
}

TASK_TRANSITIONS: dict[str, frozenset[str]] = {
    "open": frozenset({"pending", "progress", "discarded"}),
    "pending": frozenset({"progress", "discarded"}),
    "progress": frozenset({"complete", "failing", "pending", "discarded"}),
    "complete": frozenset({"pending", "discarded"}),
    "failing": frozenset({"pending", "progress", "discarded"}),
}

REVIEW_TRANSITIONS: dict[str, frozenset[str]] = {
    "open": frozenset({"in-progress", "resolved", "discarded"}),
    "in-progress": frozenset({"open", "resolved", "discarded"}),
    "resolved": frozenset({"open"}),
}

SPEC_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"active", "deprecated"}),
    "active": frozenset({"deprecated", "superseded"}),
    "deprecated": frozenset({"superseded"}),
}

FAMILY_TRANSITIONS: dict[str, dict[str, frozenset[str]]] = {
    "usecase": UC_TRANSITIONS,
    "task": TASK_TRANSITIONS,
    "review": REVIEW_TRANSITIONS,
    "spec": SPEC_TRANSITIONS,
}


# ---------------------------------------------------------------------------
# Status classifications
# ---------------------------------------------------------------------------

TERMINAL_STATUSES: dict[str, frozenset[str]] = {
    "usecase": frozenset({"shipped", "superseded", "discarded"}),
    "task": frozenset({"complete", "discarded"}),
    "review": frozenset({"resolved", "discarded"}),
    "spec": frozenset({"deprecated", "superseded"}),
    "idea": frozenset({"promoted", "discarded"}),
    "spark": frozenset({"promoted", "discarded"}),
}

IN_PROGRESS_STATUSES: dict[str, frozenset[str]] = {
    "usecase": frozenset({"implementing", "revising"}),
    "task": frozenset({"progress"}),
    "review": frozenset({"in-progress"}),
    "spec": frozenset(),
    "idea": frozenset(),
    "spark": frozenset(),
}

BLOCKED_STATUSES: frozenset[str] = frozenset({"blocked"})

# Tasks occupying the work queue — surfaced as the active section of the
# workspace dashboard.
ACTIVE_TASK_STATUSES: frozenset[str] = frozenset({"pending", "progress", "failing"})


# ---------------------------------------------------------------------------
# Kind enums
# ---------------------------------------------------------------------------
#
# Wiki types live in common.WIKI_TYPES — duplicating them here would
# fragment the wiki vocabulary across two modules.

KIND_BY_FOLDER: dict[str, frozenset[str]] = {
    "task": frozenset({"feature", "spike", "bug", "research"}),
    "review": frozenset({"finding", "gap", "question"}),
}


# ---------------------------------------------------------------------------
# Cascade-target data
# ---------------------------------------------------------------------------
#
# Used by ``transition_status.py`` (writer that performs cascades) and by
# ``markdown_validator.status_consistency`` (reader that flags drift when
# cascades did not run). Holding both sides' data here keeps the writer
# and the safety-net reader in lockstep.

# Per-family terminal-active status that triggers a supersedes cascade
# when reached by a successor. A successor at this status causes its
# same-family ``supersedes:`` targets to flip to ``superseded``.
SUPERSEDES_TRIGGER_STATUS: dict[str, str] = {
    "spec": "active",
    "usecase": "shipped",
}

# Per-family target statuses from which a supersedes cascade is willing
# to flip the target to ``superseded``. Targets outside this set are
# skipped (already-superseded, mid-flight implementing/draft, etc.).
SUPERSEDABLE_FROM_STATUSES: dict[str, frozenset[str]] = {
    "spec": frozenset({"active", "deprecated"}),
    "usecase": frozenset({"shipped"}),
}

# When a usecase transitions to ``revising``, every task whose
# ``implements:`` lists the UC and is currently in one of these
# statuses gets reset to ``TASK_RESET_TARGET``.
TASK_RESET_ON_REVISING: frozenset[str] = frozenset({"progress", "failing"})
TASK_RESET_TARGET: str = "pending"

# When a UC discard cascade looks at a review item, items already in one
# of these terminal statuses are skipped (no flip).
REVIEW_TERMINAL: frozenset[str] = frozenset({"resolved", "discarded"})


# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------


def is_transition_legal(family: str, from_status: str, to_status: str) -> bool:
    """True iff ``family`` allows ``from_status → to_status``."""
    return to_status in FAMILY_TRANSITIONS.get(family, {}).get(
        from_status, frozenset()
    )


def legal_targets_from(family: str, from_status: str) -> frozenset[str]:
    """Allowed outgoing targets from ``from_status``; empty if terminal."""
    return FAMILY_TRANSITIONS.get(family, {}).get(from_status, frozenset())


def is_terminal(family: str, status: str) -> bool:
    """True iff ``status`` is in the family's terminal set."""
    return status in TERMINAL_STATUSES.get(family, frozenset())
