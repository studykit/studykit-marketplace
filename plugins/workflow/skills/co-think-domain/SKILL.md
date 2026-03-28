---
name: co-think-domain
description: "This skill should be used when the user has functional requirements (FR) and needs to extract domain concepts, when the user says 'domain modeling', 'concept modeling', 'extract concepts', 'define terms', 'conceptual model', 'domain model', 'ubiquitous language', 'entity extraction', 'domain glossary', 'what are the entities', 'map relationships', or when FRs from co-think-requirement need cross-cutting analysis to identify domain entities, relationships, state transitions, and gaps."
argument-hint: <path to requirement and/or story file(s)>
allowed-tools: Read, Write, Agent, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode
---

# Conceptual Model Builder

Takes functional specifications and job stories to extract domain concepts through cross-cutting analysis. Through one-question-at-a-time dialogue, identify domain entities, their relationships, state transitions, and gaps in the specifications.

## Input

Resolve the input from **$ARGUMENTS** using the file resolution rules below, then read the file(s).

If no argument is provided, ask the user for a slug, filename, or path.

### File Resolution

Arguments can be full paths, partial filenames, or slugs. Resolve them by searching `A4/co-think/`:

1. **Full path** — use directly
2. **Partial match** — glob for `A4/co-think/*<argument>*.requirement.md` and `A4/co-think/*<argument>*.story.md` (e.g., `agent-orchestrator` → finds both the requirement and story files)
3. **Multiple matches per type** — present the candidates and ask the user to pick
4. **No match** — inform the user and ask for a different term

After resolution, present the resolved file(s) and ask the user to confirm before reading:

> **Resolved input files:**
> - `A4/co-think/2026-03-28-1030-agent-orchestrator.requirement.md`
> - `A4/co-think/2026-03-27-1500-agent-orchestrator.story.md`
>
> Proceed with these files?

Required input files:
1. **Functional Requirements** (`.requirement.md`) — primary input for concept extraction
2. **Job Stories** (`.story.md`) — provides user context and motivation behind the requirements

The source reference in the output file should be placed as a blockquote under the title heading, linking to all input files (see output template for format).

After reading, list all FRs and Job Stories found across all files and confirm with the user before proceeding.

## Step 0: Explore the Codebase

Before starting the conceptual model, explore the current codebase to understand:

- **Project structure** — directories, key files, tech stack
- **Existing features** — what's already built, patterns in use
- **Domain terms already in use** — naming conventions, existing entities, vocabulary

This grounds the conceptual model in reality. Reference what you find during the interview — e.g., "I see the codebase already uses the term 'Workspace' for grouping items. Should we align with that?"

## Navigation Rules

Topics follow a natural order (Concept Extraction → Relationship Mapping → State Transition Analysis → Spec Feedback). The user controls all transitions, revisiting and interleaving are welcome.

## Conversation Topics

The conceptual model covers four topics. The user controls which topic to work on, when to switch, and when to revisit. Do NOT auto-advance to the next topic — always ask the user where they want to go next.

After completing work on any topic (or when the conversation reaches a natural pause), present the current status and ask:

> Here's where we are:
>
> | Topic | Status |
> |-------|--------|
> | Concept Extraction | 5 concepts defined |
> | Relationship Mapping | Not started |
> | State Transitions | Not started |
> | Spec Feedback | Not started |
>
> What would you like to work on next? We can continue here, move to another topic, or wrap up.

### Topic 1: Concept Extraction

- Read all FRs horizontally — identify concepts (entities) that appear across multiple FRs
- Present the initial concept list to the user
- For each concept, through interview confirm: name, definition, 1-2 key attributes
- Track which FRs reference each concept

### Topic 2: Relationship Mapping

- Identify relationships between concepts
- Present as PlantUML class diagram (concept name + key attributes only, NO implementation types)
- Accompanied by text explanation of each relationship
- Diagram should show multiplicity (1..*, 0..1, etc.) where relevant

### Topic 3: State Transition Analysis

- Identify which concepts have state changes across FRs
- For each stateful concept, map states, transitions, conditions, triggers
- Present as PlantUML state diagram
- For multi-entity processes, use composite states
- Accompanied by text explanation

### Topic 4: Spec Feedback (Dependencies/Conflicts/Gaps)

- Identify missing scenarios, contradictions, undefined edge cases across FRs
- For each issue found, create a GitHub Issue (with user approval) using the Upstream Feedback Issues process
- Record the filed issues in the Spec Feedback section with links
- Format: `- FR-X, FR-Y: <reason and explanation> → #<issue-number>`

## Abstraction Level Guard

THIS IS CRITICAL — the key differentiator of this skill:

- The boundary is: "what exists and how it connects" = confirmed, "how to build it" = not decided
- If the user drifts into implementation (specific DB types, API endpoints, framework choices), redirect: "That's an implementation decision for the architecture phase. Here, let's focus on what [concept] means in the domain and how it relates to [other concept]."
- Do NOT include implementation types (VARCHAR, INT, etc.) in class diagrams
- Do NOT specify API endpoints or serialization formats in interfaces
- DO include: concept names, key attributes (without types), relationships, multiplicities, constraints, state transitions, conditions

## Progressive File Writing

### Working File Path

At the start of the session, determine the file path:
- Default: `A4/co-think/<YYYY-MM-DD-HHmm>-<topic-slug>.domain.md` relative to working directory
- Ask the user only if they want a different location
- Create the directory if needed

Tell the user the file path so they can follow along: "I've started a working file at `<path>`. It will update as we go."

### How to Update

- **Use the Write tool** to rewrite the entire file each time. This keeps the file consistent and avoids partial edit issues.
- **Preserve all previously confirmed content** — never remove or reorder confirmed concepts, relationships, or diagrams.
- After each concept is confirmed, update the glossary table and the file.
- After relationships are mapped, add the class diagram.
- After states are analyzed, add state diagrams.
- Show progress: "That's 5 concepts defined, 3 relationships mapped. Let's continue."

## Facilitation Guidelines

- **Show the next question, but give space for the previous one.** After processing the user's answer, present the next question — then use AskUserQuestion to let the user either answer the new question or continue discussing the previous topic. This handles both paths in one turn.
- **Stay concrete.** Anchor to specific FRs, not abstract domain theory.
- **Use the user's language.** Don't introduce DDD jargon unless the user does.
- **Don't design the solution.** Capture what exists in the domain, not how to implement it.
- **Flag cross-spec dependencies.** If concepts span multiple spec files, note explicitly.
- **Every 3-4 concepts:** Brief progress snapshot.

## Upstream Feedback Issues

During the conceptual modeling process, problems in upstream artifacts (Job Stories or Functional Requirements) may surface. When this happens:

1. **Note the problem** — describe what's wrong with the upstream artifact (e.g., missing behavior in a requirement, vague story that led to an ambiguous concept).
2. **Ask the user** — "I noticed FR-5 doesn't define what happens when X. This makes the domain model incomplete. Should I create a GitHub Issue to track this?"
3. **If approved, create a GitHub Issue:**
   - **Labels:** `story` or `requirement` (matching the upstream artifact type) + `feedback`
   - **Title:** Brief description of the problem
   - **Body:** Include the artifact reference (e.g., FR-5), what's unclear, and how it affects the current domain modeling work. Include a clickable markdown link to the artifact file (e.g., `[path/to/file.md](https://github.com/{owner}/{repo}/blob/main/path/to/file.md)`).
4. **Continue modeling** — don't block on the upstream issue. Make reasonable assumptions and note them. The issue will be addressed via co-revise later.

This replaces the previous approach of embedding feedback only in the Spec Feedback section. The Spec Feedback section now captures issues that have already been filed as GitHub Issues, with links to those issues.

Do NOT create issues proactively by scanning all FRs at once. Only create them as problems surface naturally during the modeling interview.

## Wrapping Up

The conceptual model ends only when the user says so. Never conclude on your own — even if all concepts seem covered, the user may want to revisit or go deeper. Keep working until the user explicitly ends the session.

When the user indicates they're done:

1. **Run the domain-reviewer agent** — invoke the `domain-reviewer` agent with the current output file path and all input file paths (requirements, stories). The agent evaluates every concept for completeness, definition clarity, relationship coverage, state transitions, diagram correctness, and spec feedback quality.
2. **Present the review results** — show the user the review report. For each flagged issue, walk through it one at a time:
   - `MISSING CONCEPT` — ask what the concept is and add it
   - `MISSING RELATIONSHIP` — propose the relationship and confirm
   - `MISSING STATE` — present the state transitions and confirm
   - `VAGUE FEEDBACK` — make the feedback item more specific
   - The user can accept, modify, or dismiss each suggestion. Respect their decision.
3. **Update the output file** with any revisions from the review.
4. **Finalize the file** — change all glossary items to final, ensure all sections are complete.
5. **Show the Spec Feedback section prominently** — list all filed GitHub Issues with their status.
6. **Ask:** "These items have been filed as GitHub Issues. Would you like to run co-revise to address them?"
7. **Write the file** using the Write tool.
8. **Report the path** so the user can reference it.

### Output Format

Follow the Conceptual Model template in `references/output-template.md` for the final file structure, field rules, and required sections.
