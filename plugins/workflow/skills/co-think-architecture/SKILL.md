---
name: co-think-architecture
description: "This skill should be used when the user has functional requirements, domain model, and job stories and needs to design system architecture, when the user says 'architecture', 'system design', 'design the system', 'component design', 'design components', 'DB schema', 'database schema', 'information flow', 'component diagram', 'system structure', 'how should the system be structured', 'tech stack', or when domain modeling is complete and the next step is to define components, their communication, and data storage."
argument-hint: <path to story, requirement, and/or domain model file(s)>
allowed-tools: Read, Write, Agent, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode
---

# Architecture Designer

Takes job stories, functional requirements, and domain model to design system architecture through collaborative dialogue. Through one-question-at-a-time conversation, identify components, their information flows, and database schemas.

## Input

Read the file(s) provided: **$ARGUMENTS**

If no files are provided, ask the user for the paths to:
1. **Job Stories** (from co-think-story)
2. **Functional Requirements** (from co-think-requirement)
3. **Domain Model** (from co-think-domain) — reference material, not a strict mapping source

The `source` frontmatter field in the output file should contain wikilinks to all input files (filename only, no path).

After reading, summarize the key stories, FRs, and domain concepts found, then confirm with the user before proceeding.

## Step 0: Explore the Codebase

Before starting the architecture design, explore the current codebase to understand:

- **Project structure** — directories, key files, tech stack
- **Existing architecture** — current components, services, communication patterns
- **Database** — existing schemas, migrations, ORM usage

This grounds the architecture in reality. Reference what you find during the interview — e.g., "I see the project already uses PostgreSQL with a users table. Should we build on that?"

## Navigation Rules

Topics follow a natural order (Component Identification → Per-Component Deep Dive → Consistency Check). The user controls all transitions, revisiting and interleaving are welcome.

## Conversation Topics

The architecture design covers three topics. Do NOT auto-advance to the next topic — always ask the user where they want to go next.

After completing work on any topic (or when the conversation reaches a natural pause), present the current status and ask:

> Here's where we are:
>
> | Topic | Status |
> |-------|--------|
> | Component Identification | 3 components identified |
> | Per-Component Deep Dive | 1 of 3 done |
> | Consistency Check | Not started |
>
> What would you like to work on next? We can continue here, move to another topic, or wrap up.

### Topic 1: Component Identification

Identify the major components of the system from the input materials.

- Read stories, FRs, and domain model to propose an initial set of components
- Present the component list with a brief description of each component's responsibility
- Through interview, confirm: component name, responsibility, whether it has its own data store
- Present as PlantUML component diagram showing components and their relationships
- Accompanied by text explanation

### Topic 2: Per-Component Deep Dive

For each confirmed component, design in detail through conversation:

- **DB schema** (if the component has its own data store):
  - Identify entities, attributes, and relationships
  - Present as PlantUML IE diagram
  - Accompanied by text explanation
  - Note: not all components need a DB schema — ask "Does this component store its own data?" before diving in

- **Information flow** (per story):
  - For each story that involves this component, map the information flow between components
  - Present as PlantUML sequence diagram — one per story
  - Abstraction level: "A sends user information to B" — no communication method or data format details
  - Accompanied by text explanation

### Topic 3: Consistency Check

Verify the architecture against all inputs and across diagrams:

- **Cross-diagram consistency**: component diagram, sequence diagrams, and ERDs reference the same components and data
- **Domain model coverage**:
  - Core concepts from the glossary are housed in at least one component
  - Relationships that cross component boundaries are reflected in information flows
  - State transition triggers and management responsibilities are assigned to components
- **Story coverage**: every story has at least one sequence diagram

Present any gaps found and discuss with the user how to address them.

## Technology Choices

When a technology choice arises during the conversation:

- **Lightweight decisions** — discuss inline and record the decision with a brief rationale in the output file. (e.g., "PostgreSQL — relational data, team experience")
- **Heavy decisions** — ask the user: "This seems like a decision worth investigating more deeply. Would you like to use `/workflow:spark-decide` to evaluate options?" Respect the user's choice.

## Abstraction Level Guard

THIS IS CRITICAL — the key differentiator of this skill:

- The boundary is: "what components exist and what information they exchange" = confirmed, "how to build each component" = not decided
- If the user drifts into implementation details (API endpoint paths, request/response schemas, framework choices, code structure), redirect: "That's an implementation detail we can decide later. Here, let's focus on what information [component A] needs from [component B] and why."
- Sequence diagrams show WHAT information flows, not HOW (no HTTP methods, no JSON schemas, no endpoint paths)
- DB schemas define entities and relationships, not implementation details (no index strategies, no specific column types beyond what's needed for clarity)
- DO include: component names, responsibilities, entity names, attributes, relationships, multiplicities, information flow descriptions, story references
- DO NOT include: API endpoint designs, request/response schemas, framework-specific patterns, deployment configurations, code directory structures

## Progressive File Writing

### Working File Path

At the start of the session, determine the file path:
- Default: `A4/co-think/<YYYY-MM-DD-HHmm>-<topic-slug>.architecture.md` relative to working directory
- Ask the user only if they want a different location
- Create the directory if needed

Tell the user the file path so they can follow along: "I've started a working file at `<path>`. It will update as we go."

### How to Update

- **Use the Write tool** to rewrite the entire file each time. This keeps the file consistent and avoids partial edit issues.
- **Preserve all previously confirmed content** — never remove or reorder confirmed components, schemas, or diagrams.
- After each component is confirmed, update the component diagram and file.
- After each deep dive is complete, add the ERD and sequence diagrams.
- Show progress: "That's 3 components identified, 1 deep dive complete. Let's continue."

## Facilitation Guidelines

- **Stay concrete.** Anchor to specific stories and FRs, not abstract architecture theory.
- **Use the user's language.** Don't introduce architecture jargon unless the user does.
- **Don't over-design.** Capture what the system needs, not what would be theoretically elegant.
- **Flag cross-component dependencies.** If a story involves multiple components, note the information flow explicitly.
- **Every 3-4 exchanges:** Brief progress snapshot.
- **Domain model is a reference, not a spec.** Use it to check for gaps, not as a checklist to mechanically convert.

## Wrapping Up

The architecture design ends only when the user says so. Never conclude on your own — even if all components seem covered, the user may want to revisit or go deeper. Keep working until the user explicitly ends the session.

When the user indicates they're done:

1. **Run the architecture-reviewer agent** — invoke the `architecture-reviewer` agent with the current output file path and all input file paths. The agent evaluates the architecture for component completeness, story coverage, domain model coverage, diagram consistency, and abstraction level.
2. **Present the review results** — show the user the review report. For each flagged issue, walk through it one at a time:
   - `MISSING COMPONENT` — ask what component should handle it and add it
   - `UNCOVERED STORY` — design the sequence diagram together
   - `MISSING DOMAIN CONCEPT` — ask which component should own it
   - `MISSING FLOW` — identify the information flow and add it
   - `INCONSISTENT` — present the inconsistency and ask how to resolve
   - `TOO CONCRETE` — suggest how to abstract it
   - The user can accept, modify, or dismiss each suggestion. Respect their decision.
3. **Update the output file** with any revisions from the review.
4. **Finalize the file** — change `status: draft` to `status: final` in frontmatter, ensure all sections are complete, remove any placeholder text.
5. **Write the file** using the Write tool.
6. **Report the path** so the user can reference it.

### Output Format

Follow the Architecture template in `references/output-template.md` for the final file structure, field rules, and required sections.
