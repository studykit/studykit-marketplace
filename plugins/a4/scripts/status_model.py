"""Single source of truth for the a4 status model.

Defines per-family status enums, allowed transitions, terminal /
in-progress / active classifications, kind enums, cascade-target data,
the cascade trigger map, and a small predicate API for legality checks.
Imported by:

  - status_cascade.py           — allowed transitions, family states,
                                  cascade-target data, cascade trigger
                                  map, legality predicates
  - a4_hook.py                  — transitions / cascade trigger /
                                  legality predicates for the live
                                  PostToolUse cascade hook
  - markdown_validator.frontmatter         — enum membership per schema
  - markdown_validator.transitions         — legality predicates
  - markdown_validator.status_consistency  — supersedes trigger map,
                                             cascade-target data
  - workspace_state.py          — terminal / in-progress / active sets
  - search.py                   — CLI flag validation

Authority: this file is canonical. The prose schema references at
plugins/a4/authoring/frontmatter-issue.md (status changes and
cascades) and plugins/a4/authoring/<type>-authoring.md (per-type
lifecycle blocks) mirror this data for human readers and must be kept
in sync when the model changes.

Keys are folder names under `<a4-dir>/`: `usecase`, the four issue
families that share the task lifecycle (`task`, `bug`, `spike`,
`research`), `review`, `spec`, `idea`, `brainstorm`.

a4 v12.0.0 split the previous combined `task` folder (with a `kind:`
discriminator) into four sibling top-level folders that share the same
status enum and transitions but each have their own type literal and
authoring contract. ``ISSUE_FAMILY_TYPES`` lists them for callers that
still need the cross-family grouping (e.g., UC cascades that touch
every implementing task regardless of family). The `task` member is the
default — equivalent to Jira's "Task" issue type alongside "Bug",
"Story", etc. The other three (`bug`, `spike`, `research`) carry
specialized authoring contracts.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Family groupings
# ---------------------------------------------------------------------------

# The four issue families that share ISSUE_FAMILY_TRANSITIONS / shared
# status enum. Order is the canonical iteration order for cross-family
# walks. The `task` member is the default kind (regular implementation
# work); `bug` / `spike` / `research` are specialized variants.
ISSUE_FAMILY_TYPES: tuple[str, ...] = ("task", "bug", "spike", "research")


# ---------------------------------------------------------------------------
# Status enums
# ---------------------------------------------------------------------------

_TASK_STATUSES: frozenset[str] = frozenset(
    {"open", "queued", "progress", "holding", "done", "failing", "discarded"}
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
    "task": _TASK_STATUSES,
    "bug": _TASK_STATUSES,
    "spike": _TASK_STATUSES,
    "research": _TASK_STATUSES,
    "review": frozenset({"open", "in-progress", "resolved", "discarded"}),
    "spec": frozenset({"draft", "active", "deprecated", "superseded"}),
    "idea": frozenset({"open", "promoted", "discarded"}),
    "brainstorm": frozenset({"open", "promoted", "discarded"}),
    "umbrella": frozenset({"open", "done", "discarded"}),
}


# ---------------------------------------------------------------------------
# Allowed forward transitions
# ---------------------------------------------------------------------------
#
# Only families with a mechanical writer (the PostToolUse cascade hook
# / status_cascade.py) appear here. `idea` and `brainstorm` transitions
# are user-driven and not enforced by the cascade engine; cross-file
# consistency is reported by markdown_validator.status_consistency
# instead.
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

ISSUE_FAMILY_TRANSITIONS: dict[str, frozenset[str]] = {
    "open": frozenset({"queued", "progress", "done", "discarded"}),
    "queued": frozenset({"progress", "discarded"}),
    "progress": frozenset({"done", "failing", "queued", "holding", "discarded"}),
    "holding": frozenset({"progress", "discarded"}),
    "done": frozenset({"queued", "discarded"}),
    "failing": frozenset({"queued", "progress", "discarded"}),
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

UMBRELLA_TRANSITIONS: dict[str, frozenset[str]] = {
    "open": frozenset({"done", "discarded"}),
    "done": frozenset({"open", "discarded"}),
}

FAMILY_TRANSITIONS: dict[str, dict[str, frozenset[str]]] = {
    "usecase": UC_TRANSITIONS,
    "task": ISSUE_FAMILY_TRANSITIONS,
    "bug": ISSUE_FAMILY_TRANSITIONS,
    "spike": ISSUE_FAMILY_TRANSITIONS,
    "research": ISSUE_FAMILY_TRANSITIONS,
    "review": REVIEW_TRANSITIONS,
    "spec": SPEC_TRANSITIONS,
    "umbrella": UMBRELLA_TRANSITIONS,
}


# ---------------------------------------------------------------------------
# Status classifications
# ---------------------------------------------------------------------------

_TASK_TERMINAL: frozenset[str] = frozenset({"done", "discarded"})
_TASK_IN_PROGRESS: frozenset[str] = frozenset({"progress"})

TERMINAL_STATUSES: dict[str, frozenset[str]] = {
    "usecase": frozenset({"shipped", "superseded", "discarded"}),
    "task": _TASK_TERMINAL,
    "bug": _TASK_TERMINAL,
    "spike": _TASK_TERMINAL,
    "research": _TASK_TERMINAL,
    "review": frozenset({"resolved", "discarded"}),
    "spec": frozenset({"deprecated", "superseded"}),
    "idea": frozenset({"promoted", "discarded"}),
    "brainstorm": frozenset({"promoted", "discarded"}),
    "umbrella": frozenset({"done", "discarded"}),
}

IN_PROGRESS_STATUSES: dict[str, frozenset[str]] = {
    "usecase": frozenset({"implementing", "revising"}),
    "task": _TASK_IN_PROGRESS,
    "bug": _TASK_IN_PROGRESS,
    "spike": _TASK_IN_PROGRESS,
    "research": _TASK_IN_PROGRESS,
    "review": frozenset({"in-progress"}),
    "spec": frozenset(),
    "idea": frozenset(),
    "brainstorm": frozenset(),
    "umbrella": frozenset(),
}

BLOCKED_STATUSES: frozenset[str] = frozenset({"blocked"})

# Tasks occupying the active workflow — surfaced as the active section
# of the workspace dashboard. Includes ``queued`` (in the work queue),
# ``progress`` (currently being worked), ``failing`` (failed this
# iteration, awaiting retry / defer), and ``holding`` (manually paused
# mid-work). ``open`` (backlog) and the terminal statuses are excluded.
ACTIVE_TASK_STATUSES: frozenset[str] = frozenset(
    {"queued", "progress", "failing", "holding"}
)


# ---------------------------------------------------------------------------
# Kind enums
# ---------------------------------------------------------------------------
#
# Wiki types live in common.WIKI_TYPES — duplicating them here would
# fragment the wiki vocabulary across two modules.
#
# After a4 v12.0.0 only `review` carries an in-file `kind:` discriminator.
# The former `task` kind set was promoted to top-level family folders;
# see ISSUE_FAMILY_TYPES.

KIND_BY_FOLDER: dict[str, frozenset[str]] = {
    "review": frozenset({"finding", "gap", "question"}),
}


# ---------------------------------------------------------------------------
# Cascade-target data
# ---------------------------------------------------------------------------
#
# Used by ``status_cascade.py`` (engine that performs cascades; called
# by both the PostToolUse cascade hook and the ``validate.py --fix``
# recovery sweep) and by ``markdown_validator.status_consistency``
# (reader that flags drift when cascades did not run). Holding both
# sides' data here keeps the writer and the safety-net reader in
# lockstep.

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
# four issue families (``task`` / ``bug`` / ``spike`` / ``research``;
# see ISSUE_FAMILY_TYPES) whose ``implements:`` lists the UC and is
# currently in one of these statuses gets reset to ``TASK_RESET_TARGET``.
# ``holding`` is intentionally outside the reset set — a manually paused
# task carries explicit human stewardship and is left untouched, in line
# with the policy that already exempts ``open`` / ``queued`` / ``done``.
TASK_RESET_ON_REVISING: frozenset[str] = frozenset({"progress", "failing"})
TASK_RESET_TARGET: str = "queued"

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
# Authoritative consumer: ``status_cascade.run_cascade()`` dispatches
# off these names (called by the PostToolUse cascade hook).
# ``markdown_validator.status_consistency`` checks the observed reverse
# drift but does not consume this map directly — the check direction is
# opposite to the dispatch direction.

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
