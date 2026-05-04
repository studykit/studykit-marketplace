# Domain Wrap Up

Domain extraction ends only when the user says so. When the user indicates they're done, run this procedure.

## 1. Pre-flight consistency check

Read `domain.md` end-to-end. Confirm:

- Every concept in `## Relationships` exists in `## Concepts`.
- Every state-diagram concept in `## State Transitions` exists in `## Concepts`.
- Every UC referenced from `Referenced By` is an existing UC file.

Resolve obvious gaps before launching the reviewer.

## 2. Launch domain-reviewer

Spawn:

```
Agent(subagent_type: "a4:domain-reviewer")
```

Pass:

- `a4/` absolute path
- Prior-session open review items that target `domain` (so the reviewer can skip duplicates)

The reviewer emits one review item file per finding into `a4/review/<id>-<slug>.md` (using `allocate_id.py`) and returns a summary.

## 3. Walk findings

For each emitted review item, ordered by priority then id, present to the user and resolve or defer:

- **Fix now** — edit `domain.md` (and any cross-referenced file). Edit the review item's `status:` to `resolved` directly, and add a dated `## Change Logs` bullet on each modified wiki page.
- **Defer** — leave `status: open`. Capture the deferral reason in conversation notes / handoff.
- **Discard** — edit `status:` to `discarded` directly.

## 4. Wiki close guard

For each item that transitioned to `resolved` whose `target:` lists one or more wiki basenames, verify each referenced wiki page contains a `## Change Logs` bullet whose markdown link points at the review item itself. Warn + allow override when missing.

## 5. Report

Summarize to the user:

- Phases completed this session
- Concepts added / revised
- Relationships added / revised
- State diagrams added / revised
- Review items opened / resolved / still open

## Cross-stage findings

If domain work surfaces an issue in another wiki (e.g., a rename invalidates a `architecture.md` component name), do not edit that wiki — emit a review item with the appropriate `target:`. This skill is **continue + review item** for upstream findings: finish domain wrap-up, leave the review item open for the owning skill's `iterate` mode.
