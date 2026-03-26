---
name: co-revise-requirement-with-domain
description: "This skill should be used when the user has a domain model with feedback TODOs and needs to revise existing functional requirements, when the user says 'fix requirement from domain model', 'address domain model feedback', 'requirement revision', 'resolve domain model TODOs', 'update requirement from domain model', 'revise requirement', 'domain model feedback', or when a co-think-domain session produced TODO items that need to be resolved in the original requirement files."
argument-hint: <path to domain model document>
allowed-tools: Read, Write, Edit, Agent, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode
---

# Requirement Revision from Domain Model Feedback

Takes a domain model's Spec Feedback TODO list and walks through each item with the user to revise the original functional requirements. Through one-question-at-a-time dialogue, clarify the gap, determine the fix, and update the requirement file(s) in place.

## Input

Read the domain model document provided: **$ARGUMENTS**

If no file is provided, ask the user for the path.

After reading, extract:

1. **Spec Feedback TODOs** — the `## Spec Feedback` section containing `- [ ]` items
2. **Source requirement file(s)** — from the `source` frontmatter field (wikilinks to requirement files)

Resolve the requirement file paths by searching the `A4/co-think/` directory for files matching the wikilink filenames.

Read all referenced requirement files.

Then present:

> **Domain model document:** `<path>`
> **Source requirement(s):** `<requirement file path(s)>`
>
> **Spec Feedback TODOs:**
>
> | # | Status | Related FRs | Issue |
> |---|--------|-------------|-------|
> | 1 | Open   | FR-3, FR-5  | <reason> |
> | 2 | Open   | FR-1        | <reason> |
> | 3 | Done   | FR-2, FR-4  | <reason> — resolved: <explanation> |
>
> Which TODO would you like to start with?

## Step 0: Explore the Codebase

Before starting revisions, explore the current codebase to understand:

- **Project structure** — directories, key files, tech stack
- **Existing features** — what's already built, patterns in use
- **Domain terms already in use** — naming conventions, existing entities

This grounds the revisions in reality. Reference what you find during the interview — e.g., "The codebase already handles this case in the auth module. Should the requirement align with that pattern?"

## Conversation Flow

Work through TODOs one at a time. The user chooses which TODO to address and in what order. Do NOT auto-advance to the next TODO.

### For Each TODO

1. **Present the TODO** — show the issue description, related FR numbers, and the relevant FR content from the requirement file.
2. **Interview** — ask clarifying questions one at a time to determine exactly how the requirement should be revised:
   - What behavior is missing or unclear?
   - What should happen in this scenario?
   - Are there edge cases to consider?
   - Does this affect other FRs?
3. **Draft the revision** — present the proposed requirement change for the user to review:

   > **TODO #1:** FR-3, FR-5 — missing error handling for concurrent edits
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

4. **Apply the revision** — after confirmation, update the requirement file using the Edit tool. Keep the FR's `[status:: final]` if it was already final, or leave as `[status:: draft]` if it was draft.
5. **Mark the TODO resolved** — update the domain model document:
   - Change `- [ ]` to `- [x]`
   - Append resolution note: ` — resolved: <brief explanation of what was changed>`
   - Example: `- [x] FR-3, FR-5: missing error handling for concurrent edits — resolved: added optimistic locking check and conflict error message`
6. **Write both files** — save the updated requirement file and domain model document.
7. **Show progress** and ask what's next:

   > | # | Status | Related FRs | Issue |
   > |---|--------|-------------|-------|
   > | 1 | Done   | FR-3, FR-5  | concurrent edit handling — resolved |
   > | 2 | Open   | FR-1        | missing validation for empty input |
   > | 3 | Open   | FR-2, FR-4  | undefined state transition |
   >
   > What would you like to work on next? Pick a TODO, revisit a resolved one, or wrap up.

### Navigation Rules

The user controls all transitions. The user may:

- Pick TODOs in any order
- Skip TODOs they want to defer
- Revisit already-resolved TODOs to adjust the fix
- Stop at any point (leaving remaining TODOs open for a future session)

## Revision Guidelines

- **Stay within scope.** Only revise what the TODO identifies. Don't refactor the entire requirement.
- **Preserve existing content.** Add or modify specific sections — don't rewrite FRs from scratch.
- **Use the Edit tool** for surgical updates to requirement files. Use Write only when the entire file needs rewriting.
- **Cross-TODO awareness.** If resolving one TODO affects another TODO's FRs, note it: "This change also addresses part of TODO #3. Want to check that one next?"
- **Flag new discoveries.** If the interview reveals a gap not in the original TODO list, ask: "This seems like a new issue not in the domain model feedback. Should I add it as a new TODO?"

## Wrapping Up

The session ends only when the user says so. Never conclude on your own — even if all TODOs are resolved, the user may want to revisit or add new items.

When the user indicates they're done:

1. **Run the requirement-reviewer agent** — invoke the `requirement-reviewer` agent on each modified requirement file. The agent evaluates revised requirements for behavior completeness, input/output clarity, edge cases, testability, ambiguity, dependencies, and overlap.
2. **Present the review results** — show the user the review report. For each flagged issue, walk through it one at a time:
   - `INCOMPLETE` — ask what's missing and fill it in
   - `UNDERSPECIFIED` — propose concrete I/O details and ask for confirmation
   - `MISSING EDGES` — present the edge cases and ask how each should be handled
   - `UNTESTABLE` — suggest measurable criteria to replace subjective language
   - `AMBIGUOUS` — present the precise alternative and ask if it captures the intent
   - `UNCLEAR DEPS` — ask the user to clarify the relationship
   - `OVERLAPS` — ask whether to merge, differentiate, or remove the overlapping requirements
   - The user can accept, modify, or dismiss each suggestion. Respect their decision.
3. **Update the requirement file(s)** with any revisions from the review.
4. **Finalize** — ensure all modified FRs reflect the conversation outcomes.
5. **Write all modified files** — requirement file(s) and domain model document.
6. **Report summary:**

   > **Session summary:**
   > - TODOs resolved: 3 of 5
   > - Requirement files modified: `A4/co-think/2026-03-20-1430-auth-flow.requirement.md`
   > - Domain model document updated: `A4/co-think/2026-03-22-1100-auth-domain.domain.md`
   > - Remaining open TODOs: 2
   >
   > Files staged for commit.
