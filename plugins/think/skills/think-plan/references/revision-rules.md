# Revision Rules

Rules for when to increment `revision` in the plan frontmatter and update the `revised` timestamp.

## When to Increment

Increment `revision` and update `revised` when:

1. **Plan initial creation** — first write of the plan file (revision 1)
2. **Reflecting a review report** — after auto-reflecting plan-reviewer findings (Phase 1)
3. **Reflecting a test report** — after updating the plan based on test failures (Phase 2)
4. **Status change** — when transitioning `status` (draft → verified → implementing → complete / blocked)

Each event increments revision by exactly 1, even if multiple changes are made in the same event.

## Update Procedure

When incrementing:

1. Increment `revision` by 1
2. Set `revised` to current timestamp (`YYYY-MM-DD HH:mm`)
3. If reflecting a report, add the report filename to `reflected_files`
4. Update `phase` and `cycle` as appropriate
