# co-think/co-revise Retrospective
> Date: 2026-03-30

## Context
co-think pipeline (story → requirement → domain → architecture) and co-revise skill usage retrospective, aimed at identifying skill improvements.

## What Worked

### Story collection for initial idea exploration
- Effective for structuring raw ideas into job stories
- Requirement redirect ("let's handle that in the requirement phase") is valid at this stage — helps maintain focus on the "why" before diving into the "how"

### Domain (concept/terminology alignment)
- Independently valuable in all situations
- Clarifying terms and relationships early prevents confusion in later stages

### Architecture for initial design
- Component identification, information flow mapping, and ERD design are valuable when designing a system from scratch
- The abstraction level guard (what vs how) helps avoid premature implementation decisions

## Problems

### 1. Story ↔ Requirement boundary is blurry
- When working on top of existing implementation (feature addition, bug fixing), story and requirement discussions intermix naturally
- The redirect ("that's a requirement concern") breaks flow in these situations
- **Key distinction**: initial idea exploration (story-first works) vs. iterating on existing implementation (everything discussed together)

### 2. Requirement ↔ Architecture separation cost
- The difference is mostly detail level, not substance
- On initial design: both stages contribute new insights
- After initial design: changes require updating both documents — maintenance overhead with little added value
- Architecture becomes "reformatting requirement content into diagrams" rather than discovering new architectural insights

### 3. co-revise doesn't match reality
- Document changes happen simultaneously with code changes, not as a separate process
- Creating GitHub Issues for upstream feedback and then running co-revise adds overhead without matching the actual workflow
- In practice: documents are updated inline during feature work, issues are not created
- **Sufficient alternative**: record the change reason directly in the document (what changed and why)

## Improvement Directions (Draft)

### Story skill overhaul → Use Case skill

**Terminology change:** story → use case. STORY-N → UC-N.

**Abstraction guard:**
- Skill must guide discussion toward **how the user uses the system** — not how the system is built
- LLM must never ask implementation-level questions (data schemas, hook mechanisms, API design, technology choices)
- Context and use case content must not contain implementation terms
- When the user mentions implementation details → ask for the intent behind it and convert to user behavior level

**Format change:** Job Story (When/I want to/so I can) → Use Case structure:

- **Actors section**: table of all actors with descriptions (top of file)
- **Use Case Diagram**: PlantUML use case diagram showing actors, use cases, and relationships (include/extend). Use PlantUML's inline description syntax for each use case to show purpose at a glance. Notes for additional context where needed.
- **Individual use case format**:
  - Actor
  - Goal
  - Situation (context/trigger)
  - Flow (numbered user-level action steps — no implementation details)
  - Expected Outcome

**Rationale:**
- Job Story compresses into one sentence, losing the flow
- The actual consumer of the file is the next-stage LLM, not the user — but the user still reviews them, and visible flow matters
- User is more familiar with use case style
- Actor/Goal visibility and PlantUML diagram give a quick overview of the whole system from the user's perspective

### Merge domain + requirement + architecture into one skill
- domain, requirement, architecture are an interacting process — separating them forces artificial phase boundaries
- Requirement naturally drifts to implementation-level detail, which overlaps with architecture. The skill tries to keep it abstract, but that conflicts with how users actually work
- **Proposed pipeline**: story → design (working title)
  - **story**: idea exploration, "why" collection. Independent skill, works well as-is
  - **design**: unified skill combining domain (terminology/concepts) → requirement (what the system needs) → architecture (components/flows). One session, interleaving allowed, no forced phase transitions
- Domain work (glossary, concept relationships, state transitions) becomes the first topic within design — establish shared language before diving into requirements and components
- Reduces pipeline steps, output files to maintain, and eliminates the requirement ↔ architecture duplication problem

### Session continuity
- domain + requirement + architecture work often spans multiple sessions — cannot finish in one sitting
- The output file must record **session checkpoint state**: what was decided, what remains undecided, and what to work on next
- This enables a new session to pick up where the previous one left off, without re-reading the full transcript or losing context
- Without this, each new session starts cold and risks re-discussing already-settled decisions

### Replace co-revise
- Remove the separate Issue → co-revise process
- Instead: inline change log in each document (what changed, why, when)
