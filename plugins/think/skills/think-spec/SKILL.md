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

After resolution, present the resolved file(s) and ask the user to confirm before reading.

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

3. **Integration report feedback** — check for `A4/<topic-slug>.integration-report.r*.md` not in `reflected_files`. Extract issues where `Stage` is **spec** and present as high-priority upstream feedback. After reflecting, add handled report filenames to `reflected_files`. If content changed, **increment `revision`** and update `revised` timestamp.

After reading, list all use cases and any existing spec content found, then confirm with the user before proceeding.

## Step 0: Explore the Codebase

Explore the codebase to ground the spec in reality — existing domain terms, architecture, conventions, and constraints. Reference what you find during the interview.

If a codebase already exists, record the detected technology stack in the Technology Stack section and confirm with the user.

## Navigation

The spec covers three phases. In **First Design** mode, start with Requirements and follow the guided sequence. In **Iteration** mode, start wherever the user wants.

The user controls all transitions — revisiting and interleaving are always welcome. Do NOT auto-advance to the next phase. After completing work on any topic, present a status table showing each phase's progress and review state (`—`, `Ready for review`, `Reviewed (rev N)`, `Changes since last review`). When a phase has unreviewed content, suggest a review — but let the user decide.

## Phase 1: Functional Requirements

### Step 1.0: Scan Excluded Ideas from Source Usecase

Before deriving FRs, read the source usecase's **Excluded Ideas** table (if present). Items excluded as "basic behavior" or "not a user-level use case" are **platform capability candidates** — prerequisites assumed by multiple UCs.

For items assumed by 2+ UCs, present them as platform FR candidates and ask the user to confirm. Confirmed platform FRs reference the Overview rather than a specific UC. Skip silently if no Excluded Ideas table exists or no items match.

### Step 1.1: Use-Case-by-Use-Case Specification

Work through use cases one at a time. For each: present the UC, check size (decompose if 3+ independent behaviors), tag as UI or Non-UI, clarify gaps, draft the FR, and stay until concrete enough for AI to develop. Move to the next only when confirmed.

For clarification checklists (UI vs Non-UI) and question techniques, read **`${CLAUDE_SKILL_DIR}/references/requirements-guide.md`** → "Question Techniques" section.

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

On **First Design**, record each source usecase file's current revision and SHA (`git hash-object`) in spec frontmatter `sources`. On **Iteration Mode entry**, compare and update as described above.

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

When entering **Iteration** mode, read the working file's Open Items and Next Steps, present them as a work backlog, and let the user choose what to work on.

## Upstream Feedback Issues

During the specification process, problems in upstream artifacts (use cases) may surface. Note the problem, ask the user before creating a GitHub Issue (labels: `usecase` + `feedback`), and continue working without blocking. Do NOT create issues proactively.

For the full procedure, read **`${CLAUDE_SKILL_DIR}/references/session-procedures.md`** → "Upstream Feedback Issues" section.

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
