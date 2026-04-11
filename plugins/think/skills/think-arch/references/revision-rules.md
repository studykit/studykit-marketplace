# Revision Rules

Rules for when to increment `revision` in the arch frontmatter and update the `revised` timestamp.

## When to Increment

Increment `revision` and update `revised` when:

1. **Before review** — immediately before launching a reviewer subagent (checkpoint write + revision increment together). This stamps the exact document state the reviewer will evaluate.
2. **Reflecting source usecase changes** — after applying changes from an updated source usecase at iteration entry
3. **Reflecting review findings** — after applying changes from an `arch-reviewer` report
4. **Reflecting scaffold feedback** — after applying changes from an `auto-scaffold` report
5. **Area transition with content changes** — when moving between Technology Stack → External Dependencies → Component Design → Test Strategy, if the previous area's content changed
6. **Session close** — at the end of an iteration (as part of the session close procedure)
7. **Finalization** — when setting `status: final`

Each of these events increments revision by exactly 1. All other file updates (checkpoint writes, component confirmations, contract additions) do not increment revision.

## Update Procedure

When incrementing:

1. Increment `revision` by 1
2. Set `revised` to current timestamp (`YYYY-MM-DD HH:mm`)
3. If reflecting a review or scaffold report, also add the report filename to `reflected_files`
