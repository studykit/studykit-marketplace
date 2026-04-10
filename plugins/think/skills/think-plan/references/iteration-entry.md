# Iteration Entry Procedure

When entering **Iteration** mode (an existing `.impl-plan.md` file is found), perform these checks before starting work.

## 1. Source Spec Change Detection

Compare the stored `sha` in plan frontmatter against the current file:

1. Run `git hash-object <spec-file-path>` to get the current SHA.
2. If SHA matches the frontmatter `sha` → no changes, skip.
3. If SHA differs:
   - Run `git diff <stored-sha> <current-sha> -- <spec-file-path>` to see what changed.
   - Present the changes: "The source spec has been updated. Changes: [list]. Review these changes before continuing?"
   - Walk through each change with the user to determine plan impact (new units needed, existing units to update, dependency changes).
   - After reflecting, update `sources` in plan frontmatter (both `revision` and `sha`). If the working file content changed, **increment `revision`** and update `revised` timestamp.

## 2. Unreflected Review Reports

Check for `A4/<topic-slug>.impl-plan.review-*.md` files against the `reflected_files` list in frontmatter:

1. Identify review report files not listed in `reflected_files`.
2. Read each unreflected report and extract issues not yet addressed.
3. Present unreflected findings to the user alongside the Open Items from the last revision.
4. After reflecting, add the review report filenames to `reflected_files`. If the working file content changed, **increment `revision`** and update `revised` timestamp.

## 3. Present Work Backlog

After the checks above, present the Open Items table as a work backlog:

> Here are the open items from the last session:
>
> | # | Section | Item | What's Missing |
> |---|---------|------|---------------|
> | 1 | IU-3 | Test Strategy | No test scenarios defined |
> | 2 | IU-5 | File Mapping | Paths not specified |
> | ...
>
> Which item would you like to work on first? Or would you like to focus on something else?

Let the user choose — they may pick from the backlog or bring new topics.
