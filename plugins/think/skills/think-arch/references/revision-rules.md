# Revision Rules

Rules for when to increment `revision` in the arch frontmatter and update the `revised` timestamp.

## When to Increment

Increment `revision` and update `revised` when:

1. **Reflecting source usecase changes** — after applying changes from an updated source usecase at iteration entry
2. **Reflecting review findings** — after applying changes from an `arch-reviewer` report
3. **Reflecting bootstrap feedback** — after applying changes from an `auto-bootstrap` report
4. **Area transition with content changes** — when moving between Technology Stack → External Dependencies → Component Design → Test Strategy, if the previous area's content changed
5. **Session close** — at the end of an iteration (as part of the session close procedure)

Each of these events increments revision by exactly 1. All other file updates (checkpoint writes, component confirmations, contract additions) do not increment revision.

## Update Procedure

When incrementing:

1. Increment `revision` by 1
2. Set `revised` to current timestamp (`YYYY-MM-DD HH:mm`)
3. If reflecting a review or bootstrap report, also add the report filename to `reflected_files`
