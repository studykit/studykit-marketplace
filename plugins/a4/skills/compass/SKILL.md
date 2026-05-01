---
name: compass
description: "Explicit-invocation only via `/a4:compass`. This skill should be used when the user doesn't know which a4 skill to use, is stuck mid-pipeline, needs help deciding the next step, or wants a recommendation rather than a raw report. Triggers: 'what should I do next', 'where do I go from here', 'which skill should I use', 'help me navigate', 'I'm stuck', 'next step', 'continue the pipeline', 'diagnose', 'pipeline status', 'compass'. Runs the drift detector (writes new review items to disk) and produces a layered diagnosis + a single recommended next skill to invoke (and may invoke it via the Skill tool). ROUTING: for a plain workspace snapshot or a single pre-defined section view (drift list, active tasks, etc.) without a recommendation, delegate to the `workspace-assistant` agent (snapshot mode). For per-item search by frontmatter (status / kind / references / labels / custom field), use `/a4:find` instead."
argument-hint: <issue id, path (e.g. usecase/3-search-history), wiki basename, or free-text description>
disable-model-invocation: true
allowed-tools: Read, Write, Glob, Grep, Bash, Skill
---

# Pipeline Navigator

Helps users find the right skill or diagnose the next step in an ongoing pipeline.

Argument: **$ARGUMENTS**

## Inter-skill entry

Other a4 skills call compass as a fallback router when their preconditions are unmet (e.g., `/a4:run` invoked without `bootstrap.md` present). The calling skill halts and invokes compass via the Skill tool, passing the calling skill name and a short workspace state diagnosis as the argument (e.g., `from=run; missing=bootstrap.md`).

Compass treats this as a regular Step 1 entry — the diagnosis text routes to Step 3 (Gap Diagnosis), not Step 2 (Fresh Start). If the calling skill provided enough context to determine the intent, compass skips the catalog presentation in Step 2 and the brownfield "What are you trying to do?" prompt described there.

## Step 0: Detect project root

```bash
ROOT=$(git rev-parse --show-toplevel)
```

If not inside a git repo, abort with a clear message and skip to Step 1.

If `$ROOT/a4/` does not exist (no workspace yet), proceed to Step 1.

---

## Step 1: Detect Context

Determine the user's situation and route to Step 2 (Fresh Start) or Step 3 (Gap Diagnosis).

### 1.1 Resolve the argument

- **Specific target** — integer id (`3`, `#3`), folder-qualified path (`usecase/3-search-history`, `review/6-...`), wiki basename (`context`, `domain`, `architecture`, `actors`, `nfr`, `bootstrap`), or a full `a4/…` path. Resolve to the underlying `a4/` file via `Glob`. If the id or path resolves uniquely, carry the target into Step 3. If the target lives under `a4/archive/`, inform the user it is archived and ask whether to restore (`git mv` back into its original folder) before continuing.
- **Free-text description** (e.g., "I want to build a chat app") → Step 2 (Fresh Start). The user is starting something new.
- **Empty argument** — route by workspace state:
  - `a4/` absent or empty → Step 2 (Fresh Start).
  - `a4/` has wiki pages or issues → Step 3 (workspace-wide diagnosis; no targeted item).

### 1.2 Note on workspace state

Compass reads a fresh workspace-state snapshot via `scripts/workspace_state.py` in Step 3.2 — the same script the `workspace-assistant` agent uses for snapshot mode. Do not pre-scan or aggregate state here; defer to Step 3.

---

## Step 2: Fresh Start

The workspace is empty or the user described a vague intent.

### 2.0 Brownfield detection and pipeline-shape choice

Before showing the catalog, detect whether the project has implementation code outside `a4/` and, if so, ask the user to pick one of three pipeline shapes (Reverse / Minimal / Full). The full detection signatures, the exact one-question prompt, the No-shape fall-through rule, and the per-choice routing live in `references/brownfield-routing.md`. Read that file before running this step.

When no implementation code is detected, skip 2.0 and go straight to the catalog.

### 2.1 Catalog

Ask: **"What are you trying to do?"** and present the four-group catalog (Ideation / Pipeline interactive / Pipeline autonomous / Standalone) from `references/catalog.md`. Read that file and show its tables verbatim — it is the single source of truth for compass routing.

Based on the user's answer, invoke the chosen skill via the Skill tool:

```
Skill({ skill: "a4:<skill-name>", args: "<user's topic or file path>" })
```

---

## Step 3: Gap Diagnosis

Procedure (3.1 detect drift → 3.2 read workspace state → 3.3 diagnose layer → 3.4 present → 3.5 archive suggestion): `references/gap-diagnosis-flow.md`.
