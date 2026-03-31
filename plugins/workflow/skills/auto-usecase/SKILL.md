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

Every Use Case follows the structure defined in `output-template.md`. In autonomous mode, the **Source** field is mandatory for every UC:

- `input` — derived from the user's idea or brainstorm
- `research — <which systems>` — discovered from similar systems research
- `implicit` — discovered during analysis as a prerequisite or complement

## Resume Detection

Before starting, check for existing progress:

1. **Research report:** Check for `A4/co-think/<topic-slug>.usecase.research-initial*.md`:
   - `*.research-initial.consumed.md` exists → research already reflected in document, skip Step 3.
   - `*.research-initial.md` exists (without consumed) → research completed but not yet reflected, skip Step 3 and pass to composer agent in Step 4.
   - Neither exists → run Step 3.
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

Check for existing research results per Resume Detection. If research is needed:

Launch a research subagent in the background via `TeamCreate`. **Do not wait** — proceed to Step 4 while research runs.

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

Save the full research results per `references/research-report.md` (label: `initial`).

### Step 4: Analyze and Generate Use Cases

If Step 3 launched a research subagent, wait for it to complete before invoking the composer agent.

Invoke the `usecase-composer` agent with:
- **User idea** — the input from Step 1
- **Research results** — file path to research report from Step 3 (or existing report from Resume Detection)
- **Target system** — file path to existing `.usecase.md` from Step 2 (if applicable)

The composer agent handles: problem space definition, actor discovery, UC extraction, system completeness analysis, splitting, relationship analysis, fitness check, PlantUML diagram, abstraction guard, and initial Session Checkpoint.

After the composer agent returns, rename the research file to mark it as consumed:
`<topic-slug>.usecase.research-initial.md` → `<topic-slug>.usecase.research-initial.consumed.md`

### Step 5: Write the Document

Assemble the composer agent's output into the final document following `output-template.md` using **auto-usecase** rules:
- Include: Original Idea, Context, Similar Systems Research, Actors, Use Case Diagram, Use Cases, Use Case Relationships, Open Questions, Session Checkpoint
- Include conditionally: Excluded Ideas (if any), Change Log (revision > 0 only)
- Omit: Interview Transcript

Frontmatter: `status: draft`, `revision: 0` (or increment), current date for `created`/`revised`, `tags: []`.

### Step 6: Review and Revision Loop

Repeat until all UCs pass and no actor issues remain, or the maximum number of rounds is reached:

1. Invoke `usecase-reviewer` agent on the output file. Save the review report per `references/review-report.md` (label: `review-1`, `review-2`, `review-3`).
2. If all UC verdicts are `PASS` and Actors Review has no issues, proceed to commit and exit the loop.
3. Otherwise:
   a. Pass the review report and document to the `usecase-reviser` agent to apply fixes.
   b. Write the updated document with Session Checkpoint.
   c. Commit to git (see Commit below).
   d. Continue to next round.

**Maximum:** 3 review rounds. Remaining issues after 3 rounds → Open Questions with `[Unresolved after review]`.

### Commit

After each review round, stage all files under `A4/co-think/<topic-slug>.*` and commit:

```
usecase(<topic-slug>): revision N — review <round>

- UCs: <total count> (<added> added, <modified> revised)
- UCs passed: <M> / <N>
- Open items: <count>
```

## Autonomous Decision Rules

Apply these consistently — no human interaction.

1. **Output file exists** → read as target system. Preserve UC numbering, increment revision.
2. **Never** create GitHub Issues or set `status: final`.

## Final Output

Report to the user:
- Path to generated file
- Number of UCs generated (new + preserved if adding to target)
- UCs excluded and top reasons
- Similar systems researched and key common features
- Review rounds completed
- Unresolved issues in Open Questions
- UCs passed (M / N)
