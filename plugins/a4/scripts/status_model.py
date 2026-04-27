"""Single source of truth for the a4 status model.

Defines per-family status enums, allowed transitions, terminal /
in-progress / active classifications, and kind enums. Imported by:

  - transition_status.py    — allowed transitions, family states
  - validate_frontmatter.py — enum membership per schema
  - workspace_state.py      — terminal / in-progress / active sets
  - search.py               — CLI flag validation

Authority: this file is canonical. The prose schema reference at
plugins/a4/references/frontmatter-schema.md mirrors this data for human
readers and must be kept in sync when the model changes.

Keys are folder names under `<a4-dir>/` (`usecase`, `task`, `review`,
`decision`, `idea`, `spark`). The validator's `spark_brainstorm` schema
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
    "decision": frozenset({"draft", "final", "superseded"}),
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
# validate_status_consistency.py instead.
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

DECISION_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"final"}),
    "final": frozenset({"superseded"}),
}

FAMILY_TRANSITIONS: dict[str, dict[str, frozenset[str]]] = {
    "usecase": UC_TRANSITIONS,
    "task": TASK_TRANSITIONS,
    "review": REVIEW_TRANSITIONS,
    "decision": DECISION_TRANSITIONS,
}


# ---------------------------------------------------------------------------
# Status classifications
# ---------------------------------------------------------------------------

TERMINAL_STATUSES: dict[str, frozenset[str]] = {
    "usecase": frozenset({"shipped", "superseded", "discarded"}),
    "task": frozenset({"complete", "discarded"}),
    "review": frozenset({"resolved", "discarded"}),
    "decision": frozenset({"final", "superseded"}),
    "idea": frozenset({"promoted", "discarded"}),
    "spark": frozenset({"promoted", "discarded"}),
}

IN_PROGRESS_STATUSES: dict[str, frozenset[str]] = {
    "usecase": frozenset({"implementing", "revising"}),
    "task": frozenset({"progress"}),
    "review": frozenset({"in-progress"}),
    "decision": frozenset(),
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
# Wiki kinds live in common.WIKI_KINDS — duplicating them here would
# fragment the wiki vocabulary across two modules.

KIND_BY_FOLDER: dict[str, frozenset[str]] = {
    "task": frozenset({"feature", "spike", "bug"}),
    "review": frozenset({"finding", "gap", "question"}),
}
