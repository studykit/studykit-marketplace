# Revision Rules

Rules for when to increment `revision` in the plan frontmatter and update the `revised` timestamp.

## When to Increment

Increment `revision` and update `revised` when:

1. **Before review** — immediately before launching a reviewer subagent (checkpoint write + revision increment together). This stamps the exact document state the reviewer will evaluate.
2. **Reflecting source spec changes** — after applying changes from an updated source spec at iteration entry
3. **Reflecting review findings** — after applying changes from a `plan-reviewer` report
4. **Session close** — at the end of an iteration (as part of the session close procedure)
5. **Finalization** — when setting `status: final`

Each of these events increments revision by exactly 1, even if multiple changes are made in the same event.

## When NOT to Increment

Do **not** increment during routine interview work within a session:

- Confirming a new unit
- Adding details to an existing unit (file mapping, test strategy, acceptance criteria)
- Updating the dependency graph
- Adding or updating the risk assessment
- Editing Open Items or Next Steps during the session
- Checkpoint writes (every 3 units, step transition)

These are normal working updates — the revision tracks discrete review/close milestones, not every edit.

## Update Procedure

When incrementing:

1. Increment `revision` by 1
2. Set `revised` to current timestamp (`YYYY-MM-DD HH:mm`)
3. If reflecting a review, also add the review report filename to `reflected_files`
