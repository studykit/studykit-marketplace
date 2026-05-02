# UC Ship Review (post-loop review, ship branch)

After the loop body (Steps 1–3) completes with all tests passing and all in-scope tasks `status: complete`, walk every UC whose implementation is now done and let the user confirm `implementing → shipped`.

This document holds the per-UC verdict template + acceptance/defer/gap protocol the SKILL.md references. It is **user-driven**: the SKILL.md transitions to `conversational`, presents the verdict, and writes status only on explicit user confirmation. No agent classifies or auto-ships.

## Conditional on UC presence

If no task in this run has a non-empty `implements:` (UC-less project, or every task in scope is a spike / bug / spec-justified task), the candidate set is empty by construction — skip ship review entirely and go to wrap-up. This is normal, not an error.

## Candidate selection

A UC X is a ship candidate when **all** hold:

- `X.status` is `implementing` (flipped by `coder` at work-start per its protocol).
- Every task with `implements: [usecase/X]` in its frontmatter now has `status: complete`.
- No review item with `target: usecase/X` is `open` or `in-progress` (all `resolved` or `discarded`).

If the candidate set is empty, skip to wrap-up.

## Per-UC verdict

For each candidate X, read:

- The UC body — `## Flow`, `## Validation`, `## Error Handling`, `## Expected Outcome`.
- The `## Log` entries of its implementing tasks (if hand-maintained).
- The test-runner return summary from Step 3 (passed-test names relevant to X).

Compose a **two- to four-sentence** verdict covering:

- **(a)** Which task(s) implemented this UC.
- **(b)** Which integration / smoke tests exercise its Flow / Validation / Error handling.
- **(c)** Any Expected Outcome point not yet visibly covered by the tests.

No new files, no review items emitted at this point unless the user defers with a reason (see "Defer with reason" below).

## Presentation + protocol

Transition to `conversational`. For each candidate X, show the verdict and ask:

> UC X is ready to mark shipped based on completed tasks and passing tests. [verdict]. Mark shipped?

Accept natural-language answers:

- **Confirm** (`yes`, `ok`, `맞아요`, `확정`, `mark shipped`, `ship it`) → flip `implementing → shipped` by editing `status:` directly.
- **Defer without reason** (`not yet`, `아직`, `let me verify`, `hold`) → leave `implementing`. The next `/a4:auto-coding iterate` will re-offer.
- **Defer with reason** (`no — X is incomplete because…`) → leave `implementing` and emit a fresh review item targeting `usecase/X` with `kind: gap`, `source: self`, body containing the user's reason. Frontmatter and body shape follow `${CLAUDE_PLUGIN_ROOT}/authoring/review-authoring.md`.

## Confirmed → shipped

For every UC the user confirmed, edit the UC file's frontmatter `status:` from `implementing` to `shipped` directly with the `Edit` tool. The PostToolUse cascade hook (`${CLAUDE_PLUGIN_ROOT}/scripts/a4_hook.py`) then:

- Refreshes `updated:` on the UC.
- Runs the supersedes-chain cascade — if the UC has a non-empty `supersedes:` list, every same-family target currently at `shipped` is flipped to `superseded` with a `superseded by usecase/<id>` reason recorded on the cascade report.
- Surfaces an `additionalContext` block listing the cascade flips; relay those to the user.

There is no mechanical task gate (a4 v6.0.0); the operator owns confirming that all tasks declaring `implements: [usecase/<this>]` are `complete` before flipping. Illegal jumps (e.g., `shipped → ready`) are silently ignored by the cascade hook and surfaced by the Stop-hook safety net — fix the source rather than retry.

Do **not** hand-edit `updated:` or supersedes-target frontmatter — the cascade hook owns those writes.

## Commit

Commit all UC ship-transitions together as one commit, separate from task commits. Predecessor UCs auto-flipped to `superseded` by the cascade hook land in the same working-tree change and belong in the same commit.

Suggested message prefix: `docs(a4): ship UC <ids>`.

## `shipped` is forward-path terminal

If a UC needs revision later, either:

- Create a new UC via `/a4:usecase` with `supersedes: [usecase/<old-id>-<slug>]`. When that new UC eventually ships, the cascade hook flips the old one to `superseded`.
- Or flip `shipped → discarded` (edit `status:` directly) when the code is being removed.

Never try to move a UC back from `shipped` to `implementing` or `draft`.
