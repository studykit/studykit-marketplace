# Architecture Wrap Up

The architecture session ends only when the user says so. When the user indicates they're done, run this procedure.

## 1. Pre-flight consistency check

Read `architecture.md` end-to-end. Confirm:

- Every Information Flow UC resolves to an existing UC file.
- Every component's contracts align with its sequence diagrams.
- Every schema field appears in `domain.md`.

Resolve obvious gaps before launching the reviewer.

## 2. Launch arch-reviewer

Spawn:

```
Agent(subagent_type: "a4:arch-reviewer")
```

Pass:

- `a4/` absolute path
- Prior-session open review items that target `architecture` (so the reviewer can skip duplicates)

The reviewer emits one review item file per finding into `a4/review/<id>-<slug>.md` (using `allocate_id.py`) and returns a summary.

## 3. Walk findings

For each emitted review item, ordered by priority then id, present to the user and resolve or defer:

- **Fix now** — edit `architecture.md` (and any cross-referenced file). Flip the review item `status: resolved` via `transition_status.py` (which appends the `<log>` entry), and add a dated `<change-logs>` bullet on each modified wiki page per the Wiki Update Protocol.
- **Defer** — leave `status: open`. Capture the deferral reason in conversation notes / handoff (writer-managed `<log>` only updates on transitions).
- **Discard** — set `status: discarded` via `scripts/transition_status.py`; the writer records the reason in `<log>`.

## 4. Wiki close guard

For each item that transitioned to `resolved` with non-empty `wiki_impact`, verify the referenced wiki pages contain a `<change-logs>` bullet whose markdown link points at the causing issue. Warn + allow override when missing.

## 5. Report

Summarize to the user:

- Phases completed this session
- Components added / revised
- Review items opened / resolved / still open
- Suggested next step:
  - `/a4:auto-bootstrap` to set up dev environment
  - `/a4:roadmap` if bootstrap is already done
