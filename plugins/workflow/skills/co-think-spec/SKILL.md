---
name: co-think-spec
description: "This skill should be used when the user needs to create or iterate on a software specification — combining domain modeling, functional requirements, and architecture in one session. Common triggers include: 'spec', 'specification', 'design the system', 'define requirements', 'domain model', 'architecture', 'what should we build', 'system design', 'component design', 'let's spec this out', 'define the system'. Also applicable when use cases from co-think-usecase need to be turned into a buildable specification."
argument-hint: <path to use case file(s), or existing .spec.md file for iteration>
allowed-tools: Read, Write, Agent, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Specification Builder

Takes use cases (from co-think-usecase) and builds a unified specification — domain model, functional requirements, and system architecture — through collaborative dialogue in a single session. Phases interleave naturally; no forced boundaries.

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

Arguments can be full paths, partial filenames, or slugs. Resolve them by searching `A4/co-think/`:

1. **Full path** — use directly
2. **Partial match** — glob for `A4/co-think/*<argument>*.usecase.md` and `A4/co-think/*<argument>*.spec.md`
3. **Multiple matches per type** — present the candidates and ask the user to pick
4. **No match** — inform the user and ask for a different term

After resolution, present the resolved file(s) and ask the user to confirm before reading:

> **Resolved input files:**
> - `A4/co-think/agent-orchestrator.usecase.md`
>
> Proceed with these files?

**Mode detection:**
- If the target `.spec.md` file already exists → **Iteration** mode. Read the spec file and its source references.
- If only use case files are found (no existing spec) → **First Design** mode.

The source reference in the output file should be placed as a blockquote under the title heading, linking to all input files (see output template for format).

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
> | Phase | Status |
> |-------|--------|
> | Requirements | 5 FRs defined (3 UI, 2 Non-UI) |
> | Domain Model | 3 concepts, 2 relationships |
> | Architecture | Not started |
>
> What would you like to work on next? We can continue here, move to another phase, or wrap up.

## Phase 1: Functional Requirements

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

For detailed clarification checklists (UI vs Non-UI) and question techniques, read **`references/requirements-guide.md`** → "Question Techniques" section.

After each FR is confirmed, write it to the output file immediately and update the task.

### Step 1.2: UI Screen Grouping

Group UI FRs by screen/view, confirm with the user, then define screen navigation as a PlantUML activity diagram. For the full procedure, read **`references/requirements-guide.md`** → "UI Screen Grouping" section.

### Step 1.3: Mock Generation

For each confirmed screen group, invoke the `mock-html-generator` agent to create an HTML mock in `A4/co-think/mock/<topic-slug>/`. Present, iterate, refine FRs from feedback, and record mock paths. For the full procedure, read **`references/requirements-guide.md`** → "Mock Generation" section.

### Step 1.4: Authorization Rules

Analyze the Actors table for role differentiation. If roles differ, build an authorization matrix (actor × FR → access level). Skip if no differentiation. For the full procedure, read **`references/requirements-guide.md`** → "Authorization Rules" section.

### Step 1.5: Non-Functional Requirements Nudge

Ask the user once whether NFRs should constrain implementation (performance, security, scalability, accessibility, compliance). If yes, capture each with description, affected FRs, and measurable criteria. If no, skip. For details, read **`references/requirements-guide.md`** → "Non-Functional Requirements Nudge" section.

## Phase 2: Domain Model

Extract domain concepts through cross-cutting analysis of the functional requirements.

### Topic 2.1: Concept Extraction

- Read all FRs horizontally — identify concepts (entities) that appear across multiple FRs
- Present the initial concept list to the user
- For each concept, through interview confirm: name, definition, 1-2 key attributes
- Track which FRs reference each concept

### Topic 2.2: Relationship Mapping

- Identify relationships between concepts
- Present as PlantUML class diagram (concept name + key attributes only, NO implementation types)
- Accompanied by text explanation of each relationship
- Show multiplicity (1..*, 0..1, etc.) where relevant

### Topic 2.3: State Transition Analysis

- Identify which concepts have state changes across FRs
- For each stateful concept, map states, transitions, conditions, triggers
- Present as PlantUML state diagram
- Accompanied by text explanation

## Phase 3: Architecture

Design system architecture using the requirements and domain model.

### Topic 3.0: External Dependencies

Before designing internal components, identify external systems the software depends on:

1. **Scan FRs for external interactions** — any FR that references sending email, payment, authentication via third-party, file storage, external data sources, etc.
2. **Present the list** to the user:

   > I've identified these external dependencies from the FRs:
   >
   > | External System | Used By | Purpose |
   > |----------------|---------|---------|
   > | OAuth Provider | FR-1, FR-2 | User authentication |
   > | Email Service | FR-5 | Notification delivery |
   >
   > Are there other external services this system will use?

3. **For each confirmed dependency**, clarify:
   - What does the system send/receive?
   - Are there constraints? (rate limits, pricing tiers, specific provider chosen or open)
   - What happens if the external system is unavailable? (fallback behavior)
4. **Record in the output file** — External Dependencies section under Architecture.

### Topic 3.1: Component Identification

- Propose an initial set of components from the input materials
- Present the component list with responsibility descriptions
- Through interview, confirm: component name, responsibility, whether it has its own data store
- Present as PlantUML component diagram

### Topic 3.2: Per-Component Deep Dive

For each confirmed component:

- **DB schema** (if the component has its own data store):
  - Identify entities, attributes, and relationships
  - Present as PlantUML IE diagram
  - Not all components need a DB schema — ask before diving in

- **Information flow** (per use case):
  - For each use case involving this component, map the information flow between components
  - Present as PlantUML sequence diagram — one per use case
  - First iteration: "A sends user information to B" level is fine
  - Subsequent iterations: progressively refine to **interface contract** level — communication method (REST, event, function call), operation name, request/response schema
  - The goal by finalization: a coding agent can implement the interface without guessing

- **Interface contracts** (per component boundary):
  - Define how components communicate: API style, operations, request/response schemas
  - This is not required in the first iteration — it emerges as the spec matures
  - Present as a contract table per component pair:

    > | Operation | Direction | Request | Response | Notes |
    > |-----------|-----------|---------|----------|-------|
    > | createSession | Client → SessionService | { userId, title } | { sessionId, status } | |
    > | onSessionExpired | SessionService → NotificationService | { sessionId, reason } | — | event |

### Topic 3.3: Consistency Check

Verify the architecture against all inputs and across diagrams:

- **Cross-diagram consistency**: component diagram, sequence diagrams, and ERDs reference the same components and data
- **Domain model coverage**:
  - Core concepts housed in at least one component
  - Cross-boundary relationships reflected in information flows
  - State transition responsibilities assigned to components
- **Use case coverage**: every use case has at least one sequence diagram

Present any gaps found and discuss with the user.

### Technology Choices

When a technology choice arises:
- **Lightweight decisions** — discuss inline and record with brief rationale.
- **Heavy decisions** — ask the user: "This seems like a decision worth investigating more deeply. Would you like to use `/workflow:spark-decide` to evaluate options?"

## Abstraction Level Guards

**Applied per phase:**

### Requirements
- Capture **what the software should do**, not how to implement it
- No technology choices, no data schemas, no API endpoint designs

### Domain Model
- "What exists and how it connects" = confirmed, "how to build it" = not decided
- No implementation types (VARCHAR, INT) in class diagrams
- No API endpoints or serialization formats

### Architecture
- **First iteration**: "What components exist and what information they exchange" — sequence diagrams at information level, no interface contracts yet
- **Subsequent iterations**: progressively add interface contracts — communication method, operations, request/response schemas. This is expected and necessary for coding agents.
- DB schemas define entities and relationships, not implementation details (no index strategies)
- **Always off-limits**: internal implementation of each component (algorithms, library choices within a component, internal data structures)

When the user drifts into component internals, redirect gently: "That's an internal implementation detail. Here, let's focus on the interface between components."

## Progressive File Writing

### Working File Path

At the start of the session, determine the file path:
- Default: `A4/co-think/<topic-slug>.spec.md`
- If the file already exists, this is **Iteration** mode — read the existing file and continue from where it left off
- Ask the user only if they want a different location

Tell the user the file path so they can follow along: "I've started a working file at `<path>`. It will update as we go."

### How to Update

- **Use the Write tool** to rewrite the entire file each time. This keeps the file consistent and avoids partial edit issues.
- **Preserve all previously confirmed content** — never remove or reorder confirmed items.
- After each FR is confirmed, update the Requirements section.
- After each concept is confirmed, update the Domain Model section.
- After each component is confirmed, update the Architecture section.
- Show progress: "That's 5 FRs defined, 3 concepts extracted. Let's continue."

## Session Checkpoint

At the end of each session (whether wrapping up or pausing):

1. **Scan for incomplete items** — walk through each phase and identify what's missing or underspecified:
   - Requirements: FRs without error handling, vague input/output, missing validation
   - Domain Model: concepts referenced in FRs but not in glossary, missing state transitions
   - Architecture: components without interface contracts, information flows at abstract level, missing DB schemas
2. **Increment `revision`** in frontmatter and update `revised` timestamp.
3. **Write the checkpoint** with structured Open Items. The heading must include the revision number so readers know which iteration it belongs to:

```markdown
## Session Checkpoint (Revision N)
> Last updated: <YYYY-MM-DD HH:mm>

### Decisions Made
- <key decision 1>
- <key decision 2>

### Open Items

| Section | Item | What's Missing | Priority |
|---------|------|---------------|----------|
| FR-3 | Input | Batch size limit undecided | High |
| Architecture | AuthService ↔ SessionManager | Interface contract not defined | High |
| FR-5 ↔ FR-7 | Concurrency | Conflict handling undecided | Medium |
| Domain | Session | "Paused" state transitions incomplete | Medium |

### Next Steps
- <suggested work items for the next iteration, derived from Open Items>
```

This enables a new session to pick up where the previous one left off.

### Iteration Mode Entry

When entering **Iteration** mode:
1. Read the checkpoint first.
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

## Change Log

When modifying an existing spec (Iteration mode), record changes inline:

```markdown
## Change Log

| Revision | Date | Section | Change | Reason |
|----------|------|---------|--------|--------|
| 1 | 2026-04-01 | FR-3 | Added error handling for empty input | Edge case discovered during implementation |
| 1 | 2026-04-01 | Domain | Added "Archive" state to Session | New requirement FR-15 |
```

This replaces the separate co-revise process.

## Upstream Feedback Issues

During the specification process, problems in upstream artifacts (use cases) may surface. When this happens:

1. **Note the problem** — describe what's wrong with the upstream artifact.
2. **Ask the user** — "I noticed UC-3 has a vague situation. Should I create a GitHub Issue to track this?"
3. **If approved, create a GitHub Issue:**
   - **Labels:** `usecase` + `feedback`
   - **Title:** Brief description of the problem
   - **Body:** Include the artifact reference, what's unclear, and how it affects the current work. Include a clickable markdown link to the artifact file.
4. **Continue working** — don't block on the upstream issue. Make reasonable assumptions and note them.

Do NOT create issues proactively. Only create them as problems surface naturally during the interview.

## Facilitation Guidelines

- **One question at a time.** Show the next question, but give space for the previous one.
- **Stay concrete.** Anchor to specific use cases and FRs, not abstract theory.
- **Use the user's language.** Don't introduce jargon unless the user does.
- **Don't design the solution.** Capture what the system needs, not how to implement it.
- **Flag cross-phase dependencies.** If a requirement change implies a domain or architecture change, say so.
- **Every 3-4 items:** Brief progress snapshot.

## Wrapping Up

The specification ends only when the user says so. Never conclude on your own — even if all phases seem complete, the user may want to revisit or go deeper.

When the user indicates they're done, ask whether they want to:
- **End this iteration** (come back later to refine further)
- **Finalize** (mark as complete for coding agent)

### End Iteration (not finalizing)

Run the spec-reviewer agent, walk through flagged issues with the user, scan for open items, increment revision, write the session checkpoint and change log, append the interview transcript, and report.

For the full step-by-step checklist, read **`references/session-procedures.md`** → "End Iteration" section.

### Finalize

Verify technology stack is filled, run the spec-reviewer agent (all issues must be resolved), write the final session checkpoint, set `status: final`, show spec feedback issues, and report.

For the full step-by-step checklist, read **`references/session-procedures.md`** → "Finalize" section.

### Output Format

Follow the Specification template in `references/output-template.md` for the final file structure, field rules, and required sections.
