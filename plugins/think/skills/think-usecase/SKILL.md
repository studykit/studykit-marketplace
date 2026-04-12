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

### Session Task List

Use the task list as a live workflow map. The user should be able to check the task list at any point and understand exactly where they are and what remains.

**Naming convention:** Phase-level tasks use the phase name. Sub-tasks use `<phase prefix>: <detail>` format. Sub-tasks are created **dynamically** when entering a phase — not all upfront.

**Task lifecycle:**
- Mark phase-level task `in_progress` when entering the phase.
- Create sub-tasks as work items are identified within the phase.
- Mark sub-tasks `completed` as each is confirmed.
- Mark phase-level task `completed` when all sub-tasks are done.
- If the user navigates back to a completed phase, set it back to `in_progress`.

**New Session** — create phase-level tasks at session start:
- `"Step 1: Receive idea and create file"` → `in_progress`
- `"Discovery: Use cases"` → `pending`
- `"Platform capabilities audit"` → `pending`
- `"Domain model: Concept extraction"` → `pending`
- `"Domain model: Relationship mapping"` → `pending`
- `"Domain model: State transitions"` → `pending`
- `"Wrap Up: Explorer review"` → `pending`
- `"Wrap Up: Reviewer validation"` → `pending`
- `"Wrap Up: Record open items"` → `pending`

**Iteration** — adjust based on the work backlog:
- `"Review open items and backlog"` → `in_progress`
- One task per selected item (e.g., `"Revise UC-3: Update error handling"`)
- `"Wrap Up: Explorer review"` → `pending`
- `"Wrap Up: Reviewer validation"` → `pending`
- `"Wrap Up: Record open items"` → `pending`

**Conditional tasks** — add when they become relevant:
- `"Discovery: Relationship analysis"` — when 5+ UCs are confirmed
- `"UI screen grouping"` — when UI use cases are confirmed
- `"Mock generation"` — when the user agrees to create mocks
- `"Non-functional requirements"` — when the user has NFRs to capture

**Dynamic sub-task examples:**

Discovery — per confirmed UC:
- `"Discovery: UC-1 Share meeting summary"`
- `"Discovery: UC-2 Search history"`
- `"Discovery: UC-3 Export transcript"`

Platform capabilities audit — per identified gap:
- `"Platform audit: Message input and sending"`
- `"Platform audit: Conversation display with streaming"`

Domain model — per confirmed concept or relationship:
- `"Domain model: Concept — Session"`
- `"Domain model: Concept — Message"`
- `"Domain model: Relationship — Session contains Messages"`

### 1. Receive the Idea

Take the user's input — it may be a raw idea, a brainstorming output, or a vague description. Restate the idea back in one sentence to confirm understanding.

**Then immediately create the working file** as described in Progressive File Writing above. Mark "Step 1: Receive idea and create file" as `completed`. Mark "Discovery: Use cases" as `in_progress`.

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

After the user confirms the core UC, **immediately drill into precision**:

- **Validation:** "Are there input constraints? Limits? Required formats?" — capture as business rules the user can see (e.g., "empty messages cannot be sent", "maximum 100KB diagram source")
- **Error handling:** "What does the user see when this fails?" — capture user-visible failure states (e.g., "rendering failed indicator with raw source access", "error message with retry option")
- **Boundary conditions:** "What happens at the edges?" — empty input, maximum items, concurrent access, timeouts

Record confirmed validation/error handling in the UC's **Validation** and **Error handling** fields. These fields are optional — skip if the UC has no meaningful constraints or failure modes. Keep all descriptions at user-visible level (what the user sees), not system-internal level (how the system handles it).

After precision is confirmed:
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

### 8. Platform Capabilities Audit

Mark "Discovery: Use cases" as `completed`. Mark "Platform capabilities audit" as `in_progress`.

After all UC-derived use cases are confirmed, perform a final audit for implicit platform capabilities — shared behaviors that multiple UCs assume but no UC defines.

1. **Scan all UC flows** — identify user actions or system behaviors that appear across 3+ UCs but aren't themselves covered by any UC.

   Common patterns to check:
   - **Input mechanisms** — message input, form submission, command entry, search box
   - **Display mechanisms** — conversation display, list views, real-time response streaming, status indicators
   - **Navigation infrastructure** — view routing, tab management, sidebar, breadcrumbs
   - **State lifecycle** — session restore on launch, data persistence across restarts, undo/redo

2. **Present findings** to the user:

   > These capabilities are assumed by multiple UCs but not yet defined:
   >
   > | Assumed Capability | Referenced By | Example UC Text |
   > |-------------------|---------------|-----------------|
   > | Message input and sending | UC-1, UC-7, UC-8, UC-15 | "user types a question" |
   > | Conversation display with streaming | UC-1, UC-2, UC-3 | "response displays inline" |
   >
   > Should I create UCs for these?

3. **Create UCs** for confirmed gaps. These UCs reference the Overview rather than a specific source:
   - **Actor:** (platform capability — implicit across [list dependent UCs])

4. Skip silently if no gaps are found.

### 9. UI Screen Grouping (if UI use cases exist)

After all UCs (including platform capabilities) are confirmed, group UI-related UCs by screen or view:

1. **Propose screen groups** — analyze UCs and group them by the screen/view where the interaction occurs.
2. **Confirm with the user** — they may merge, split, or rename groups.
3. **Define screen navigation** — map how users move between screens. Present as a PlantUML activity diagram.
4. **Record** in the output file's UI Screen Groups section.

### 10. Mock Generation (optional, per screen group)

For each confirmed screen group, optionally create an HTML mock:

1. Invoke the `mock-html-generator` agent to create an HTML mock in `A4/mock/<topic-slug>/`.
2. Present the mock and gather feedback.
3. Refine UCs from mock feedback — fill gaps, clarify interactions.
4. Record mock file paths in the output file.

Move to the next screen group only when the user confirms. Mock generation is suggested but not required — the user can skip it.

### 11. Non-Functional Requirements (optional)

Ask the user once whether NFRs should constrain implementation:

> "Are there non-functional requirements? For example: performance targets, security requirements, scalability needs, accessibility standards, compliance rules. If not, we can skip this."

- If yes → capture each NFR with: description, affected UCs, measurable criteria
- If no → skip, no section created

### 12. Domain Model Extraction

Mark "Platform capabilities audit" as `completed` (if it was the previous phase). Mark "Domain model: Concept extraction" as `in_progress`.

After UCs are substantially complete (including platform capabilities and precision), extract domain concepts through cross-cutting analysis. This produces the shared vocabulary that architecture and implementation will use.

For the detailed procedure (concept extraction, relationship mapping, state transition analysis), read **`${CLAUDE_SKILL_DIR}/references/domain-model-guide.md`**.

The Domain Model has three topics:
1. **Concept Extraction** — identify entities that appear across multiple UCs, confirm name/definition/key attributes
2. **Relationship Mapping** — identify relationships between concepts, present as PlantUML class diagram
3. **State Transition Analysis** — identify stateful concepts, map states/transitions/conditions as PlantUML state diagram

Domain Model uses the same interview style — present findings, confirm with the user, iterate. Track confirmed concepts via tasks.

**Abstraction rule for Domain Model:**
- "What exists and how it connects" = confirmed
- "How to build it" = not decided
- No implementation types (VARCHAR, INT) in diagrams
- No API endpoints or serialization formats

## Wrapping Up

The interview ends only when the user says so. Never conclude on your own — even if all gaps seem covered, the user may want to go deeper or add more use cases. Keep asking until the user explicitly ends the session.

When the user indicates they're done, mark the current phase task as `completed` and proceed to **End Iteration**.

### Agent Usage

Reviews, explorations, and mock generation are handled by launching fresh subagents. Always spawn a fresh agent — context is passed via file paths, not agent memory.

- **Reviewer:** Launch via `Agent(subagent_type: "usecase-reviewer")`. Pass the working file path and report output path. If a previous review report exists, include its path so the reviewer can check whether prior findings have been addressed.
- **Explorer:** Launch via `Agent(subagent_type: "usecase-explorer")`. Pass the working file path and report output path.
- **Mock generator:** Launch via `Agent(subagent_type: "mock-html-generator")`. Each invocation provides UCs, layout requirements, and output path in the prompt.

**Execution order:** Explorer runs first (find gaps and new UC candidates), then Reviewer validates all UCs (existing + newly added) in one pass. Both are required steps, not optional.

### End Iteration

Launch `usecase-explorer` → reflect accepted candidates → launch `usecase-reviewer` → walk through findings → update working file. If significant changes were made during review, optionally re-run the reviewer. Scan for open items, optionally create GitHub Issues, append Session Close entry to the history file, update Open Items + Next Steps, increment revision, and report.

For the full step-by-step checklist, read **`${CLAUDE_SKILL_DIR}/references/session-closing.md`** → "End Iteration" section.

### Output Format

Follow the Use Case template in `${CLAUDE_SKILL_DIR}/references/output-template.md` for the final file structure and required sections.
