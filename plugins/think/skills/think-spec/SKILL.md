---
name: think-spec
description: "This skill should be used when the user needs to create or iterate on a software specification — combining domain modeling, functional requirements, and architecture in one session. Common triggers include: 'spec', 'specification', 'design the system', 'define requirements', 'domain model', 'architecture', 'what should we build', 'system design', 'component design', 'let's spec this out', 'define the system'. Also applicable when use cases from think-usecase need to be turned into a buildable specification."
argument-hint: <path to use case file(s), or existing .spec.md file for iteration>
allowed-tools: Read, Write, Agent, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Specification Builder

Takes use cases (from think-usecase) and builds a unified specification — domain model, functional requirements, and system architecture — through collaborative dialogue in a single session. Phases interleave naturally; no forced boundaries.

## Modes

This skill operates in two modes, determined by the input:

### First Design

Input is a use case file (no existing `.spec.md`). Follows a guided sequence:

1. **Functional Requirements** — turn use cases into concrete behavior specs
2. **Domain / Concept Extraction** — extract domain concepts, relationships, and state transitions from the requirements
3. **Architecture** — identify components, information flows, and DB schemas

The sequence helps bootstrap shared language from requirements before structuring components. The user can still jump between phases freely.

### Iteration

Input is an existing `.spec.md` file. No fixed order — enter from wherever the change is needed.

**Impact propagation rule:** when something changes in one phase, check whether it affects the other phases:
- Requirement change → does the domain model need updating? Do sequence diagrams still hold?
- Domain change → do requirements reference outdated concepts? Do components need restructuring?
- Architecture change → does this imply new requirements? Does the domain model need new concepts?

Always surface these cross-phase impacts to the user rather than silently assuming they're fine.

## Input

Resolve the input from **$ARGUMENTS** using the file resolution rules below, then read the file(s).

If no argument is provided, ask the user for a slug, filename, or path.

### File Resolution

Arguments can be full paths, partial filenames, or slugs. Resolve them by searching `A4/`:

1. **Full path** — use directly
2. **Partial match** — glob for `A4/*<argument>*.usecase.md` and `A4/*<argument>*.spec.md`
3. **Multiple matches per type** — present the candidates and ask the user to pick
4. **No match** — inform the user and ask for a different term

After resolution, present the resolved file(s) and ask the user to confirm before reading:

> **Resolved input files:**
> - `A4/agent-orchestrator.usecase.md`
>
> Proceed with these files?

**Mode detection:**
- If the target `.spec.md` file already exists → **Iteration** mode. Read the spec file and its source references.
- If only use case files are found (no existing spec) → **First Design** mode.

The source reference in the output file should be placed as a blockquote under the title heading, linking to all input files (see output template for format).

**Iteration Mode entry:** When entering Iteration mode, check two things:

1. **Source usecase changes** — compare the stored `sha` in spec frontmatter against the current file:
   - Run `git hash-object <usecase-file-path>` to get the current SHA.
   - If SHA matches → no changes, skip.
   - If SHA differs → run `git diff <stored-sha> <current-sha>` to see exactly what changed. Also read the usecase's history file (`<topic-slug>.usecase.history.md`) for context on why changes were made.
   - Present the changes to the user: "The source usecase has been updated. Changes: [list]. Review these changes before continuing?"
   - Walk through each change with the user to determine spec impact (new FRs needed, existing FRs to update, domain/architecture implications).
   - After reflecting, update `sources` in spec frontmatter (both `revision` and `sha`). If the working file content changed, **increment `revision`** and update `revised` timestamp.

2. **Unreflected review reports** — check for `A4/<topic-slug>.spec.review-*.md` files against `reflected_files` in frontmatter:
   - Read each unreflected review report and extract issues that were not yet addressed.
   - Present unreflected findings to the user alongside the Open Items from the last revision.
   - After reflecting, add the review report filenames to `reflected_files`. If the working file content changed, **increment `revision`** and update `revised` timestamp.

3. **Integration report feedback** — check for `A4/<topic-slug>.integration-report.md`:
   - If it exists and its filename is not in `reflected_files`, read it.
   - Extract issues where `Stage` is **spec** (missing FRs, ambiguous behavior, platform capability gaps).
   - Present these as high-priority upstream feedback:

     > **Integration verification found spec-level issues:**
     >
     > | # | Issue | Recommended Fix |
     > |---|-------|----------------|
     > | 1 | No FR for conversation input UI — 8 FRs blocked | Add platform FR for message input + display |
     >
     > These should be addressed before other work. Review?

   - After reflecting, add the integration report filename to `reflected_files`. If the working file content changed, **increment `revision`** and update `revised` timestamp.

After reading, list all use cases and any existing spec content found, then confirm with the user before proceeding.

## Step 0: Explore the Codebase

Before starting, explore the current codebase to understand:

- **Project structure** — directories, key files, tech stack
- **Existing features** — what's already built, patterns in use
- **Domain terms already in use** — naming conventions, existing entities, vocabulary
- **Existing architecture** — current components, services, communication patterns
- **Database** — existing schemas, migrations, ORM usage
- **Constraints** — frameworks, conventions, dependencies that the spec should respect

This grounds the specification in reality. Reference what you find during the interview — e.g., "I see the project already uses the term 'Workspace' for grouping items. Should we align with that?"

If the codebase already exists, record the detected technology stack (language, frameworks, key libraries) in the Technology Stack section of the output file. Present it to the user for confirmation: "I detected the project uses TypeScript with Next.js and Prisma. Should I record this as the technology stack?"

## Navigation

The spec covers three phases. In **First Design** mode, start with Requirements and follow the guided sequence. In **Iteration** mode, start wherever the user wants.

The user controls all transitions — revisiting and interleaving are always welcome. Do NOT auto-advance to the next phase. After completing work on any topic (or when the conversation reaches a natural pause), present the current status:

> Here's where we are:
>
> | Phase | Status | Review |
> |-------|--------|--------|
> | Requirements | 5 FRs defined (3 UI, 2 Non-UI) | Ready for review |
> | Domain Model | 3 concepts, 2 relationships | Not reviewed |
> | Architecture | Not started | — |
>
> What would you like to work on next? We can continue here, move to another phase, request a phase review, or wrap up.

The **Review** column tracks per-phase review state: `—` (not enough content), `Ready for review`, `Reviewed (rev N)`, or `Changes since last review`. When a phase has meaningful content and hasn't been reviewed yet (or has changed since the last review), suggest a phase review — but always let the user decide.

## Phase 1: Functional Requirements

### Step 1.0: Scan Excluded Ideas from Source Usecase

Before deriving FRs, read the source usecase's **Excluded Ideas** table (if present). Items excluded with reason containing "basic behavior", "basic UI behavior", "basic app behavior", or "not a user-level use case" are **platform capability candidates** — behaviors that aren't use cases but are prerequisites for use cases to function.

For each such item:
1. Check whether the capability is assumed by 2+ UCs in the document (e.g., "main session create/close" is assumed by every UC that involves conversation).
2. If yes → this is a platform FR candidate. Present to the user:

   > The usecase document excluded these as "basic behavior," but they appear to be prerequisites for multiple UCs:
   >
   > | Excluded Item | Assumed By | Suggested FR |
   > |--------------|------------|-------------|
   > | Main session create/close | UC-1 through UC-9 | Conversation UI — message input, display, and response streaming |
   >
   > Should I create FRs for these?

3. If the user confirms, create FRs for each platform capability. These FRs reference the Overview rather than a specific UC:

   ```
   > Use Case: (platform capability — implicit across all conversation UCs)
   ```

4. If no Excluded Ideas table exists, or no items match the criteria, skip this step silently.

### Step 1.1: Use-Case-by-Use-Case Specification

Work through use cases one at a time. For each use case:

1. **Present the use case** and confirm it's still relevant.
2. **Check use case size** — if the use case is too big (3+ independent behaviors), decompose it first.
3. **Tag as UI or Non-UI** — determine whether this use case involves a user interface. A single use case file may contain both UI and Non-UI use cases.
4. **Ask clarifying questions** — one at a time — to fill in the gaps.
5. **Draft the FR** and present it for confirmation.
6. **Stay until concrete** — do not move to the next use case until the current FR is detailed enough for AI to develop.
7. Move to the next use case only when the user confirms.

#### Use Case Decomposition

When a use case is too big:
1. Tell the user: "This use case seems to cover multiple distinct behaviors. I'd like to break it down."
2. Propose sub-use-cases.
3. Once confirmed, proceed to specify each sub-use-case individually.

For detailed clarification checklists (UI vs Non-UI) and question techniques, read **`${CLAUDE_SKILL_DIR}/references/requirements-guide.md`** → "Question Techniques" section.

After each FR is confirmed, track it via a task (e.g., `FR-1: <title>`, marked completed). The file is written at checkpoints — not after every FR (see Progressive File Writing).

### Step 1.2: UI Screen Grouping

Group UI FRs by screen/view, confirm with the user, then define screen navigation as a PlantUML activity diagram. For the full procedure, read **`${CLAUDE_SKILL_DIR}/references/requirements-guide.md`** → "UI Screen Grouping" section.

### Step 1.3: Mock Generation

For each confirmed screen group, invoke the `mock-html-generator` agent to create an HTML mock in `A4/mock/<topic-slug>/`. Present, iterate, refine FRs from feedback, and record mock paths. For the full procedure, read **`${CLAUDE_SKILL_DIR}/references/requirements-guide.md`** → "Mock Generation" section.

### Step 1.4: Authorization Rules

Analyze the Actors table for role differentiation. If roles differ, build an authorization matrix (actor × FR → access level). Skip if no differentiation. For the full procedure, read **`${CLAUDE_SKILL_DIR}/references/requirements-guide.md`** → "Authorization Rules" section.

### Step 1.5: Non-Functional Requirements Nudge

Ask the user once whether NFRs should constrain implementation (performance, security, scalability, accessibility, compliance). If yes, capture each with description, affected FRs, and measurable criteria. If no, skip. For details, read **`${CLAUDE_SKILL_DIR}/references/requirements-guide.md`** → "Non-Functional Requirements Nudge" section.

## Phase 2: Domain Model

Extract domain concepts through cross-cutting analysis of the functional requirements. Three topics: Concept Extraction, Relationship Mapping, and State Transition Analysis — each through interview with PlantUML diagrams.

For the detailed procedure per topic, read **`${CLAUDE_SKILL_DIR}/references/domain-model-guide.md`**.

## Phase 3: Architecture

Design system architecture using the requirements and domain model. Topics: External Dependencies, Component Identification, Per-Component Deep Dive (DB schema, information flow, interface contracts), Technology Choices, and Technical Claim Verification.

For the detailed procedure per topic, read **`${CLAUDE_SKILL_DIR}/references/architecture-guide.md`**.

## Abstraction Level Guards

Each phase has boundaries on what level of detail is appropriate — requirements capture *what*, domain models describe *what exists*, architecture defines *component interfaces*. None should include internal implementation details.

For the full per-phase rules, read **`${CLAUDE_SKILL_DIR}/references/abstraction-guards.md`**.

When the user drifts into component internals, redirect gently: "That's an internal implementation detail. Here, let's focus on the interface between components."

## Progressive File Writing

### Working File Path

At the start of the session, determine the file path:
- Default: `A4/<topic-slug>.spec.md`
- If the file already exists, this is **Iteration** mode — read the existing file and continue from where it left off
- Ask the user only if they want a different location

Tell the user the file path so they can follow along: "I've started a working file at `<path>`. It will update as we go."

### Source Revision Tracking

On **First Design**, record each source usecase file's current revision in the spec frontmatter:

```yaml
sources:
  - file: <topic-slug>.usecase.md
    revision: <current revision number>
    sha: <git hash-object output>
```

On **Iteration Mode entry**, compare and update as described in the Iteration Mode entry procedure above.

### How to Update

- **Track confirmed items via tasks** — after each FR, concept, or component is confirmed, create a task (e.g., `FR-1: <title>`) and mark it completed. This gives the user a running overview via TaskList without writing the file.
- **Write at checkpoints only** — when a checkpoint trigger fires (see below), use the Write tool to rewrite the entire file with all pending confirmed content. This keeps the file consistent and avoids partial edit issues.
- **Preserve all previously confirmed content** — never remove or reorder confirmed items.
- Show progress: "That's 5 FRs defined, 3 concepts extracted. Let's continue."

### Checkpoint Triggers

| Trigger | When |
|---------|------|
| Item count | Every 3 confirmed items within a phase (3 FRs, 3 concepts, etc.) |
| Phase transition | Moving between Requirements → Domain Model → Architecture. **Increment `revision`** if content changed during the phase. |
| Before review | Before launching a `spec-reviewer` subagent |
| Navigation status | When presenting the phase status table to the user |
| Session end | End iteration or finalize |

## Revision and Session History

Increment `revision` in frontmatter and update `revised` timestamp when: before launching a reviewer subagent (stamps the reviewed snapshot), reflecting source usecase changes, reflecting review findings, phase transition with content changes, or closing the session. Routine updates during the interview (FR confirmation, concept extraction) do not increment revision.

Session history is stored in a separate file (`<topic-slug>.spec.history.md`). See `${CLAUDE_SKILL_DIR}/references/session-history.md` for the full format.

At the end of each session (whether wrapping up or pausing):

1. **Scan for incomplete items** — walk through each phase and identify what's missing or underspecified:
   - Requirements: FRs without error handling, vague input/output, missing validation
   - Domain Model: concepts referenced in FRs but not in glossary, missing state transitions
   - Architecture: components without interface contracts, information flows at abstract level, missing DB schemas
2. **Append a Session Close entry** to the history file per `${CLAUDE_SKILL_DIR}/references/session-history.md`.
3. **Update the working file** — update the Open Items and Next Steps sections with the current state. **Increment `revision`** and update `revised` timestamp.

### Iteration Mode Entry

When entering **Iteration** mode:
1. Read the working file — Open Items and Next Steps show the current backlog.
2. Present the Open Items table as a **work backlog**:

   > Here are the open items from the last session:
   >
   > | # | Section | Item | What's Missing |
   > |---|---------|------|---------------|
   > | 1 | Architecture | AuthService ↔ SessionManager | Interface contract not defined |
   > | 2 | FR-3 | Input | Batch size limit undecided |
   > | ...
   >
   > Which item would you like to work on first? Or would you like to focus on something else?

3. Let the user choose — they may pick from the backlog or bring new topics.

## Upstream Feedback Issues

During the specification process, problems in upstream artifacts (use cases) may surface. Note the problem, ask the user before creating a GitHub Issue (labels: `usecase` + `feedback`), and continue working without blocking. Do NOT create issues proactively.

For the full procedure, read **`${CLAUDE_SKILL_DIR}/references/session-procedures.md`** → "Upstream Feedback Issues" section.

## Facilitation Guidelines

- **One question at a time.** Show the next question, but give space for the previous one.
- **Stay concrete.** Anchor to specific use cases and FRs, not abstract theory.
- **Use the user's language.** Don't introduce jargon unless the user does.
- **Don't design the solution.** Capture what the system needs, not how to implement it.
- **Flag cross-phase dependencies.** If a requirement change implies a domain or architecture change, say so.
- **Every 3-4 items:** Brief progress snapshot.

## Phase Review

Reviews are handled by launching a `spec-reviewer` subagent. Each invocation is independent — context is passed via file paths. Four scopes: Requirements, Domain Model, Architecture, and Full.

For review scopes, trigger conditions, prompt formats, and post-review steps, read **`${CLAUDE_SKILL_DIR}/references/phase-review-guide.md`**.

## Agent Usage

Always spawn fresh subagents — context is passed via file paths, not agent memory.

- **`spec-reviewer`** — launch via `Agent(subagent_type: "spec-reviewer")`. Context passed via file paths. See **`${CLAUDE_SKILL_DIR}/references/phase-review-guide.md`** for invocation details.
- **`mock-html-generator`** — launch via `Agent(subagent_type: "mock-html-generator")`. Each invocation provides FRs, layout requirements, and output path in the prompt.

## Wrapping Up

The specification ends only when the user says so. Never conclude on your own — even if all phases seem complete, the user may want to revisit or go deeper.

When the user indicates they're done, ask whether they want to:
- **End this iteration** (come back later to refine further)
- **Finalize** (mark as complete for coding agent)

### End Iteration (not finalizing)

Launch a **Full** scope `spec-reviewer` subagent. Walk through flagged issues with the user, scan for open items, increment revision, write the session checkpoint and change log, append the interview transcript, and report.

For the full step-by-step checklist, read **`${CLAUDE_SKILL_DIR}/references/session-procedures.md`** → "End Iteration" section.

### Finalize

Verify technology stack is filled, launch a **Full** scope `spec-reviewer` subagent. All issues must be resolved. Write the final session checkpoint, set `status: final`, show spec feedback issues, and report.

For the full step-by-step checklist, read **`${CLAUDE_SKILL_DIR}/references/session-procedures.md`** → "Finalize" section.

After finalizing, suggest the next step: "To create an implementation plan from this spec, run `/think:think-plan <file_path>`."

### Output Format

Follow the Specification template in `${CLAUDE_SKILL_DIR}/references/output-template.md` for the final file structure, field rules, and required sections.
