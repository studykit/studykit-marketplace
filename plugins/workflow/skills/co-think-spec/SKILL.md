---
name: co-think-spec
description: "This skill should be used when the user has Job Stories or user stories and needs to turn them into detailed functional requirements, when the user says 'detail this', 'write specs', 'make this buildable', 'turn stories into requirements', 'spec this out', or when Job Stories from co-think-story need to be shaped into functional specifications detailed enough for AI to develop."
argument-hint: <path to Job Story file>
allowed-tools: Read, Write, Bash, Agent, WebSearch, WebFetch
---

# Functional Specification Builder

Takes Job Stories and turns them into functional requirements detailed enough for AI to develop. Through one-question-at-a-time dialogue, clarify each story's behavior, edge cases, and constraints — then produce a structured specification.

## Input

Read the Job Story file provided: **$ARGUMENTS**

If no file is provided, ask the user for the path or paste content.

After reading, list all Job Stories found and confirm with the user before proceeding.

## Step 0: Explore the Codebase

Before starting the specification, explore the current codebase to understand:

- **Project structure** — directories, key files, tech stack
- **Existing features** — what's already built, patterns in use
- **Constraints** — frameworks, conventions, dependencies that the spec should respect

This grounds the specification in reality. Reference what you find during the interview — e.g., "I see the project already has a notification system. Should this feature use it?"

## Step 1: Determine Software Type

Before diving into individual stories, ask the user:

> "Does this software have a user interface (web, mobile, desktop, CLI with TUI), or is it non-UI (API, library, automation script, plugin)?"

This determines how functional requirements are structured and whether mock UIs are useful.

| Type | Requirements focus |
|------|-------------------|
| **UI** | Screens, user interactions, navigation, visual states, input/output per screen |
| **Non-UI** | Commands/endpoints, input/output contracts, business logic rules, integration points |

If the software has both UI and non-UI parts, note which stories belong to which.

## Step 2: Story-by-Story Specification

Work through stories one at a time. For each story:

1. **Present the story** and confirm it's still relevant.
2. **Check story size** — if the story is too big, decompose it first (see Story Decomposition).
3. **Decide mock need** — for UI stories, judge whether a mock UI would make the conversation easier (see Mock UI).
4. **Ask clarifying questions** — one at a time — to fill in the gaps.
5. **Draft the spec** and present it for confirmation.
6. **Stay until concrete** — do not move to the next story until the current spec is detailed enough for AI to develop. Keep asking until all gaps are filled.
7. Move to the next story only when the user confirms the current spec is complete.

### Story Decomposition

A story is too big when it contains 3 or more independent actions or behaviors.

When you spot a big story:

1. Tell the user: "This story seems to cover multiple distinct behaviors. I'd like to break it down."
2. Propose sub-stories in Job Story format (When / I want to / so I can).
3. Ask the user to confirm, adjust, or add.
4. Once confirmed, proceed to specify each sub-story individually.

The sub-stories replace the original in the final output.

### Mock UI

For UI software, judge whether creating a mock UI would help clarify the spec for the current story. A mock is useful when:

- The screen layout or flow is hard to describe in words alone
- Multiple related stories share the same screen — mock them together
- The user seems uncertain about how the UI should work

When a mock is helpful:

1. Use the **mock-html-generator** agent to create an HTML mock. Save mock files to `A4/spec/mock/<topic-slug>/` relative to working directory.
2. Present the mock to the user and gather feedback.
3. Iterate on the mock if needed.
4. Use the feedback to refine the spec. Record the mock file path in the spec.

When a mock is NOT needed (simple interactions, clear behavior), skip it and proceed with dialogue only.

### What to clarify per story

#### For UI software

- **Where does this happen?** — Which screen or view? New screen or part of existing one?
- **What does the user see?** — Key elements, information displayed, initial state.
- **What does the user do?** — Interactions (click, type, drag, etc.), step-by-step flow.
- **What changes?** — State transitions, feedback, what the user sees after the action.
- **What can go wrong?** — Error states, validation, edge cases. What does the user see when something fails?

#### For non-UI software

- **What triggers this?** — Command, API call, event, schedule?
- **What goes in?** — Input format, required/optional parameters, validation rules.
- **What comes out?** — Output format, success response, data structure.
- **What are the rules?** — Business logic, conditions, calculations, ordering.
- **What can go wrong?** — Error cases, invalid input handling, failure modes.

### Question techniques

- Ask about **concrete scenarios**: "If a user does X in this situation, what should happen?"
- Ask about **edge cases**: "What if the input is empty? What if there are 10,000 items?"
- Ask about **boundaries**: "Is there a limit? What's the maximum/minimum?"
- When the user is unsure, offer 2-3 concrete options to choose from.

## Core Rule: One Question at a Time

Ask exactly ONE question per turn. Wait for the answer. Then ask the next.

## Progressive Specification

As each story gets clarified, draft its spec and present it for confirmation — don't wait until the end.

**How to present:**

> Here's the spec for Story #1:
>
> **Story:** When [situation], I want to [action], so I can [outcome].
>
> **Screen:** Dashboard > Summary panel
> **User action:** Clicks "Generate Summary" button
> **System behavior:**
> 1. Shows loading indicator
> 2. Extracts key decisions and action items from transcript
> 3. Displays summary in editable text area
>
> **Validation:** Transcript must have at least 3 entries
> **Error:** "Not enough content to summarize" message
>
> Does this capture it? Anything to adjust or add?

After confirmation:

1. **Write to file immediately** — append the confirmed spec to the output file so the user can review it in their editor at any time. Create the file on the first confirmed spec using the output format. Update the file after each subsequent confirmation.
2. **Show progress table** — present a summary of all stories and their status:

> | # | Story | Key behavior | Status |
> |---|-------|-------------|--------|
> | 1 | Generate meeting summary | Clicks button → extracts decisions → shows editable summary | Done |
> | 2 | Share summary with team | — | In progress |
> | 3 | Filter by date range | — | Pending |

3. Move to the next story.

## Facilitation Guidelines

- **Stay concrete.** Avoid abstract discussions — always anchor to specific behavior.
- **Use the user's language.** Don't introduce technical jargon unless the user does.
- **Don't design the solution.** Capture what the software should do, not how to implement it.
- **Flag dependencies.** If one story's spec depends on another, note it explicitly.
- **Every 3-4 stories:** Brief progress snapshot — what's done, what's next.

## Wrapping Up

The specification ends only when the user says so. Never conclude on your own — even if all stories seem covered, the user may want to revisit or go deeper. Keep working until the user explicitly ends the session.

When the user indicates they're done:

1. **Finalize the file** — review the entire output file and ensure all conversation outcomes are reflected. Apply any changes or feedback given during the session that may not have been captured in incremental updates. The final file must be the single source of truth.
2. **Present the final spec** to the user for last confirmation.
3. **Write the file** using the Write tool.
4. **Stage the file** — run `git add <file_path>` to include it in version control.
5. **Report the path** so the user can reference it.

### Output Format

```markdown
---
topic: "<topic>"
date: <YYYY-MM-DD>
source: "<path to Job Story file>"
type: <ui | non-ui | mixed>
---
# Functional Specification: <topic>

## Overview
<Brief summary of what this software does and who it's for. Derived from the Job Stories.>

## Job Stories Reference
<List all Job Stories from the source file for traceability. If any were decomposed, show the sub-stories with a note referencing the original.>

## Functional Requirements

### FR-1: <short title>
**Story:** When [situation], I want to [action], so I can [outcome].

<!-- For UI -->
**Screen/View:** <where this happens>
**User action:** <what the user does>
**System behavior:**
1. <step 1>
2. <step 2>
...
**Validation:** <input rules, constraints>
**Error handling:** <what happens when things go wrong>
**Mock:** <path to mock HTML file, if created>

<!-- For Non-UI -->
**Trigger:** <what initiates this>
**Input:** <format, parameters, validation>
**Processing:** <business logic, rules, steps>
**Output:** <format, structure, response>
**Error handling:** <failure modes, error responses>

**Dependencies:** <other FRs this depends on, if any>

### FR-2: <short title>
...

## Open Questions
<Unresolved decisions or ambiguities to revisit.>
- ...
```

**Required sections**: Overview, Job Stories Reference, Functional Requirements.
**Conditionally required:**
- **Open Questions** — if unresolved topics remain
