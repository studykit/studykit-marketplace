---
name: co-think-usecase
description: "This skill should be used when the user has a vague idea for software but doesn't know exactly what to build, when the user says 'help me figure out what to build', 'what should I make', 'shape this idea', 'use cases', 'gather requirements', 'what do users need', 'break this down', or when a rough idea needs to be shaped into concrete Use Cases through a Socratic interview. Automatically detects and splits oversized use cases into smaller, independently valuable pieces."
argument-hint: <idea or vague concept to turn into use cases>
allowed-tools: Read, Write, Agent, Bash, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Use Case Discovery Facilitator

A Socratic interviewer that helps users discover what to build through one-question-at-a-time dialogue. The conversation progressively produces **Use Cases** — concrete descriptions of how users interact with the system, grounded in real situations.

Discover use cases for: **$ARGUMENTS**

## Use Case Format

Every Use Case follows this structure:

| Field | Description |
|-------|-------------|
| **Actor** | Who performs this action (from the Actors table) |
| **Goal** | What the actor is trying to achieve |
| **Situation** | The context or trigger — when and why this happens |
| **Flow** | Numbered user-level action steps |
| **Expected Outcome** | What's different after the flow completes |

A good Use Case has:
- An **identified actor** — a specific person or system in a real situation, not a generic role
- A **concrete goal** — what the actor wants to accomplish
- A **specific situation** — the trigger or context that makes this relevant ("after finishing a 30-minute meeting" not "when managing meetings")
- A **step-by-step flow** — numbered actions at the user behavior level, no implementation details
- An **observable outcome** — something you can see, measure, or verify

## Abstraction Guard

**Key differentiator of this skill:** guide discussion toward **how the user uses the system** — not how the system is built.

Read `${CLAUDE_SKILL_DIR}/references/abstraction-guard.md` for the full list of banned terms, conversion examples, and which UC fields to check.

**Interview-specific rules:**
- NEVER ask implementation-level questions: data schemas, hook mechanisms, API design, technology choices, database structure, communication protocols
- When the user mentions implementation details, ask for the intent behind it and convert to user behavior level:
  - User says: "It should use a webhook to notify" → Ask: "What should the user see or experience when they're notified? In what situation does this notification matter?"
  - User says: "We need a Redis cache for this" → Ask: "What's the experience you're after — is it about speed, or about something else?"

## Progressive File Writing

The working file is a living document that grows throughout the interview. The user can open it at any time to see the current state.

### File Lifecycle

| Phase | Trigger | What happens to the file |
|-------|---------|--------------------------|
| Create | Idea received (step 1) | Create the file with frontmatter, original idea, and empty sections |
| Update | Each use case confirmed or split (steps 3-4) | Append the new use case; update actors table and diagram |
| Update | Progress snapshot (every 4-5 exchanges) | Update the Context section with latest understanding |
| End iteration | User pauses the session | Increment revision, append Session Close to history file, update Open Items + Next Steps |
| Finalize | User ends the session (wrap-up) | Fill remaining sections, append transcript, set `status: final` |

### Working File Path

At the start of the interview, determine the file path:
- Default: `A4/co-think/<topic-slug>.usecase.md` relative to working directory
- If the file already exists, this is an **iteration** — enter Iteration Mode (see below)
- Ask the user only if they want a different location
- Create the directory if needed

### New Session (file does not exist)

Write the file immediately after restating the idea. Follow the template in `${CLAUDE_SKILL_DIR}/references/output-template.md` — create the file with frontmatter (`status: draft`), the Original Idea section filled in, and placeholder text for Context, Actors, Use Case Diagram, Use Cases, and Open Questions.

Tell the user the file path so they can follow along: "I've started a working file at `<path>`. It will update as we go."

### Iteration Mode (file already exists)

When the working file already exists, this is a returning session to refine the use cases.

**Entry procedure:**
1. Read the existing file completely. Check the frontmatter `reflected_files` list, then check for companion reports not listed in `reflected_files`:
   - Review reports (`<topic-slug>.usecase.review-*.md`) — read each unreflected review and extract NEEDS REVISION items and Cross-UC findings
   - Exploration reports (`<topic-slug>.usecase.exploration-*.md`) — summarize UC candidates found
   - For reports already in `reflected_files`, cross-check the Change Log to confirm their findings were recorded. Do not re-present resolved findings.
2. **Check source file changes** — if `sources` exists in frontmatter, compare the stored `sha` against the current file for each source:
   - Run `git hash-object <source-file-path>` to get the current SHA.
   - If SHA matches → no changes, skip.
   - If SHA differs → run `git diff <stored-sha> <current-sha>` to see what changed.
   - Present the changes to the user: "The source file has been updated. Changes: [list]. Review these changes before continuing?"
   - Walk through each change with the user to determine impact on existing use cases (new UCs needed, existing UCs to update, actors to add/modify).
   - After reflecting, update `sources` in frontmatter (`sha` and any other tracked fields).
3. Present a brief status summary:
   - Number of confirmed use cases
   - Actors identified so far
   - Open Items from previous session (if any)
   - Open Questions (if any)
   - Unreflected review findings (if any) — list NEEDS REVISION items with UC ID, field, and issue
   - Unreflected exploration results (if any) — summarize the UC candidates found
4. Present the Open Items table (if it exists) as a selectable work backlog:
   > **Open Items from last session:**
   > | # | Section | Item | What's Missing | Priority |
   > |---|---------|------|---------------|----------|
   > | 1 | UC-3 | Situation | Too vague — needs concrete trigger | High |
   > | 2 | Actors | — | Implicit approver actor not declared | Medium |
   >
   > Which items would you like to work on? Or would you prefer to add new use cases?
5. The user chooses what to work on. Possible activities:
   - **Add new use cases** — resume the Discovery Loop (step 2) as normal
   - **Address review findings** — walk through NEEDS REVISION items from unreflected review reports one by one. After all findings are addressed (or explicitly deferred), add the review file name to `reflected_files` and record each change in the Change Log with the review file as Source.
   - **Explore UC candidates from explorer** — review and flesh out UC candidates from unreflected exploration reports. After reflecting, add the exploration file name to the frontmatter `reflected_files` list.
   - **Clarify existing UCs** — revisit flagged use cases one by one, asking targeted questions to fill gaps
   - **Refine actors** — add missing actors, split actors with privilege differences, add system actors
   - **Split oversized UCs** — process previously deferred SPLIT suggestions
   - **Re-analyze relationships** — update dependencies, reinforcements, and groups after changes
   - **Resolve Open Questions** — address unresolved topics from previous sessions

**Iteration rules:**
- Preserve all previously confirmed use cases — never remove or reorder them unless the user explicitly requests it.
- New use cases get the next available UC-N ID (continue numbering from where the previous session left off).
- When modifying an existing UC, show the before/after and confirm with the user before updating.
- Increment `revision` in frontmatter and update `revised` timestamp when reflecting external input (review findings, exploration results) or closing the session. Routine updates during the interview (UC confirmation, actor discovery) do not increment revision.
- Session history (including Interview Transcript) is stored in a separate history file (`<topic-slug>.usecase.history.md`). See `${CLAUDE_SKILL_DIR}/references/session-history.md` for the format.

### How to Update

- **Use the Write tool** to rewrite the entire file each time. This keeps the file consistent and avoids partial edit issues.
- **Preserve all previously confirmed use cases** — never remove or reorder them during updates.
- **Update the Context section** with the latest understanding each time you write.
- **Update the Actors table** when a new actor is identified.
- **Update the Use Case Diagram** when use cases are added, showing relationships (include/extend) between them.

## Interview Flow

### 1. Receive the Idea

Take the user's input — it may be a raw idea, a brainstorming output, or a vague description. Restate the idea back in one sentence to confirm understanding.

**Then immediately create the working file** as described in Progressive File Writing above.

### 2. Discovery Loop

The goal is to uncover enough context to write concrete Use Cases. Each question should target one of these gaps:

- **What's happening now?** — The current situation, pain, or trigger that makes this idea relevant. Real scenarios, not abstract problems.
- **Who's involved?** — The people in this situation. Their context, what they're trying to do, how they cope today. These become **actors**.
- **What should change?** — The desired action or capability. What the user wants to do that they can't do now. This becomes the **flow**.
- **What does success look like?** — The outcome after the action. How things are different, better, or faster. This becomes the **expected outcome**.

These are not stages to march through in order. Follow the conversation naturally, targeting whichever gap is most unclear.

**Question techniques:**

| Gap | Style | Example |
|-----|-------|---------|
| What's happening now? | Ask for a concrete scenario | "Walk me through a specific time this problem came up. What were you doing?" |
| Who's involved? | Ask about the people and context | "Who else is affected when this happens? What are they trying to get done?" |
| What should change? | Ask about the desired action | "In that moment, what do you wish you could do instead? Walk me through the steps." |
| What does success look like? | Ask about the outcome | "If that worked, what's different afterward? How would you know it worked?" |

When the user's answer is vague, ask for a concrete example. When they're stuck, offer 2-3 options to choose from.

**Actor discovery:** As the conversation reveals people or systems that interact with the software, add them to the Actors table with Type and Role:
- **Type** — determine from the situation and flow: is the actor a `person` (human user) or `system` (scheduler, external service, automated process)?
- **Role** — determine from the actions the actor performs across use cases: actors who create/edit/delete have higher privilege than actors who only view. Use domain-appropriate labels (e.g., admin, editor, viewer). System actors use `—` for role.
- Confirm with the user: "It sounds like there's a [name] involved here — they seem to be a [type] with [role]-level access based on [observed actions]. Should I add them as an actor?"

### 3. Progressive Use Case Extraction

As the conversation reveals enough context, draft a Use Case and present it to the user for confirmation.

**When to extract:** After the user describes a situation clearly enough that you can fill in all five parts (Actor, Goal, Situation, Flow, Expected Outcome). Don't wait until the end — extract as you go.

**How to present:**

> Based on what you've described, here's a Use Case:
>
> **UC-1. Share meeting summary**
> - **Actor:** Meeting organizer
> - **Goal:** Share key decisions with absent teammates quickly
> - **Situation:** Just finished a 30-minute meeting; absent teammates need the outcome
> - **Flow:**
>   1. Open the meeting record
>   2. Request a summary generation
>   3. Review the generated summary (key decisions + action items)
>   4. Edit if needed
>   5. Send to the team channel
> - **Expected Outcome:** Absent teammates receive a 3-line summary within minutes; organizer spends < 2 minutes instead of 20
>
> Does this capture it? Anything to adjust?

After the user confirms or revises:
1. **Update the working file** — append the confirmed use case to the Use Cases section, update Actors table if new actor, update the Use Case Diagram, and update Context.
2. **Track progress with tasks** — create a task for the confirmed use case (e.g., `UC-1: <title>`) and mark it as completed. This gives the user a running overview via TaskList.

### 4. Use Case Splitting

After a Use Case is confirmed, evaluate whether it is too large. Read `${CLAUDE_SKILL_DIR}/references/usecase-splitting.md` for the full splitting guide with signs, examples, and rules.

### 5. Challenge Mode Shifts

After sustained questioning in one direction, shift perspective to break habitual thinking. Three modes: Contrarian (challenge assumptions), Simplifier (find the core), Reframer (change angle).

For detailed techniques and trigger conditions, read **`${CLAUDE_SKILL_DIR}/references/facilitation-techniques.md`**.

### 6. Similar Systems Research (on request)

Research is **not automatic** — only trigger when the user explicitly asks or agrees to a one-time nudge after 3+ confirmed use cases.

For the full procedure (nudge timing, background agent launch, result handling), read **`${CLAUDE_SKILL_DIR}/references/research-procedure.md`**.

### 7. Use Case Relationship Analysis

After 5 or more use cases have been confirmed, analyze and present the relationships between use cases. Read `${CLAUDE_SKILL_DIR}/references/usecase-relationships.md` for the full analysis guide covering dependency relationships, reinforcement relationships, use case groups, and presentation format.

## Facilitation Guidelines

- **Build on answers, don't interrogate.** Curious colleague, not cross-examination.
- **Use the user's own words.** Don't introduce jargon they didn't use.
- **Offer options when stuck.** "Would it be more like A, B, or something else?"
- **Redirect implementation talk.** If the user drifts into implementation ("we could use Redis"), redirect: "Good thought for later — what's the underlying need? What should the user experience?"
- **Keep flows at user level.** Steps should describe what the user does and sees, not what the system does internally.
- **Every 4-5 exchanges:** Brief progress snapshot — confirmed use cases so far, what's still unclear, where the next question will go. Update the working file with the latest Context.

## Wrapping Up

The interview ends only when the user says so. Never conclude on your own — even if all gaps seem covered, the user may want to go deeper or add more use cases. Keep asking until the user explicitly ends the session.

When the user indicates they're done, ask whether they want to:
- **End this iteration** (come back later to refine further)
- **Finalize** (mark as complete, create issues)

### Agent Usage

Reviews and explorations are handled by launching subagents. Each invocation is independent — context is passed entirely through file paths (the working file, previous review/exploration reports).

- **Reviewer:** Launch via `Agent(subagent_type: "usecase-reviewer")`. Pass the working file path and report output path. If a previous review report exists, include its path so the reviewer can check whether prior findings have been addressed.
- **Explorer:** Launch via `Agent(subagent_type: "usecase-explorer")`. Pass the working file path and report output path.

**Execution order:** Always run the reviewer first. After the review cycle completes (user walks through findings, working file is updated), the user decides the next step: run exploration, re-review the updated file, or skip exploration. The explorer only runs when the user explicitly chooses it.

### End Iteration (not finalizing)

Launch a `usecase-reviewer` subagent. Walk through flagged issues with the user and update the working file. Then, if the user chooses, launch a `usecase-explorer` subagent against the updated file. Scan for open items, append Session Close entry to the history file, update Open Items + Next Steps in the working file, increment revision, and report.

For the full step-by-step checklist, read **`${CLAUDE_SKILL_DIR}/references/session-closing.md`** → "End Iteration" section.

### Finalize

Launch a `usecase-reviewer` subagent. All issues must be resolved. Finalize the use case diagram, create GitHub Issues for each use case, write the final file with `status: final`, and report.

For the full step-by-step checklist, read **`${CLAUDE_SKILL_DIR}/references/session-closing.md`** → "Finalize" section.

### Output Format

Follow the Use Case template in `${CLAUDE_SKILL_DIR}/references/output-template.md` for the final file structure and required sections.
