# Revision Rules

Rules for when to increment `revision` in the plan frontmatter and update the `revised` timestamp.

## When to Increment

Increment `revision` and update `revised` when:

1. **Before review** — immediately before launching a reviewer subagent (checkpoint write + revision increment together). This stamps the exact document state the reviewer will evaluate.
2. **Reflecting source spec changes** — after applying changes from an updated source spec at iteration entry
3. **Reflecting review findings** — after applying changes from a `plan-reviewer` report
4. **Reflecting integration report findings** — after applying changes from a `think-verify` integration report
5. **Reflecting risk assessment findings** — after applying confirmed risks from a `risk-assessor` report to the Risk Assessment section
6. **Session close** — at the end of an iteration (as part of the session close procedure)
7. **Finalization** — when setting `status: final`

Each of these events increments revision by exactly 1, even if multiple changes are made in the same event. All other file updates (checkpoint writes, unit confirmations, detail additions, dependency graph updates) do not increment revision.

## Update Procedure

When incrementing:

1. Increment `revision` by 1
2. Set `revised` to current timestamp (`YYYY-MM-DD HH:mm`)
3. If reflecting a review, integration report, or risk assessment, also add the report filename to `reflected_files`
