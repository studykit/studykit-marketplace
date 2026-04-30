"""Single source of truth for the a4 status model.

Defines per-family status enums, allowed transitions, terminal /
in-progress / active classifications, kind enums, cascade-target data,
the cascade trigger map, and a small predicate API for legality checks.
Imported by:

  - transition_status.py        — allowed transitions, family states,
                                  cascade-target data, cascade trigger
                                  map, legality predicates
  - markdown_validator.frontmatter         — enum membership per schema
  - markdown_validator.transitions         — legality predicates
  - markdown_validator.status_consistency  — supersedes trigger map,
                                             cascade-target data
  - workspace_state.py          — terminal / in-progress / active sets
  - search.py                   — CLI flag validation

Authority: this file is canonical. The prose schema reference at
plugins/a4/references/frontmatter-schema.md mirrors this data for human
readers and must be kept in sync when the model changes.

Keys are folder names under `<a4-dir>/`: `usecase`, the four task-family
folders (`feature`, `bug`, `spike`, `research`), `review`, `spec`,
`idea`, `spark`. The validator's `spark_brainstorm` schema maps to the
`spark` folder key.

a4 v12.0.0 split the previous `task` family with a `kind:` discriminator
into four sibling families that share the same status enum and
transitions but live in flat folders. ``TASK_FAMILY_TYPES`` lists them
for callers that still need the cross-kind grouping (e.g., UC cascades
that touch every implementing task regardless of kind).
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Family groupings
# ---------------------------------------------------------------------------

# The four issue families that share TASK_TRANSITIONS / shared status
# enum. Order is the canonical iteration order for cross-kind walks.
TASK_FAMILY_TYPES: tuple[str, ...] = ("feature", "bug", "spike", "research")


# ---------------------------------------------------------------------------
# Status enums
# ---------------------------------------------------------------------------

_TASK_STATUSES: frozenset[str] = frozenset(
    {"open", "pending", "progress", "complete", "failing", "discarded"}
)

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
    "feature": _TASK_STATUSES,
    "bug": _TASK_STATUSES,
    "spike": _TASK_STATUSES,
    "research": _TASK_STATUSES,
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
    "feature": TASK_TRANSITIONS,
    "bug": TASK_TRANSITIONS,
    "spike": TASK_TRANSITIONS,
    "research": TASK_TRANSITIONS,
    "review": REVIEW_TRANSITIONS,
    "spec": SPEC_TRANSITIONS,
}


# ---------------------------------------------------------------------------
# Status classifications
# ---------------------------------------------------------------------------

_TASK_TERMINAL: frozenset[str] = frozenset({"complete", "discarded"})
_TASK_IN_PROGRESS: frozenset[str] = frozenset({"progress"})

TERMINAL_STATUSES: dict[str, frozenset[str]] = {
    "usecase": frozenset({"shipped", "superseded", "discarded"}),
    "feature": _TASK_TERMINAL,
    "bug": _TASK_TERMINAL,
    "spike": _TASK_TERMINAL,
    "research": _TASK_TERMINAL,
    "review": frozenset({"resolved", "discarded"}),
    "spec": frozenset({"deprecated", "superseded"}),
    "idea": frozenset({"promoted", "discarded"}),
    "spark": frozenset({"promoted", "discarded"}),
}

IN_PROGRESS_STATUSES: dict[str, frozenset[str]] = {
    "usecase": frozenset({"implementing", "revising"}),
    "feature": _TASK_IN_PROGRESS,
    "bug": _TASK_IN_PROGRESS,
    "spike": _TASK_IN_PROGRESS,
    "research": _TASK_IN_PROGRESS,
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
#
# After a4 v12.0.0 only `review` carries an in-file `kind:` discriminator.
# The former `task` kind set was promoted to top-level family folders;
# see TASK_FAMILY_TYPES.

KIND_BY_FOLDER: dict[str, frozenset[str]] = {
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

# When a usecase transitions to ``revising``, every task across the
# four task families (``feature`` / ``bug`` / ``spike`` / ``research``;
# see TASK_FAMILY_TYPES) whose ``implements:`` lists the UC and is
# currently in one of these statuses gets reset to ``TASK_RESET_TARGET``.
TASK_RESET_ON_REVISING: frozenset[str] = frozenset({"progress", "failing"})
TASK_RESET_TARGET: str = "pending"

# When a UC discard cascade looks at a review item, items already in one
# of these terminal statuses are skipped (no flip).
REVIEW_TERMINAL: frozenset[str] = frozenset({"resolved", "discarded"})


# ---------------------------------------------------------------------------
# Cascade trigger map
# ---------------------------------------------------------------------------
#
# Which (family, from_status, to_status) primary transitions trigger a
# cross-file cascade, and a stable name for the cascade. Keyed by
# (family, from_status_or_None, to_status); ``None`` for from_status
# means "any legal source" — useful for transitions whose cascade fires
# regardless of where the file came from (e.g., UC → discarded).
#
# Lookup order in ``cascade_for``: the (family, from, to) entry wins
# over the (family, None, to) entry, so callers can override a generic
# rule with a specific one. Returns ``None`` when no cascade applies.
#
# Authoritative consumer: ``transition_status.transition()`` dispatches
# off these names. ``markdown_validator.status_consistency`` checks the
# observed reverse drift but does not consume this map directly — the
# check direction is opposite to the dispatch direction.

CASCADE_TRIGGERS: dict[tuple[str, str | None, str], str] = {
    ("usecase", "implementing", "revising"): "uc_revising",
    ("usecase", None, "discarded"): "uc_discarded",
    ("usecase", None, "shipped"): "uc_supersedes_chain",
    ("spec", None, "active"): "spec_supersedes_chain",
}


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


def cascade_for(family: str, from_status: str, to_status: str) -> str | None:
    """Cascade name for a primary transition, or ``None`` if none applies.

    Specific (family, from, to) entries take precedence over generic
    (family, None, to) wildcards.
    """
    specific = CASCADE_TRIGGERS.get((family, from_status, to_status))
    if specific is not None:
        return specific
    return CASCADE_TRIGGERS.get((family, None, to_status))
