---
name: auto-usecase
description: "This skill should be used when the user wants to extract or batch-shape Use Cases from raw input — an existing codebase, an idea, brainstorm notes, or a file path — without interactive interview. Reverse-engineering an existing system into UCs is its primary job; running it on a fresh idea is a secondary mode. Triggers: 'reverse-engineer use cases', 'extract use cases from code', 'auto-generate use cases', 'auto-usecase', 'generate use cases from this idea', 'no interview needed just generate', 'run auto-usecase on'. Writes the result into <project-root>/a4/ per the spec-as-wiki+issues layout (per-UC files + context.md / actors.md / nfr.md). Not the autonomous twin of /a4:usecase — they serve different inputs; see references/skill-modes.md for the mode taxonomy."
argument-hint: <codebase path, idea, brainstorm text, or file path to extract use cases from>
allowed-tools: Read, Write, Agent, Glob, Grep, Bash, WebSearch, WebFetch, TaskCreate, TaskUpdate, TaskList
---

# Use Case Reverse-Engineer / Batch Generator

> **Authoring contract:** UC files this skill writes are governed by [`rules/a4-usecase-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-usecase-authoring.md); review items by [`rules/a4-review-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-review-authoring.md). This skill orchestrates the autonomous compose / review / explore loops; subagents follow those rules at write time.

Extract or batch-shape a complete spec-as-wiki+issues Use Case set from raw input — an existing codebase, an idea, brainstorm notes, description, or file path — without human interaction. Make all decisions independently, record open questions as review items, and refine until the set meets quality criteria.

This skill is **not** the autonomous twin of `/a4:usecase`. `/a4:usecase` is a Socratic interview that draws UCs out of a user who knows the problem; this skill is a reverse / batch entry for cases where the input is raw material rather than a person to interview against. See [`references/skill-modes.md`](${CLAUDE_PLUGIN_ROOT}/references/skill-modes.md) for the full mode taxonomy.

Generate use cases for: **$ARGUMENTS**

## Workspace

All artifacts live under `<project-root>/a4/` (resolve via `git rev-parse --show-toplevel`). Shape matches `usecase`:

```
a4/
  context.md, actors.md, domain.md, nfr.md   # wiki pages
  usecase/<id>-<slug>.md                       # one per UC
  review/<id>-<slug>.md                        # per-finding / per-gap / per-question
  research/                                    # similar-systems research, code-analysis reports, exploration reports
```

Create `a4/`, `a4/usecase/`, `a4/review/`, `a4/research/` if missing.

## Id Allocation

Every new UC / review item uses the shared allocator:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

Subagents (composer, reviser, reviewer, explorer) each call the allocator themselves at write time — do not batch ids in the main session.

## Shared References for Subagents

Subagents read these directly — don't pull their contents into the main session.

- `${CLAUDE_PLUGIN_ROOT}/skills/usecase/SKILL.md` — file layout, frontmatter schemas, wiki update protocol.
- `${CLAUDE_PLUGIN_ROOT}/skills/usecase/references/abstraction-guard.md` — banned implementation terms.
- `${CLAUDE_PLUGIN_ROOT}/skills/usecase/references/usecase-splitting.md` — splitting guide.
- `${CLAUDE_PLUGIN_ROOT}/skills/usecase/references/usecase-relationships.md` — relationship analysis.
- `${CLAUDE_PLUGIN_ROOT}/skills/usecase/references/review-report.md` — review-item schema emitted by reviewers.

Include these paths in each subagent prompt.

## Source Attribution on UCs

Each UC body records source attribution (`input`, `research — <systems>`, `code — <path>`, or `implicit`) as a one-line note inside the relevant required section (typically the start of `<situation>`). See [`references/source-attribution.md`](references/source-attribution.md) for the value definitions and the rationale for the requirement. The XSD does not declare a separate `<source>` tag — keeping attribution inline avoids a per-skill schema deviation.

## Resume Detection

Before starting, check the workspace for prior progress:

```bash
# Existing wiki pages
ls a4/context.md a4/actors.md a4/domain.md a4/nfr.md 2>/dev/null

# Existing UCs
ls a4/usecase/*.md 2>/dev/null | wc -l

# Existing research / code analysis / exploration reports
ls a4/research/*.md 2>/dev/null

# Open review items
grep -l 'status: open' a4/review/*.md 2>/dev/null
```

If UCs already exist, enter **expansion mode**: treat the existing set as the target system and extend it rather than rewrite. Preserve UC ids and content; allocate new ids for new UCs only. Open review items carry over and feed the inner quality loop.

## Flow

This skill runs two nested loops:

- **Outer growth loop** — compose → review → expand (via explorer / completeness) — up to 3 iterations.
- **Inner quality loop** — review → revise — up to 3 rounds per growth iteration.

### Step 1: Classify the Input

From `$ARGUMENTS`:

- **File path reference** — if the argument looks like a path, check whether it exists. `.md` → brainstorm / idea doc; source-code directories → code analysis target.
- **Inline content** — treat as raw idea.
- **Mixed** — inline idea + code path is common (e.g., "generate UCs for our current message-queue module at `src/mq/`").

Do **not** read input files in the main session. Pass their paths to subagents.

### Step 2: Research (parallel, optional)

Run Step 2a and 2b in parallel when both are needed. Wait for both to complete before composing.

#### Step 2a: Similar Systems Research

If no `a4/research/similar-systems-initial.md` exists, spawn a research subagent via `Agent(subagent_type: "general-purpose")`:

> Research similar systems for the following idea:
>
> <raw idea / path to brainstorm file>
>
> Goal: discover features and UCs that users of this type of system commonly need. Try 2–3 search queries. For each similar product (up to 5), list key user-facing features as "Actor does X to achieve Y". Identify candidates common across 3+ systems (high-value) vs unique to one (niche). Look for user reviews or feature requests indicating unmet needs.
>
> Write the report to `a4/research/similar-systems-initial.md` with frontmatter `{ label: similar-systems-initial, scope: similar-systems, source-input: <idea/file>, date: <today> }`. Include sections: Similar systems, High-value UC candidates, Niche UC candidates, User-requested features.

#### Step 2b: Code Analysis

Skip when no source-code path is referenced. When source is referenced and no `a4/research/code-analysis-initial.md` exists, spawn a `general-purpose` subagent:

> Analyze the codebase at `<paths>`.
>
> Goal: extract what the system currently does from the perspective of its users — features, actors, workflows. Identify main entry points, implemented user-facing features, visible actors (user roles, external systems, scheduled jobs), partial/stubbed features, data entities + CRUD operations.
>
> Write the report to `a4/research/code-analysis-initial.md` with frontmatter `{ label: code-analysis-initial, scope: code-analysis, paths: [<input paths>], date: <today> }`.

### Step 3: Compose + Refine Loop

All work in this step happens via subagents. The main session orchestrates.

#### Agents

- **Composer** — `Agent(subagent_type: "a4:usecase-composer")`. Writes / extends the workspace wiki pages and per-UC files.
- **Reviewer** — `Agent(subagent_type: "a4:usecase-reviewer")`. Emits per-finding review items.
- **Reviser** — `Agent(subagent_type: "a4:usecase-reviser")`. Walks open review items and applies fixes.
- **Explorer** — `Agent(subagent_type: "a4:usecase-explorer")`. Surfaces new-perspective UC candidates.

Pass each subagent the **absolute `a4/` path**, the shared reference paths listed above, and any iteration-specific inputs (e.g., which research reports to consume).

#### Step 3a: Compose

Spawn the composer:

```
Agent(subagent_type: "a4:usecase-composer", prompt: """
Workspace: <absolute path to a4/>
Mode: new | expansion                          # based on resume detection
User idea: <raw input from Step 1, or file path>
Research reports: <paths to a4/research/*.md (optional)>
Code analysis: <path to a4/research/code-analysis-initial.md, if it exists>
Shared refs: <list of reference file paths>
Growth iteration: <N>

For new mode: create context.md + actors.md + per-UC files from scratch.
For expansion mode: read existing UCs, preserve them, and write additional UC
files / wiki entries for new candidates.

Return a summary listing UC ids written, excluded candidates, and any open
questions emitted as kind: question review items.
""")
```

The composer:
- Writes `a4/context.md` with `type: context`, `updated`, an `<original-idea>` section quoting the input and a `<problem-framing>` section.
- Writes `a4/actors.md` with `type: actors`, `updated`, a `<roster>` section containing the Actors table.
- Allocates ids via `allocate_id.py` and writes one `a4/usecase/<id>-<slug>.md` per UC.
- Writes NFRs to `a4/nfr.md` (with `type: nfr` and a `<requirements>` section) if any are surfaced.
- Does **not** write `a4/domain.md`. Domain Model authorship belongs to `/a4:domain` (workspace authorship policy: [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md)). The final summary recommends running `/a4:domain` after auto-usecase finishes.
- Emits `kind: question` review items for unresolvable ambiguities (not merely autonomous defaults it has chosen — those are recorded inline within the UC body, e.g., as a paragraph under `<flow>` or `<dependencies>` flagged as a source attribution).
- Never rewrites previously confirmed UC files without cause.

#### Step 3b: Verify Write

The composer writes directly. Do **not** read the files back in the main session — section completeness is the composer's responsibility. Use the returned summary to confirm UC count.

#### Step 3c: Quality Loop (inner)

Repeat up to 3 rounds. Each round:

1. Spawn the reviewer per `usecase/references/review-report.md`. It writes per-finding review items into `a4/review/<id>-<slug>.md` (via `allocate_id.py`) and returns a summary:
   ```
   verdict: ALL_PASS | NEEDS_REVISION
   passed: M / N
   items_written: [ids]
   domain_model: OK | NEEDS_REVISION | NOT_YET_CREATED
   completeness: SUFFICIENT | INCOMPLETE
   ```
2. If `verdict == ALL_PASS`, exit the quality loop.
3. Otherwise, spawn the reviser:
   ```
   Agent(subagent_type: "a4:usecase-reviser", prompt: """
   Workspace: <a4/ path>
   Review item ids to address: <list from reviewer summary>
   Shared refs: <paths>

   For each review item (status: open, source: usecase-reviewer): read it, apply
   the Suggestion to the target UC / wiki page, flip status: resolved via
   transition_status.py (which appends the <log> entry), and append a
   <change-logs> bullet on each modified wiki page when wiki_impact is set.
   If a finding cannot be applied (e.g., ambiguous), leave status: open and
   capture the reason in conversation notes for the main session to surface.

   Return: revised UC ids, resolved review item ids, deferred review item ids.
   """)
   ```
4. Continue to the next round.

**Maximum:** 3 quality rounds per growth iteration. Remaining findings stay as `status: open` review items for human follow-up.

#### Step 3d: Growth Check (outer)

After the quality loop settles:

- `completeness: INCOMPLETE` → the reviewer's findings already include `kind: gap` review items with UC candidates. Feed them back into the composer for another growth iteration.
- `completeness: SUFFICIENT` → spawn the explorer to surface fresh perspectives:
  ```
  Agent(subagent_type: "a4:usecase-explorer", prompt: """
  Workspace: <a4/ path>
  Report path: a4/research/exploration-g<N>.md
  Prior explorations: <paths to a4/research/exploration-*.md if any>
  Shared refs: <paths>
  """)
  ```
  - If the explorer returns UC candidates, feed them back into the composer.
  - If it returns none, exit the outer loop.

**Maximum:** 3 growth iterations. Remaining unexplored perspectives stay as `kind: gap` review items.

### Step 4: Final Summary

Produce a short report to the user:

- Path to `a4/` workspace
- UCs in the final set (count and ids)
- UCs excluded (and why, per composer's record)
- Similar systems researched / common features found
- Growth iterations consumed / review rounds per iteration
- Review items: total / open / resolved / discarded
- Open questions (review items with `kind: question`) remaining

Do **not** advance any UC past `status: draft` — autonomous generation only produces drafts. Promotion to `ready` / `implementing` / `shipped` is always user-driven.

## Commit Points

All commit subjects follow [`commit-message-convention.md`](${CLAUDE_PLUGIN_ROOT}/references/commit-message-convention.md). Stage files under `a4/`. Timing:

- **After Step 2** — research / code-analysis reports, one commit:
  ```
  docs(a4): research similar systems for <topic>
  ```
  (ID-less: research reports under `a4/research/` carry no a4 workspace id.)
- **After Step 3a (each compose)** — UC files + wiki pages + any `kind: question` review items:
  ```
  #<uc-ids> [#<question-review-ids>] docs(a4): auto-usecase compose growth <N>
  ```
  Body bullet: `- UCs: <total> (<added> added)`.
- **After each quality round** — reviewer-emitted review items + reviser edits to UC files:
  ```
  #<revised-uc-ids> #<written-review-ids> docs(a4): auto-usecase growth <N> review <round>
  ```
  Body bullets: `- UCs: <total> (<revised> revised)` / `- Review items: <written>/<resolved>/<deferred>`.
- **After Step 3d exploration** — exploration report + any new `kind: gap` review items:
  ```
  #<gap-review-ids> docs(a4): auto-usecase exploration growth <N>
  ```
  (ID-less subject when zero gap items were emitted; the exploration report itself is under `a4/research/` and carries no id.)
  Body bullet: `- UC candidates: <count>`.
- **Final** — summary commit if anything remains unstaged. Subject form depends on what's staged; default to `chore(a4): auto-usecase wrap up` when only ambient updates remain.

## Cross-Stage Findings

This skill is **continue + review item** for any architecture / domain / NFR concern that surfaces during composition or review — UC drafts are independently meaningful, so emit review items targeting the upstream wiki and finish the autonomous run. See [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md) §Cross-stage feedback for the workspace policy. Domain Model itself is **out of scope** for this skill — domain extraction lives in `/a4:domain` and is recommended in the final summary when UCs are settled.

## Autonomous Decision Rules

Apply the rules in [`references/autonomous-decision-rules.md`](references/autonomous-decision-rules.md) consistently across composition, revision, and exclusion. No user interaction is permitted — autonomous output is always `status: draft` and promotion is user-driven.

## Non-Goals

- Do not write an aggregated `a4/<topic>.usecase.md` file. All output is per-UC + wiki pages.
- Do not maintain per-topic or per-slug file naming. `a4/` is a single workspace — filenames carry no topic.
- Do not write a `history.md` file. Per-UC `<log>` sections plus git history cover audit needs.
- Do not create GitHub Issues — `a4/` replaces that role.
