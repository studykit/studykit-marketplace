---
name: auto-usecase
description: "This skill should be used when the user wants to autonomously generate a complete Use Case document from an idea or brainstorm input without interactive interview. Triggers: 'auto-generate use cases', 'auto-usecase', 'generate use cases from this idea', 'create use case doc automatically', 'no interview needed just generate', 'run auto-usecase on', or when the user provides an idea/brainstorm and wants a .usecase.md file produced without back-and-forth dialogue."
argument-hint: <idea, brainstorm text, or file path to generate use cases from>
allowed-tools: Read, Write, Edit, Agent, Glob, Grep, Bash, WebSearch, WebFetch, TeamCreate, SendMessage, TaskCreate, TaskUpdate, TaskList
---

# Autonomous Use Case Generator

Generate a complete `.usecase.md` file from raw input — an idea, brainstorm notes, a description, or a file path — without human interaction. Make all decisions independently, record assumptions in Open Questions, and refine until the document meets quality standards.

Generate use cases for: **$ARGUMENTS**

## Shared References

Before doing any analysis, read these files. They define the rules and format you must follow.

- `${SKILL_DIR}/../co-think-usecase/references/output-template.md` — exact output format (use **auto-usecase** sections)
- `${SKILL_DIR}/../co-think-usecase/references/usecase-splitting.md` — when and how to split oversized use cases
- `${SKILL_DIR}/../co-think-usecase/references/usecase-relationships.md` — dependency and reinforcement analysis
- `${SKILL_DIR}/../co-think-usecase/references/abstraction-guard.md` — banned implementation terms and conversion rules
- `${SKILL_DIR}/../co-think-usecase/references/review-report.md` — how to persist reviewer reports
- `${SKILL_DIR}/../co-think-usecase/references/research-report.md` — how to persist research results

If `SKILL_DIR` is not resolved, locate the workflow plugin via Glob for `plugins/workflow/skills/co-think-usecase/references/`.

## Use Case Format

Every Use Case follows the structure defined in `output-template.md` with one addition for autonomous mode:

- **Source** field — tracks where each UC originated:
  - `input` — derived from the user's idea or brainstorm
  - `research — <which systems>` — discovered from similar systems research
  - `implicit` — discovered during analysis as a prerequisite or complement

## Resume Detection

Before starting, check for existing progress:

1. **Research report:** If `A4/co-think/<topic-slug>.usecase.research-initial.md` exists, skip Step 3 and use the existing results.
2. **Output file with checkpoint:** If `A4/co-think/<topic-slug>.usecase.md` exists and contains a **Session Checkpoint** section:
   - Read the checkpoint to determine the **last completed step**.
   - **Resume from the next step** — do not repeat completed work.
   - If the checkpoint shows a step was in progress, re-run that step from the beginning (the file state is the pre-step state).
3. **Review reports:** Read any existing `A4/co-think/<topic-slug>.usecase.review-*.md` files to understand what was already flagged and fixed.

This allows recovery from API limits, context window exhaustion, or other interruptions without starting over.

## Step-by-Step Process

### Step 1: Understand the Input

The input has two components:

1. **New idea** (required) — the feature, idea, or brainstorm to turn into use cases. Can be a file path (read it), inline content, or a vague description.
2. **Target system** (optional) — an existing `.usecase.md` file, topic slug, or partial name. If absent, create from scratch.

Determine the **topic slug** (lowercase, hyphen-separated, 2–5 words). Output path: `A4/co-think/<topic-slug>.usecase.md`.

### Step 2: Load System Context (when target system exists)

If a target system file exists, read it and extract: Context, Actors, existing UCs, Relationships, and domain language. Preserve the existing revision number and increment it when writing.

### Step 3: Research Similar Systems

Launch a research subagent in the background via `TeamCreate`. **Do not wait** — proceed to Steps 4a and 4b while research runs.

Prompt the subagent:

> Research similar systems to "<system context/description>".
>
> **Goal:** Discover features and use cases that users of this type of system commonly need.
>
> 1. Search for comparable apps/tools/services. Try 2–3 different search queries.
> 2. For each similar product (up to 5), list name + key user-facing features as "Actor does X to achieve Y".
> 3. Identify UC candidates common across 3+ systems (high-value signals).
> 4. Identify UC candidates unique to 1 system (niche/innovative).
> 5. Look for user reviews or feature requests indicating unmet needs.
>
> Return: **Similar systems**, **High-value UC candidates**, **Niche UC candidates**, **User-requested features**.

Save the full research results per `references/research-report.md` (label: `initial`). The results feed into Step 4c (UC extraction) and Step 4g (practical value evidence).

### Step 4: Analyze the Input

Work through the content systematically. Do NOT ask the user questions — make your best judgment and record uncertainties in Open Questions.

#### 4a. Define the Problem Space

**New system:** Summarize in 2–4 sentences (what problem, who's affected, why it matters) → becomes the Context section.

**Adding to target system:** Preserve existing Context unchanged. Record scope expansion concerns in Open Questions.

#### 4b. Discover Actors

Identify every person or system that interacts with the software. For each: Name, Type (`person`/`system`), Role, Description.

Rules:
- **When target system exists:** reuse existing actors where possible. Only create new actors for uncovered privilege levels.
- Prefer specific roles over generic "User"
- Distinct permission levels → separate actors
- Automated behaviors → system actor
- When unsure → split and record in Open Questions

#### 4c. Extract Use Cases

**Wait for Step 3 research results before proceeding.**

UCs come from **two sources**:
1. **From user input** — each distinct goal or situation in the idea
2. **From research** — high-value candidates from Step 3 not already covered

For each UC, fill all fields per the output template + Source field. Number sequentially: UC-1, UC-2, ... (input-derived first, then research-derived).

#### 4d. System Completeness Analysis

After initial extraction, systematically scan for UCs that the system needs but no one explicitly mentioned. Work through three lenses:

**Actor lifecycle** — for each actor, check whether the existing UCs cover their full interaction with the system:

| Stage | Question |
|-------|----------|
| Entry | How does this actor first start using the system? (signup, onboarding, invitation) |
| Core activity | What do they repeatedly do? Is the main loop fully covered? |
| Management | How do they organize, edit, delete, or search what they've created? |
| Exit | How do they leave, export data, or clean up? |

Missing stages → UC candidates with `Source: implicit`.

**Data lifecycle** — identify the key entities implied by existing UCs (e.g., "share a list" implies a List entity). For each entity, check CRUD coverage:

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| *derived from existing UCs* | UC-? or missing | UC-? or missing | UC-? or missing | UC-? or missing |

Empty cells where a user would reasonably need that operation → UC candidates with `Source: implicit`.

**Actor interaction points** — when multiple actors exist, check:
- Does one actor's output become another actor's input? (e.g., author publishes → reader views)
- Are there approval, delegation, or sharing flows between actors?
- Do permission differences require admin-level UCs? (invite, assign role, revoke access)

Missing interaction points → UC candidates with `Source: implicit`.

Finally, re-read the Context from Step 4a. If any stated goals are not yet covered by a UC, add candidates.

Number new UCs sequentially after the last UC from Step 4c.

#### 4e. Apply Splitting Rules

Evaluate each UC against `usecase-splitting.md`. When splitting, use sub-numbering: UC-3 → UC-3a, UC-3b, UC-3c.

#### 4f. Analyze Relationships

Apply `usecase-relationships.md`. When target system exists, analyze relationships between new and existing UCs.

#### 4g. Fitness and Practical Value Check

Evaluate every candidate UC before including it.

**System fitness** (target system only): Does this UC fall within the system's Context? If not → Excluded Ideas.

**Practical value** — three criteria using research evidence:

| Criterion | Include | Exclude |
|-----------|---------|---------|
| **Usage frequency** | Routine / repeated action | Rare edge case |
| **User reach** | Majority of users | Tiny subset |
| **Core goal contribution** | Directly serves system's purpose | Tangential |

Decision: 2+ "Exclude" → drop. Record in Excluded Ideas with criteria scores and evidence.

Research evidence overrides gut judgment: if similar systems commonly offer a feature, that is strong evidence for inclusion.

### Step 5: Build the PlantUML Diagram

Include all actors, all UCs (existing + new), actor→UC connections, `<<include>>` for dependencies, `<<extend>>` for reinforcements. Use PlantUML's inline description syntax.

### Step 6: Write the Document

Follow `output-template.md` using **auto-usecase** rules:
- Include: Original Idea, Context, Similar Systems Research, Actors, Use Case Diagram, Use Cases, Use Case Relationships, Open Questions, Session Checkpoint
- Include conditionally: Excluded Ideas (if any), Change Log (revision > 0 only)
- Omit: Interview Transcript

Frontmatter: `status: draft`, `revision: 0` (or increment), current date for `created`/`revised`, `tags: []`.

**Abstraction guard:** Before writing, verify every flow step against `abstraction-guard.md`. No implementation terms may appear in any UC field.

Include a Session Checkpoint with `Last Completed Step: Step 6 — Initial draft` so the file is resumable before the first review pass.

### Step 7: Self-Review and Enrichment Loop

Three sub-steps: **7a** → **7b** → **7c**. Each: **enrich** → **review** (invoke `usecase-reviewer`) → **fix**. Use `TeamCreate` to parallelize review and research when beneficial.

**Review report persistence:** After each `usecase-reviewer` invocation, save the review report per `references/review-report.md` (label: step label, e.g., `review-7a`).

**Quality checklist — run before each reviewer invocation:**

- [ ] Every UC has all required fields (Actor, Goal, Situation, Flow, Expected Outcome, Source)
- [ ] Every actor in UCs is in the Actors table with Type and Role
- [ ] Every actor in the table is referenced by at least one UC
- [ ] No flow step contains implementation terms (per abstraction-guard.md)
- [ ] No goal contains "and" signaling multiple goals
- [ ] No situation is generic — all are specific and observable
- [ ] All outcomes are observable or measurable
- [ ] PlantUML diagram includes all actors and all UCs
- [ ] Split UCs use sub-numbering (UC-3a, UC-3b)
- [ ] `status` is `draft`
- [ ] Excluded Ideas section present with reason and criteria (if any excluded)
- [ ] No new UC overlaps existing (when adding to target system)
- [ ] Similar Systems Research section present
- [ ] Open Questions populated with assumptions made

#### Step 7a — Review + Fix + Concretize

1. **Review:** Invoke `usecase-reviewer` agent on the output file.
2. **Fix:** Apply verdict table below.
3. **Enrich:** Walk every UC — strengthen vague flows, sharpen situations/outcomes, re-check research for missed high-value features (add with `Source: research`).
4. Write updated file with **Session Checkpoint** (see below).
5. **Commit to git** (see Step 7 Commit below).

#### Step 7b — Catch Remaining Gaps + Targeted Research + Review + Fix

1. **Discover remaining implicit UCs:** Step 4d should have caught most system-level gaps. This step is a safety net — for each UC, ask: "Does this assume another UC exists that isn't documented?" If 4d worked well, expect 0–2 additions here. Add missing ones with `Source: implicit`.
2. **Targeted research:** If implicit UCs found, launch subagent to research whether similar systems offer those specific features. Save results per `references/research-report.md` (label: `targeted-7b`). Use results to validate, refine flows, and discover related UCs.
3. **Fitness check:** Apply Step 4g to all new UCs. Failures → Excluded Ideas. Update diagram.
4. **Review:** Invoke `usecase-reviewer`.
5. **Fix:** Apply verdict table.
6. Write updated file with **Session Checkpoint** (see below).
7. **Commit to git** (see Step 7 Commit below).

#### Step 7c — Stabilize + Review + Fix

1. **Stabilize:** No new UCs. Consistency pass only — verify Sources, relationships, diagram.
2. **Review:** Invoke `usecase-reviewer`. Final quality gate.
3. **Fix:** Apply verdict table.
4. Write updated file with **Session Checkpoint** (see below).
5. **Commit to git** (see Step 7 Commit below).

#### Step 7 Commit

After each sub-step, stage all files under `A4/co-think/<topic-slug>.*` and commit:

```
usecase(<topic-slug>): revision N — step 7a

- UCs: <total count> (<added> added, <modified> revised)
- Reviewer verdict: <PASS / NEEDS REVISION>
- Open items: <count>
```

#### Session Checkpoint (write after each sub-step)

Update the `## Session Checkpoint` section in the output file after each sub-step, using the checkpoint format from `output-template.md` (Revision N). Add `Last Completed Step` and `Changes This Step` fields for resume support:

```markdown
## Session Checkpoint (Revision <N>)
> Last updated: <YYYY-MM-DD HH:mm>

### Last Completed Step
- Step: <step number and name, e.g., "Step 7a — Review + Fix + Concretize">
- Reviewer verdict: <PASS / NEEDS REVISION>

### Changes This Step
- <what was added, fixed, or enriched>

### Open Items

| Section | Item | What's Missing | Priority |
|---------|------|---------------|----------|
| <section> | <item> | <gap> | High / Medium / Low |

### Next Steps
- <what the next step will focus on, derived from Open Items>
```

This checkpoint enables **resume after interruption** — if the skill is re-invoked, it reads this section to skip completed work.

#### Verdict → Action Table

| Verdict | Action |
|---------|--------|
| `SPLIT` | Apply suggested split with sub-numbering |
| `VAGUE` / `UNCLEAR` / `WEAK` | Rewrite flagged content with reviewer's suggestion |
| `IMPLEMENTATION LEAK` | Rewrite at user level per abstraction-guard.md |
| `OVERLAPS UC-N` | Merge or clearly differentiate situations |
| `MISSING ACTOR` / `IMPLICIT ACTOR` | Add to Actors table + diagram |
| `PRIVILEGE SPLIT` | Split actor if actions require different privilege levels |
| `MISSING SYSTEM ACTOR` | Add system actor + assign to relevant UC |
| `INCOMPLETE ACTOR` | Fill missing Type or Role |
| `TYPE MISMATCH` / `ROLE MISMATCH` | Correct to match observed actions |
| `MISSING UC` / `MISSING ACTOR` in diagram | Update PlantUML diagram |
| `STALE RELATIONSHIP` | Update `<<include>>`/`<<extend>>` |

#### Step 7 Rules

- **Maximum:** 3 sub-steps (7a → 7b → 7c). Remaining issues → Open Questions with `[Unresolved after review]`.
- **Stop early:** If reviewer verdict is `PASS` AND enrichment added nothing new.

## Team Execution

For complex or large-scope inputs, use `TeamCreate` to parallelize work:

- **Research worker** — runs Step 3 research and targeted research (Step 7b) in background
- **Writer** — drafts and revises the document
- **Reviewer** — runs `usecase-reviewer` reviews

Use teams when the input suggests 10+ use cases or multiple research domains. For simpler inputs, sequential `Agent` calls are sufficient.

## Autonomous Decision Rules

Apply these consistently — no human interaction.

1. **Ambiguous topic** → pick the most specific interpretation. Record in Open Questions.
2. **Unclear actor role** → default to `viewer`. If actions suggest edit capability, use `editor`.
3. **Splitting boundary** → default to splitting. Smaller UCs are better.
4. **Vague situation** → construct a plausible concrete one. Record in Open Questions.
5. **Unclear relationships** → err toward dependency over reinforcement. Record reasoning.
6. **Output file exists** → read as target system. Preserve UC numbering, increment revision.
7. **New UC overlaps existing** → exclude. Record in Excluded Ideas.
8. **New UC outside scope** → exclude. Record in Excluded Ideas.
9. **Practical value borderline** → prefer exclusion over inclusion.
10. **Never** create GitHub Issues or set `status: final`.

## Final Output

Report to the user:
- Path to generated file
- Number of UCs generated (new + preserved if adding to target)
- UCs excluded and top reasons
- Similar systems researched and key common features
- Review steps completed
- Unresolved issues in Open Questions
- Final review verdict
