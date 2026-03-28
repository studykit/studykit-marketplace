---
name: co-revise
description: "This skill should be used when the user has Git Issues describing problems in upstream artifacts and needs to revise them, when the user says 'fix upstream artifact', 'address feedback', 'revise requirement', 'revise story', 'revise domain model', 'revise architecture', 'resolve feedback issues', 'co-revise', or when a co-think session produced feedback issues that need to be resolved in upstream artifact files."
argument-hint: <GitHub issue number(s) or 'open' to list open feedback issues>
allowed-tools: Read, Write, Edit, Agent, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode
---

# Artifact Revision from Feedback Issues

Takes Git Issues that describe problems in upstream artifacts and walks through each one with the user to revise the original files. Through one-question-at-a-time dialogue, clarify the gap, determine the fix, and update the artifact file(s) in place.

## Artifact Types and Labels

The co-think pipeline produces four artifact types. Each has a corresponding GitHub Issue label:

| Artifact | Label | File suffix |
|----------|-------|-------------|
| Job Stories | `story` | `.story.md` |
| Functional Requirements | `requirement` | `.requirement.md` |
| Conceptual Model | `domain` | `.domain.md` |
| Architecture | `architecture` | `.architecture.md` |

### Issue Types

Issues without a `feedback` label are artifact records (canonical records of stories, requirements, etc.) and are not actionable by co-revise. **co-revise only processes issues that have the `feedback` label.**

## Input

Read the GitHub Issue(s) specified: **$ARGUMENTS**

- If issue number(s) are provided, fetch each issue via the GitHub MCP tools. Verify the issue has the `feedback` label — if it doesn't, inform the user that issues without `feedback` are records and not revision targets.
- If `open` is provided, list all open issues that have the `feedback` label.
- If no argument is provided, ask the user for the issue number(s) or whether to list open feedback issues.

For each issue, extract:

1. **Labels** — the artifact label determines which artifact type to revise; the `feedback` label confirms it's actionable
2. **Issue body** — describes the problem, related item references (issue numbers, e.g., #42), and the originating context
3. **Target artifact file** — identified from the issue body or by searching `A4/co-think/` for the relevant artifact file

Read the target artifact file(s).

Then present:

> **Issues to address:**
>
> | # | Issue | Label | Target file | Summary |
> |---|-------|-------|-------------|---------|
> | 1 | #42 | requirement | `<path>` | FR-3, FR-5: missing error handling |
> | 2 | #43 | story | `<path>` | Story #2: vague situation |
> | 3 | #44 | domain | `<path>` | Missing state for Concept X |
>
> Which issue would you like to start with?

## Step 0: Explore the Codebase

Before starting revisions, explore the current codebase to understand:

- **Project structure** — directories, key files, tech stack
- **Existing features** — what's already built, patterns in use
- **Domain terms already in use** — naming conventions, existing entities

This grounds the revisions in reality. Reference what you find during the interview — e.g., "The codebase already handles this case in the auth module. Should the requirement align with that pattern?"

## Conversation Flow

Work through issues one at a time. The user chooses which issue to address and in what order. Do NOT auto-advance to the next issue.

### For Each Issue

1. **Present the issue** — show the issue description, label, and the relevant content from the target artifact file.
2. **Interview** — ask clarifying questions one at a time to determine exactly how the artifact should be revised. Tailor questions to the artifact type:

   **For stories (`story` label):**
   - Is the situation specific enough?
   - Is the action concrete?
   - Is the outcome measurable?

   **For requirements (`requirement` label):**
   - What behavior is missing or unclear?
   - What should happen in this scenario?
   - Are there edge cases to consider?
   - Does this affect other FRs?

   **For domain models (`domain` label):**
   - Is a concept missing or misdefined?
   - Is a relationship missing or incorrect?
   - Are state transitions incomplete?

   **For architecture (`architecture` label):**
   - Is a component missing or misscoped?
   - Is an information flow incomplete?
   - Does the DB schema need adjustment?

3. **Draft the revision** — present the proposed change for the user to review:

   > **Issue #42:** FR-3, FR-5 — missing error handling for concurrent edits
   >
   > **Proposed change to FR-3:**
   > Add to Error handling:
   > - When two users edit the same item simultaneously, the second save attempt shows "This item was modified by another user. Review changes before saving."
   >
   > **Proposed change to FR-5:**
   > Add to System behavior step 4:
   > - Before saving, check the item's last-modified timestamp against the loaded version.
   >
   > Does this capture it? Anything to adjust?

4. **Apply the revision** — after confirmation, update the artifact file using the Edit tool. Use Write only when the entire file needs rewriting.
5. **Update frontmatter** — increment the `revision` field by 1 and set `last_revised` to today's date.
6. **Close the issue** — add a comment to the GitHub Issue summarizing what was changed, then close it.
7. **Write the modified file.**
8. **Show progress** and ask what's next:

   > | # | Issue | Label | Target file | Status |
   > |---|-------|-------|-------------|--------|
   > | 1 | #42 | requirement | `<path>` | Done |
   > | 2 | #43 | story | `<path>` | Open |
   > | 3 | #44 | domain | `<path>` | Open |
   >
   > What would you like to work on next? Pick an issue, revisit a resolved one, or wrap up.

### Navigation Rules

The user controls all transitions. The user may:

- Pick issues in any order
- Skip issues they want to defer
- Revisit already-resolved issues to adjust the fix
- Stop at any point (leaving remaining issues open for a future session)

## Revision Guidelines

- **Stay within scope.** Only revise what the issue identifies. Don't refactor the entire artifact.
- **Preserve existing content.** Add or modify specific sections — don't rewrite from scratch.
- **Use the Edit tool** for surgical updates. Use Write only when the entire file needs rewriting.
- **Cross-issue awareness.** If resolving one issue affects another issue's content, note it: "This change also addresses part of issue #44. Want to check that one next?"
- **Flag new discoveries.** If the interview reveals a gap not in the original issues, ask: "This seems like a new issue. Should I create a new GitHub Issue for it?"

## Downstream Propagation

After all selected issues are resolved (or when the user wants to check downstream impact), perform downstream impact analysis.

### Pipeline Order

```
story → requirement → domain → architecture
```

Each artifact type can affect all downstream types.

### Impact Analysis

For each resolved issue:

1. Identify which downstream artifacts exist (check `A4/co-think/` for files whose source blockquote links back to the revised file).
2. Analyze whether the revision changes behavior, contracts, or concepts that downstream artifacts depend on.
3. Present findings:

   > **Downstream impact analysis for issue #42 (requirement revision):**
   >
   > | Downstream artifact | Impact | Reason |
   > |--------------------|--------|--------|
   > | `<domain-file>` | Likely affected | FR-3 change adds new error state not in domain model |
   > | `<architecture-file>` | Likely affected | FR-5 change requires new component interaction |
   >
   > Should I create downstream issues for these?

4. If the user approves, create GitHub Issues for each affected downstream artifact:
   - Apply the appropriate artifact label (`domain`, `architecture`, etc.) + `feedback`
   - Reference the upstream issue in the body
   - Describe the specific impact and what needs to change
5. Link the upstream issue to the downstream issues via a comment.

### Chained Revision

After downstream issues are created, ask the user:

> "Downstream issues have been created. Would you like to continue with co-revise to address them now, or handle them in a separate session?"

If the user wants to continue, loop back to the main conversation flow with the newly created issues.

## Wrapping Up

The session ends only when the user says so. Never conclude on your own — even if all issues are resolved, the user may want to revisit or add new items.

When the user indicates they're done:

1. **Run the appropriate reviewer agent** — for each modified artifact type, invoke the corresponding reviewer agent:
   - `story` → `story-reviewer`
   - `requirement` → `requirement-reviewer`
   - `domain` → `domain-reviewer`
   - `architecture` → `architecture-reviewer`
2. **Present the review results** — show the user the review report. For each flagged issue, walk through it one at a time. The user can accept, modify, or dismiss each suggestion.
3. **Update the artifact file(s)** with any revisions from the review.
4. **Finalize** — ensure all modified artifacts reflect the conversation outcomes.
5. **Write all modified files.**
6. **Report summary:**

   > **Session summary:**
   > - Issues resolved: 3 of 5
   > - Files modified: `<file paths>`
   > - Downstream issues created: #45, #46
   > - Remaining open issues: 2
