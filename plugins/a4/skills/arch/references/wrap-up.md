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

- **Fix now** — edit `architecture.md` (and any cross-referenced file). Edit the review item's `status:` to `resolved` directly, and add a dated `## Change Logs` bullet on each modified wiki page per the Wiki Update Protocol.
- **Defer** — leave `status: open`. Capture the deferral reason in conversation notes / handoff.
- **Discard** — edit `status:` to `discarded` directly.

## 4. Wiki close guard

For each item that transitioned to `resolved` whose `target:` lists one or more wiki basenames, verify each referenced wiki page contains a `## Change Logs` bullet whose markdown link points at the review item itself. Warn + allow override when missing.

## 5. Report

Summarize to the user:

- Phases completed this session
- Components added / revised
- Review items opened / resolved / still open
