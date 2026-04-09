---
name: auto-usecase
description: "This skill should be used when the user wants to autonomously generate a complete Use Case document from an idea or brainstorm input without interactive interview. Triggers: 'auto-generate use cases', 'auto-usecase', 'generate use cases from this idea', 'create use case doc automatically', 'no interview needed just generate', 'run auto-usecase on', or when the user provides an idea/brainstorm and wants a .usecase.md file produced without back-and-forth dialogue."
argument-hint: <idea, brainstorm text, or file path to generate use cases from>
allowed-tools: Read, Write, Agent, Glob, Grep, Bash, WebSearch, WebFetch, TaskCreate, TaskUpdate, TaskList
---

# Autonomous Use Case Generator

Generate a complete `.usecase.md` file from raw input — an idea, brainstorm notes, a description, or a file path — without human interaction. Make all decisions independently, record assumptions in Open Questions, and refine until the document meets quality standards.

Generate use cases for: **$ARGUMENTS**

## Shared References

These files define the rules and format for use case documents. **Do not read them in the main session.** Pass the paths to agents — each subagent reads them per invocation.

- `${CLAUDE_SKILL_DIR}/../think-usecase/references/output-template.md` — exact output format (use **auto-usecase** sections)
- `${CLAUDE_SKILL_DIR}/../think-usecase/references/usecase-splitting.md` — when and how to split oversized use cases
- `${CLAUDE_SKILL_DIR}/../think-usecase/references/usecase-relationships.md` — dependency and reinforcement analysis
- `${CLAUDE_SKILL_DIR}/../think-usecase/references/abstraction-guard.md` — banned implementation terms and conversion rules
- `${CLAUDE_SKILL_DIR}/../think-usecase/references/review-report.md` — how to persist reviewer reports
- `${CLAUDE_SKILL_DIR}/../think-usecase/references/research-report.md` — how to persist research results
- `${CLAUDE_SKILL_DIR}/../think-usecase/references/exploration-report.md` — how to persist exploration results

If `${CLAUDE_SKILL_DIR}` is not resolved, use `${CLAUDE_PLUGIN_ROOT}/skills/think-usecase/references/` instead.

## Use Case Format

Every Use Case follows the structure defined in `output-template.md`. In autonomous mode, the **Source** field is mandatory for every UC:

- `input` — derived from the user's idea or brainstorm
- `research — <which systems>` — discovered from similar systems research
- `code — <what was found>` — discovered from code analysis of existing implementation
- `implicit` — discovered during analysis as a prerequisite or complement

## Resume Detection

Before starting, check for existing progress. If the output file (`A4/<topic-slug>.usecase.md`) exists, extract its `reflected_files` list via:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/read_frontmatter.py A4/<topic-slug>.usecase.md reflected_files
```

Do not read the output file itself. A file listed in `reflected_files` has already been reflected — do not read it and do not pass it to agents.

1. **Research report:** Check for `A4/<topic-slug>.usecase.research-initial.md`:
   - File exists and listed in `reflected_files` → already reflected, skip Step 2a.
   - File exists but not in `reflected_files` → completed but not yet reflected, pass to composer in Step 3.
   - File does not exist → run Step 2a.
2. **Code analysis report:** Check for `A4/<topic-slug>.usecase.code-analysis.md`:
   - File exists and listed in `reflected_files` → already reflected, skip Step 2b.
   - File exists but not in `reflected_files` → completed but not yet reflected, pass to composer in Step 3.
   - File does not exist and input references source code → run Step 2b.
   - File does not exist and no source code referenced → skip Step 2b.
3. **Last completed step:** Extract `last_step` from frontmatter via `read_frontmatter.py`:
   - If set → **resume from the next step** — do not repeat completed work.
   - If empty or absent → no prior progress, start from Step 1.
4. **Review reports:** Check existing `A4/<topic-slug>.usecase.review-*.md` files against `reflected_files`. Only pass unreflected review reports to agents.
5. **Exploration reports:** Check existing `A4/<topic-slug>.usecase.exploration-*.md` files against `reflected_files`. Only pass unreflected exploration reports to agents.
   - File exists but not in `reflected_files` → exploration done but not yet reflected, use existing results in next compose iteration.

This allows recovery from API limits, context window exhaustion, or other interruptions without starting over.

## Step-by-Step Process

### Step 1: Understand the Input

The input has two components:

1. **New idea** (required) — the feature, idea, or brainstorm to turn into use cases. Can be a file path, inline content, or a vague description.
2. **Target system** (optional) — an existing `.usecase.md` file, topic slug, or partial name. If absent, create from scratch.

Determine the **topic slug** (lowercase, hyphen-separated, 2–5 words). Output path: `A4/<topic-slug>.usecase.md`.

**Do not read any input files, source code, or target system files in the main session.** Only identify paths and pass them to agents in subsequent steps.

### Step 2: Research and Analysis

Run Step 2a and 2b in parallel when both are needed. Wait for all to complete before proceeding to Step 3.

#### Step 2a: Research Similar Systems

Check for existing research results per Resume Detection. If research is needed:

Launch a research subagent via `Agent`. Prompt the subagent:

> Research similar systems to "$ARGUMENTS".
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

#### Step 2b: Analyze Source Code

Skip if the input does not reference source code. Check for existing results per Resume Detection. If analysis is needed:

Launch a code analysis subagent via `Agent` (general-purpose). The subagent must both analyze the code and write the results file. Prompt the subagent:

> Analyze the codebase at `<paths from Step 1>`.
>
> **Goal:** Extract what the system currently does from the perspective of its users — features, actors, and workflows already implemented.
>
> 1. Identify the overall architecture and main entry points.
> 2. List implemented user-facing features as "Actor does X to achieve Y".
> 3. Identify actors (user roles, external systems, scheduled jobs) visible in the code.
> 4. Note any partially implemented or stubbed features.
> 5. Identify data entities and their CRUD operations.
>
> Write the results to `A4/<topic-slug>.usecase.code-analysis.md` with frontmatter `label: code-analysis`, `topic: <topic-slug>`.

### Step 3: Compose and Refine Loop

This step runs an outer **growth loop** (compose → review → expand) and an inner **quality loop** (review → revise).

#### Agents

Each step launches a fresh subagent. Context is passed entirely through file paths — the working file, history file, research/code analysis reports, review/exploration reports. File-based state (`reflected_files`, history file) ensures continuity across invocations.

- **Composer:** `Agent(subagent_type: "usecase-composer")` — composes UC documents
- **Reviewer:** `Agent(subagent_type: "usecase-reviewer")` — reviews UC quality and system completeness
- **Reviser:** `Agent(subagent_type: "usecase-reviser")` — applies review fixes
- **Explorer:** `Agent(subagent_type: "usecase-explorer")` — explores new perspectives for UC candidates

Include the shared reference file paths in each subagent prompt.

#### Step 3a: Compose

Launch a `usecase-composer` subagent with:
- **Output path** — `A4/<topic-slug>.usecase.md`
- **User idea** — the input from Step 1 (first iteration) or UC Candidates from reviewer/explorer (subsequent iterations)
- **Research results** — file path to research report from Step 2a (first iteration only)
- **Code analysis** — file path to code analysis report from Step 2b (first iteration only, if exists)
- **Target system** — file path to existing `.usecase.md` from Step 1, or the current document (subsequent iterations)

**Do not read research results, code analysis reports, or input files in the main session.** Pass file paths only — the subagent reads them directly. This avoids duplicating content into the main session context.

#### Step 3b: Verify and Commit

The composer subagent writes the document directly. Verify the file exists at the output path (do not read it). Section completeness is the composer's responsibility.

The composer responds with a summary including UC count. Use that for the commit message:
```
usecase(<topic-slug>): growth <iteration> — compose

- UCs: <total count> (<added> added)
```

#### Step 3c: Quality Loop (inner)

Repeat until all UCs pass and no actor issues remain, or the maximum is reached:

1. Launch a `usecase-reviewer` subagent with the output file and report path per `references/review-report.md` (label: `review-g<iteration>-q<round>`). If previous review reports exist from earlier rounds, include their paths so the reviewer can check whether prior findings have been addressed. The reviewer responds with a summary: verdict (`ALL_PASS` or `NEEDS_REVISION`), pass count, total count, system completeness (`INCOMPLETE` or `SUFFICIENT`), and UC candidates if any.
2. If verdict is `ALL_PASS`:
   a. Commit review report:
      ```
      usecase(<topic-slug>): growth <iteration>, review <round> — PASS

      - UCs passed: <N> / <N>
      ```
   b. Exit quality loop.
3. Otherwise (`NEEDS_REVISION`):
   a. **Always** launch a `usecase-reviser` subagent — do not apply fixes directly in the main session. Pass the review report, document path, and history file path (`<topic-slug>.usecase.history.md`). The reviser responds with a summary including UC count and changes applied. The reviser appends a new entry (`Last Completed`, `Change Log`) to the history file and updates Open Items + Next Steps in the working file.
   b. Commit review report + revised document (use counts from reviser's summary):
      ```
      usecase(<topic-slug>): growth <iteration>, review <round>

      - UCs: <total count> (<modified> revised)
      - UCs passed: <M> / <N>
      ```
   c. Continue to next round.

**Maximum:** 3 quality rounds per growth iteration. Remaining quality issues → Open Questions with `[Unresolved after review]`.

#### Step 3d: Growth Check (outer)

After the quality loop passes (or reaches maximum), determine whether to expand the system:

1. **System Completeness** — use the reviewer's returned summary (from Step 3c):
   - **INCOMPLETE** with UC Candidates → pass the UC Candidates back to Step 3a.
   - **SUFFICIENT** → proceed to Perspective Exploration.

2. **Perspective Exploration** — launch a `usecase-explorer` subagent with the current document path and report path per `references/exploration-report.md` (label: `exploration-<iteration>`, e.g., `exploration-1`). If previous exploration reports exist, include their paths so the explorer avoids duplicating candidates. Commit after explorer:
   ```
   usecase(<topic-slug>): growth <iteration> — exploration

   - Perspectives explored: <count>
   - UC candidates found: <count>
   ```
   - UC Candidates found → pass the UC Candidates and current document back to Step 3a.
   - No candidates → exit the growth loop, proceed to Final Output.

Completeness gaps are addressed first. Perspective exploration only runs when the system is structurally sufficient.

**Maximum:** 3 growth iterations. Remaining gaps or unexplored perspectives → Open Questions with `[Unresolved after growth loop]`.

### Commit

All commits stage files under `A4/<topic-slug>.*`. Commit timing:
- **After compose** (Step 3b) — UC document created/updated
- **After each quality round** (Step 3c) — review report (+ revised document if NEEDS REVISION)
- **After exploration** (Step 3d) — exploration report

## Autonomous Decision Rules

Apply these consistently — no human interaction.

1. **Output file exists** → pass as target system path to the composer. The composer reads and preserves UC numbering and increments revision.
2. **Never** create GitHub Issues or set `status: final`.

## Final Output

Report to the user:
- Path to generated file
- Number of UCs generated (new + preserved if adding to target)
- UCs excluded and top reasons
- Similar systems researched and key common features
- Growth iterations and review rounds completed
- System completeness status
- Unresolved issues in Open Questions
- UCs passed (M / N)
