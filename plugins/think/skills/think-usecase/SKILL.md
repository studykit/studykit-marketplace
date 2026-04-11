---
name: think-usecase
description: "This skill should be used when the user has a vague idea for software but doesn't know exactly what to build, when the user says 'help me figure out what to build', 'what should I make', 'shape this idea', 'use cases', 'gather requirements', 'what do users need', 'break this down', or when a rough idea needs to be shaped into concrete Use Cases through a Socratic interview. Automatically detects and splits oversized use cases into smaller, independently valuable pieces."
argument-hint: <idea or vague concept to turn into use cases>
allowed-tools: Read, Write, Agent, Bash, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Use Case Discovery Facilitator

A Socratic interviewer that helps users discover what to build through one-question-at-a-time dialogue. The conversation progressively produces **Use Cases** — concrete descriptions of how users interact with the system, grounded in real situations.

Discover use cases for: **$ARGUMENTS**

## Use Case Format

Every Use Case has five fields: **Actor** (specific person or system, not generic role), **Goal** (what they want to accomplish), **Situation** (concrete trigger — "after finishing a 30-minute meeting" not "when managing meetings"), **Flow** (numbered user-level action steps, no implementation details), and **Expected Outcome** (observable, measurable result).

## Abstraction Guard

**Key differentiator of this skill:** guide discussion toward **how the user uses the system** — not how the system is built.

Read `${CLAUDE_SKILL_DIR}/references/abstraction-guard.md` for the full list of banned terms, conversion examples, and which UC fields to check.

When the user mentions implementation details, ask for the intent behind it and convert to user behavior level.

## Progressive File Writing

The working file grows through **checkpoint writes** rather than after every confirmed item. Between checkpoints, confirmed use cases are tracked via tasks (TaskCreate/TaskUpdate). This keeps the conversation flowing without constant file I/O, while limiting data loss if the session is interrupted.

### File Lifecycle

| Phase | Trigger | What happens to the file |
|-------|---------|--------------------------|
| Create | Idea received (step 1) | Create the file with frontmatter, original idea, and empty sections |
| Checkpoint | Every 3 confirmed use cases | Batch-write all unwritten confirmed UCs, update actors table, diagram, and Context |
| Checkpoint | Interview stage transition or challenge mode shift | Write all pending confirmed content |
| Checkpoint | Before review (reviewer launch) | Write all pending confirmed content so the reviewer sees the latest state |
| End iteration | User pauses the session | Write all pending content, increment revision, append Session Close to history file, update Open Items + Next Steps |
| Finalize | User ends the session (wrap-up) | Fill remaining sections, append transcript, set `status: final` |

### Working File Path

At the start of the interview, determine the file path from **$ARGUMENTS**:

1. **Full path or filename** — if the argument matches an existing `.usecase.md` file, use it directly → Iteration Mode
2. **Partial match** — glob for `A4/*<argument>*.usecase.md`. If multiple matches, present candidates and ask the user to pick
3. **No existing file** — treat the argument as an idea. Derive a topic slug (lowercase, hyphen-separated, 2–5 words). File path: `A4/<topic-slug>.usecase.md`
   - If this path already exists → Iteration Mode
   - Otherwise → New Session

- Ask the user only if they want a different location
- Create the directory if needed

### New Session (file does not exist)

Write the file immediately after restating the idea. Follow the template in `${CLAUDE_SKILL_DIR}/references/output-template.md` — create the file with frontmatter (`status: draft`), the Original Idea section filled in, and placeholder text for Context, Actors, Use Case Diagram, Use Cases, and Open Questions.

Tell the user the file path so they can follow along: "I've started a working file at `<path>`. It will update as we go."

### Iteration Mode (file already exists)

When the working file already exists, this is a returning session to refine the use cases. Read `${CLAUDE_SKILL_DIR}/references/iteration-entry.md` and follow the entry checks (unreflected reports, source file changes, status summary, work backlog) before starting work.

### How to Update

- **Track confirmed items via tasks** — after each use case is confirmed, create a task (e.g., `UC-1: <title>`) and mark it completed. This gives the user a running overview via TaskList without writing the file.
- **Write at checkpoints only** — when a checkpoint trigger fires (see File Lifecycle), use the Write tool to rewrite the entire file with all pending confirmed content. This keeps the file consistent and avoids partial edit issues.
- **Preserve all previously confirmed use cases** — never remove or reorder them during updates.
- **Update the Context section** with the latest understanding at each checkpoint.
- **Update the Actors table** when a new actor is identified (included in the next checkpoint write).
- **Update the Use Case Diagram** when use cases are added, showing relationships (include/extend) between them.

## Interview Flow

### 1. Receive the Idea

Take the user's input — it may be a raw idea, a brainstorming output, or a vague description. Restate the idea back in one sentence to confirm understanding.

**Then immediately create the working file** as described in Progressive File Writing above.

### 2. Discovery Loop

Uncover enough context to write concrete Use Cases by targeting four gaps: **What's happening now?** (current situation/trigger), **Who's involved?** (people → actors), **What should change?** (desired action → flow), **What does success look like?** (outcome). Follow the conversation naturally, targeting whichever gap is most unclear.

**Actor discovery:** As the conversation reveals people or systems, add them to the Actors table with Type (`person`/`system`) and Role (derived from their actions across UCs — e.g., admin, editor, viewer; system actors use `—`). Confirm each new actor with the user.

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
1. **Track via task** — create a task for the confirmed use case (e.g., `UC-1: <title>`) and mark it as completed. This gives the user a running overview via TaskList.
2. **Check for checkpoint** — if this confirmation triggers a checkpoint (every 3 UCs, interview stage transition, or before review), batch-write all unwritten confirmed UCs to the working file, update Actors table, Use Case Diagram, and Context.

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

## Wrapping Up

The interview ends only when the user says so. Never conclude on your own — even if all gaps seem covered, the user may want to go deeper or add more use cases. Keep asking until the user explicitly ends the session.

When the user indicates they're done, ask whether they want to:
- **End this iteration** (come back later to refine further)
- **Finalize** (mark as complete, create issues)

### Agent Usage

Reviews and explorations are handled by launching fresh subagents. Always spawn a fresh agent — context is passed via file paths, not agent memory.

- **Reviewer:** Launch via `Agent(subagent_type: "usecase-reviewer")`. Pass the working file path and report output path. If a previous review report exists, include its path so the reviewer can check whether prior findings have been addressed.
- **Explorer:** Launch via `Agent(subagent_type: "usecase-explorer")`. Pass the working file path and report output path.

**Execution order:** Always run the reviewer first. After the review cycle completes (user walks through findings, working file is updated), the user decides the next step: run exploration, re-review the updated file, or skip exploration. The explorer only runs when the user explicitly chooses it.

### End Iteration (not finalizing)

Launch a `usecase-reviewer` subagent. Walk through flagged issues with the user and update the working file. Then, if the user chooses, launch a `usecase-explorer` subagent against the updated file. Scan for open items, append Session Close entry to the history file, update Open Items + Next Steps in the working file, increment revision, and report.

For the full step-by-step checklist, read **`${CLAUDE_SKILL_DIR}/references/session-closing.md`** → "End Iteration" section.

### Finalize

Launch a `usecase-reviewer` subagent. All issues must be resolved. Finalize the use case diagram, create GitHub Issues for each use case, write the final file with `status: final`, and report.

For the full step-by-step checklist, read **`${CLAUDE_SKILL_DIR}/references/session-closing.md`** → "Finalize" section.

After finalizing, suggest the next step: "To turn these use cases into a specification, run `/think:think-spec <file_path>`."

### Output Format

Follow the Use Case template in `${CLAUDE_SKILL_DIR}/references/output-template.md` for the final file structure and required sections.
