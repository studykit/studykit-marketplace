# Iteration Entry Procedure

When entering **Iteration** mode (an existing `.usecase.md` file is found), perform these checks before starting work.

## 1. Read and Check for Unreflected Reports

Read the existing file completely. Check the frontmatter `reflected_files` list, then check for companion reports not listed in `reflected_files`:

- Review reports (`<topic-slug>.usecase.review-*.md`) — read each unreflected review and extract NEEDS REVISION items and Cross-UC findings
- Exploration reports (`<topic-slug>.usecase.exploration-*.md`) — summarize UC candidates found
- For reports already in `reflected_files`, cross-check the Change Log to confirm their findings were recorded. Do not re-present resolved findings.

## 2. Check Source File Changes

If `sources` exists in frontmatter, compare the stored `sha` against the current file for each source:

1. Run `git hash-object <source-file-path>` to get the current SHA.
2. If SHA matches → no changes, skip.
3. If SHA differs → run `git diff <stored-sha> <current-sha>` to see what changed.
4. Present the changes to the user: "The source file has been updated. Changes: [list]. Review these changes before continuing?"
5. Walk through each change with the user to determine impact on existing use cases (new UCs needed, existing UCs to update, actors to add/modify).
6. After reflecting, update `sources` in frontmatter (`sha` and any other tracked fields). If the working file content changed, **increment `revision`** and update `revised` timestamp.

## 3. Present Status Summary

Present a brief status summary:

- Number of confirmed use cases
- Actors identified so far
- Open Items from previous session (if any)
- Open Questions (if any)
- Unreflected review findings (if any) — list NEEDS REVISION items with UC ID, field, and issue
- Unreflected exploration results (if any) — summarize the UC candidates found

## 4. Present Work Backlog

Present the Open Items table (if it exists) as a selectable work backlog:

> **Open Items from last session:**
> | # | Section | Item | What's Missing | Priority |
> |---|---------|------|---------------|----------|
> | 1 | UC-3 | Situation | Too vague — needs concrete trigger | High |
> | 2 | Actors | — | Implicit approver actor not declared | Medium |
>
> Which items would you like to work on? Or would you prefer to add new use cases?

## 5. User Chooses What to Work On

Possible activities:

- **Add new use cases** — resume the Discovery Loop (step 2) as normal
- **Address review findings** — walk through NEEDS REVISION items from unreflected review reports one by one. After all findings are addressed (or explicitly deferred), add the review file name to `reflected_files` and record each change in the Change Log with the review file as Source. If the working file content changed, **increment `revision`** and update `revised` timestamp.
- **Explore UC candidates from explorer** — review and flesh out UC candidates from unreflected exploration reports. After reflecting, add the exploration file name to the frontmatter `reflected_files` list. If the working file content changed, **increment `revision`** and update `revised` timestamp.
- **Clarify existing UCs** — revisit flagged use cases one by one, asking targeted questions to fill gaps
- **Refine actors** — add missing actors, split actors with privilege differences, add system actors
- **Split oversized UCs** — process previously deferred SPLIT suggestions
- **Re-analyze relationships** — update dependencies, reinforcements, and groups after changes
- **Resolve Open Questions** — address unresolved topics from previous sessions

## Iteration Rules

- Preserve all previously confirmed use cases — never remove or reorder them unless the user explicitly requests it.
- New use cases get the next available UC-N ID (continue numbering from where the previous session left off).
- When modifying an existing UC, show the before/after and confirm with the user before updating.
- Increment `revision` in frontmatter and update `revised` timestamp when: before launching a reviewer/explorer subagent (stamps the reviewed snapshot), reflecting external input (source file changes, review findings, exploration results) that changes the working file content, or closing the session. Routine updates during the interview (UC confirmation, actor discovery) do not increment revision.
- Session history (including Interview Transcript) is stored in a separate history file (`<topic-slug>.usecase.history.md`). See `${CLAUDE_SKILL_DIR}/references/session-history.md` for the format.
