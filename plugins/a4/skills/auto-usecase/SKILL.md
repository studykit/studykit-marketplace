---
name: auto-usecase
description: "This skill should be used when the user wants to autonomously generate a complete Use Case set from an idea or brainstorm input without interactive interview. Triggers: 'auto-generate use cases', 'auto-usecase', 'generate use cases from this idea', 'create use case doc automatically', 'no interview needed just generate', 'run auto-usecase on'. Writes the result into <project-root>/a4/ per the spec-as-wiki+issues layout (per-UC files + context.md / actors.md / domain.md / nfr.md)."
argument-hint: <idea, brainstorm text, or file path to generate use cases from>
allowed-tools: Read, Write, Agent, Glob, Grep, Bash, WebSearch, WebFetch, TaskCreate, TaskUpdate, TaskList
---

# Autonomous Use Case Generator

Generate a complete spec-as-wiki+issues Use Case set from raw input — an idea, brainstorm notes, description, or file path — without human interaction. Make all decisions independently, record open questions as review items, and refine until the set meets quality criteria.

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

Each UC body includes a `## Source` section identifying where the UC came from:

- `input` — from the user's idea/brainstorm directly
- `research — <systems>` — from similar-systems research
- `code — <path>` — from code analysis of an existing implementation
- `implicit` — surfaced during reviewer/explorer completeness analysis

The `## Source` section is mandatory for every UC in auto-usecase output.

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
- Writes `a4/context.md` with `kind: context`, `updated`, Original Idea quote, Problem Framing.
- Writes `a4/actors.md` with `kind: actors`, `updated`, Actors table.
- Allocates ids via `allocate_id.py` and writes one `a4/usecase/<id>-<slug>.md` per UC.
- Writes NFRs to `a4/nfr.md` if any are surfaced.
- Does **not** write `a4/domain.md`. Domain Model authorship belongs to `/a4:domain` (workspace authorship policy: [`references/wiki-authorship.md`](../../../references/wiki-authorship.md)). The final summary recommends running `/a4:domain` after auto-usecase finishes.
- Emits `kind: question` review items for unresolvable ambiguities (not merely autonomous defaults it has chosen — those are recorded in the UC body's `## Source` section).
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
   the Suggestion to the target UC / wiki page, mark the item status: resolved,
   append a ## Log entry, and add wiki footnote markers when wiki_impact is set.
   If a finding cannot be applied (e.g., ambiguous), leave status: open with a
   ## Log entry explaining why.

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

All commits stage files under `a4/`. Timing:

- **After Step 2** — research / code-analysis reports, one commit.
- **After Step 3a (each compose)** — UC files + wiki pages + any `kind: question` review items, one commit per compose. Suggested title:
  ```
  usecase(auto): growth <N> — compose

  - UCs: <total> (<added> added)
  ```
- **After each quality round** — reviewer-emitted review items + reviser edits:
  ```
  usecase(auto): growth <N>, review <round>

  - UCs: <total> (<revised> revised)
  - Review items: <written>/<resolved>/<deferred>
  ```
- **After Step 3d exploration** — exploration report + any new `kind: gap` review items:
  ```
  usecase(auto): growth <N> — exploration

  - UC candidates: <count>
  ```
- **Final** — summary commit if anything remains unstaged.

## Cross-Stage Findings

This skill is **continue + review item** for any architecture / domain / NFR concern that surfaces during composition or review — UC drafts are independently meaningful, so emit review items targeting the upstream wiki and finish the autonomous run. See [`references/wiki-authorship.md`](../../../references/wiki-authorship.md) §Cross-stage feedback for the workspace policy. Domain Model itself is **out of scope** for this skill — domain extraction lives in `/a4:domain` and is recommended in the final summary when UCs are settled.

## Autonomous Decision Rules

Apply these consistently — no user interaction:

1. Ambiguous topic → pick the most specific interpretation. Record the interpretation in `context.md`'s Problem Framing and emit a `kind: question` review item so a human can confirm later.
2. Unclear actor role → default to `viewer`. Upgrade to `editor` when actions imply edit capability.
3. Splitting boundary → prefer splitting. Smaller UCs are better.
4. Vague situation → construct a plausible concrete one. Emit a `kind: question` review item.
5. Unclear relationship → prefer `depends_on` over `related`. Note the reasoning in the UC's `## Source` section.
6. New UC overlaps existing → exclude. Record in the exclusion log (Step 3a composer output) and do not emit a file.
7. New UC outside context → exclude. Record in the exclusion log.
8. Practical value borderline → prefer exclusion over inclusion.
9. Never set `status: final` on any wiki or UC; autonomous output is always `status: draft`.

## Non-Goals

- Do not write an aggregated `a4/<topic>.usecase.md` file. All output is per-UC + wiki pages.
- Do not maintain per-topic or per-slug file naming. `a4/` is a single workspace — filenames carry no topic.
- Do not write a `history.md` file. Per-UC `## Log` sections plus git history cover audit needs.
- Do not create GitHub Issues — `a4/` replaces that role.
