---
name: co-think-spec
description: "This skill should be used when the user needs to create or iterate on a software specification — combining domain modeling, functional requirements, and architecture in one session. Trigger when the user says 'spec', 'specification', 'design the system', 'define requirements', 'domain model', 'architecture', 'what should we build', 'system design', 'component design', 'let's spec this out', 'define the system', or when use cases from co-think-story need to be turned into a buildable specification."
argument-hint: <path to use case/story file(s), or existing .spec.md file for iteration>
allowed-tools: Read, Write, Agent, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Specification Builder

Takes use cases (or job stories) and builds a unified specification — domain model, functional requirements, and system architecture — through collaborative dialogue in a single session. Phases interleave naturally; no forced boundaries.

## Modes

This skill operates in two modes, determined by the input:

### First Design

Input is a use case / story file (no existing `.spec.md`). Follows a guided sequence:

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
2. **Partial match** — glob for `A4/co-think/*<argument>*.story.md`, `A4/co-think/*<argument>*.usecase.md`, and `A4/co-think/*<argument>*.spec.md`
3. **Multiple matches per type** — present the candidates and ask the user to pick
4. **No match** — inform the user and ask for a different term

After resolution, present the resolved file(s) and ask the user to confirm before reading:

> **Resolved input files:**
> - `A4/co-think/agent-orchestrator.story.md`
>
> Proceed with these files?

**Mode detection:**
- If the target `.spec.md` file already exists → **Iteration** mode. Read the spec file and its source references.
- If only story/use case files are found (no existing spec) → **First Design** mode.

The source reference in the output file should be placed as a blockquote under the title heading, linking to all input files (see output template for format).

After reading, list all use cases (or stories) and any existing spec content found, then confirm with the user before proceeding.

## Step 0: Explore the Codebase

Before starting, explore the current codebase to understand:

- **Project structure** — directories, key files, tech stack
- **Existing features** — what's already built, patterns in use
- **Domain terms already in use** — naming conventions, existing entities, vocabulary
- **Existing architecture** — current components, services, communication patterns
- **Database** — existing schemas, migrations, ORM usage
- **Constraints** — frameworks, conventions, dependencies that the spec should respect

This grounds the specification in reality. Reference what you find during the interview — e.g., "I see the project already uses the term 'Workspace' for grouping items. Should we align with that?"

## Navigation

The spec covers three phases. In **First Design** mode, start with Requirements and follow the guided sequence. In **Iteration** mode, start wherever the user wants.

The user controls all transitions — revisiting and interleaving are always welcome. Do NOT auto-advance to the next phase. After completing work on any topic (or when the conversation reaches a natural pause), present the current status:

> Here's where we are:
>
> | Phase | Status |
> |-------|--------|
> | Requirements | 5 FRs defined |
> | Domain Model | 3 concepts, 2 relationships |
> | Architecture | Not started |
>
> What would you like to work on next? We can continue here, move to another phase, or wrap up.

## Phase 1: Functional Requirements

### Step 1.1: Determine Software Type

Before diving into individual stories, ask the user:

> "Does this software have a user interface (web, mobile, desktop, CLI with TUI), or is it non-UI (API, library, automation script, plugin)?"

| Type | Requirements focus |
|------|-------------------|
| **UI** | Screens, user interactions, navigation, visual states, input/output per screen |
| **Non-UI** | Commands/endpoints, input/output contracts, business logic rules, integration points |

If the software has both UI and non-UI parts, note which stories belong to which.

### Step 1.2: Story-by-Story Specification

Work through stories one at a time. For each story:

1. **Present the story** and confirm it's still relevant.
2. **Check story size** — if the story is too big (3+ independent behaviors), decompose it first.
3. **Decide mock need** — for UI stories, judge whether a mock UI would make the conversation easier.
4. **Ask clarifying questions** — one at a time — to fill in the gaps.
5. **Draft the spec** and present it for confirmation.
6. **Stay until concrete** — do not move to the next story until the current spec is detailed enough for AI to develop.
7. Move to the next story only when the user confirms.

#### Story Decomposition

When a story is too big:
1. Tell the user: "This story seems to cover multiple distinct behaviors. I'd like to break it down."
2. Propose sub-stories.
3. Once confirmed, proceed to specify each sub-story individually.

#### Mock UI

For UI software, judge whether creating a mock UI would help clarify the spec. When helpful:
1. Use the **mock-html-generator** agent to create an HTML mock. Save to `A4/co-think/mock/<topic-slug>/`.
2. Present the mock, gather feedback, iterate if needed.
3. Use the feedback to refine the spec. Record the mock file path.

#### What to clarify per story

**For UI software:**
- Where does this happen? (which screen/view)
- What does the user see? (elements, information, initial state)
- What does the user do? (interactions, step-by-step flow)
- What changes? (state transitions, feedback, result)
- What can go wrong? (error states, validation, edge cases)

**For non-UI software:**
- What triggers this? (command, API call, event, schedule)
- What goes in? (input format, parameters, validation)
- What comes out? (output format, success response)
- What are the rules? (business logic, conditions, ordering)
- What can go wrong? (error cases, invalid input, failure modes)

#### Question techniques

- Ask about **concrete scenarios**: "If a user does X in this situation, what should happen?"
- Ask about **edge cases**: "What if the input is empty? What if there are 10,000 items?"
- Ask about **boundaries**: "Is there a limit? What's the maximum/minimum?"
- When the user is unsure, offer 2-3 concrete options.

After each story spec is confirmed, write the FR to the output file immediately and update the task.

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

- **Information flow** (per story):
  - For each story involving this component, map the information flow between components
  - Present as PlantUML sequence diagram — one per story
  - Abstraction level: "A sends user information to B" — no communication method or data format details

### Topic 3.3: Consistency Check

Verify the architecture against all inputs and across diagrams:

- **Cross-diagram consistency**: component diagram, sequence diagrams, and ERDs reference the same components and data
- **Domain model coverage**:
  - Core concepts housed in at least one component
  - Cross-boundary relationships reflected in information flows
  - State transition responsibilities assigned to components
- **Story coverage**: every story has at least one sequence diagram

Present any gaps found and discuss with the user.

### Technology Choices

When a technology choice arises:
- **Lightweight decisions** — discuss inline and record with brief rationale.
- **Heavy decisions** — ask the user: "This seems like a decision worth investigating more deeply. Would you like to use `/workflow:spark-decide` to evaluate options?"

## Abstraction Level Guards

THIS IS CRITICAL — applied per phase:

### Requirements
- Capture **what the software should do**, not how to implement it
- No technology choices, no data schemas, no API endpoint designs

### Domain Model
- "What exists and how it connects" = confirmed, "how to build it" = not decided
- No implementation types (VARCHAR, INT) in class diagrams
- No API endpoints or serialization formats

### Architecture
- "What components exist and what information they exchange" = confirmed, "how to build each component" = not decided
- Sequence diagrams show WHAT information flows, not HOW (no HTTP methods, no JSON schemas)
- DB schemas define entities and relationships, not implementation details (no index strategies)

When the user drifts into implementation, redirect gently: "That's an implementation detail we can decide during development. Here, let's focus on [what's appropriate for the current phase]."

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

At the end of each session (whether wrapping up or pausing), write a checkpoint section at the bottom of the output file:

```markdown
## Session Checkpoint
> Last updated: <YYYY-MM-DD HH:mm>

### Decisions Made
- <key decision 1>
- <key decision 2>

### Open Items
- <undecided topic 1>
- <undecided topic 2>

### Next Steps
- <what to work on next>
```

This enables a new session to pick up where the previous one left off. When entering **Iteration** mode, read the checkpoint first and present it to the user before continuing.

## Change Log

When modifying an existing spec (Iteration mode), record changes inline:

```markdown
## Change Log

| Date | Section | Change | Reason |
|------|---------|--------|--------|
| 2026-04-01 | FR-3 | Added error handling for empty input | Edge case discovered during implementation |
| 2026-04-01 | Domain | Added "Archive" state to Session | New requirement FR-15 |
```

This replaces the separate co-revise process.

## Upstream Feedback Issues

During the specification process, problems in upstream artifacts (use cases / stories) may surface. When this happens:

1. **Note the problem** — describe what's wrong with the upstream artifact.
2. **Ask the user** — "I noticed STORY-3 has a vague situation. Should I create a GitHub Issue to track this?"
3. **If approved, create a GitHub Issue:**
   - **Labels:** `story` + `feedback`
   - **Title:** Brief description of the problem
   - **Body:** Include the artifact reference, what's unclear, and how it affects the current work. Include a clickable markdown link to the artifact file.
4. **Continue working** — don't block on the upstream issue. Make reasonable assumptions and note them.

Do NOT create issues proactively. Only create them as problems surface naturally during the interview.

## Facilitation Guidelines

- **One question at a time.** Show the next question, but give space for the previous one.
- **Stay concrete.** Anchor to specific stories and FRs, not abstract theory.
- **Use the user's language.** Don't introduce jargon unless the user does.
- **Don't design the solution.** Capture what the system needs, not how to implement it.
- **Flag cross-phase dependencies.** If a requirement change implies a domain or architecture change, say so.
- **Every 3-4 items:** Brief progress snapshot.

## Wrapping Up

The specification ends only when the user says so. Never conclude on your own — even if all phases seem complete, the user may want to revisit or go deeper.

When the user indicates they're done:

1. **Run the spec-reviewer agent** — invoke the `spec-reviewer` agent with the current output file path and all input file paths. The agent evaluates requirements, domain model, architecture, and cross-section consistency in one pass.
2. **Present the review results** — show the user the review report. For each flagged issue, walk through it one at a time. The user can accept, modify, or dismiss each suggestion.
3. **Update the output file** with any revisions from the review.
4. **Write the session checkpoint** — capture decisions made, open items, and next steps.
5. **Write the change log** (Iteration mode only) — record what changed and why.
6. **Finalize the file** — set `status: final` in frontmatter, ensure all sections are complete.
7. **Show the Spec Feedback section prominently** — list all filed upstream feedback GitHub Issues.
8. **Write the file** using the Write tool.
9. **Report the path** so the user can reference it.

### Output Format

Follow the Specification template in `references/output-template.md` for the final file structure, field rules, and required sections.
