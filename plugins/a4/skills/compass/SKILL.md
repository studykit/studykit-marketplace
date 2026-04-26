---
name: compass
description: "This skill should be used when the user doesn't know which a4 skill to use, is stuck mid-pipeline, or needs help deciding the next step. Triggers: 'what should I do next', 'where do I go from here', 'which skill should I use', 'help me navigate', 'I'm stuck', 'next step', 'continue the pipeline', 'compass', or when the user invokes the a4 plugin without a specific skill name."
argument-hint: <issue id, path (e.g. usecase/3-search-history), wiki basename, or free-text description>
allowed-tools: Read, Write, Glob, Grep, Bash, Skill
---

# Pipeline Navigator

Helps users find the right skill or diagnose the next step in an ongoing pipeline.

Argument: **$ARGUMENTS**

## Inter-skill entry

Compass is also callable as a fallback router from other a4 skills. When another skill's preconditions are unmet (e.g., `/a4:run` invoked without `bootstrap.md` present — bootstrap is the single source of truth for Launch & Verify), it halts and invokes compass via the Skill tool, passing the calling skill name and a short workspace state diagnosis as the argument (e.g., `from=run; missing=bootstrap.md`).

Compass treats this as a regular Step 1 entry — the diagnosis text routes to Step 3 (Gap Diagnosis), not Step 2 (Fresh Start), since the workspace already has some state by definition. If the calling skill provided enough context to determine the intent, compass skips the catalog presentation in Step 2 and the brownfield "What are you trying to do?" prompt described there.

## Step 0: Detect project root

### 0.1 Resolve workspace location

```bash
ROOT=$(git rev-parse --show-toplevel)
```

If not inside a git repo, abort this step with a clear message and skip to Step 1.

If `$ROOT/a4/` does not exist (no workspace yet), proceed to Step 1.

### 0.2 Optional: surface existing INDEX dashboard

`a4/INDEX.md` is a precomputed dashboard regenerated only by `/a4:index` — compass does **not** refresh it. If the user invoked compass with no argument and `a4/INDEX.md` exists, read it and show the **Stage progress** and **Drift alerts** sections before entering Step 1 — these two answer "where is the workspace at" faster than any other section. Note to the user that the dashboard may be stale relative to recent edits and that `/a4:index` regenerates it. Otherwise proceed silently to Step 1.

---

## Step 1: Detect Context

Determine the user's situation and route to Step 2 (Fresh Start) or Step 3 (Gap Diagnosis).

### 1.1 Resolve the argument

- **Specific target** — integer id (`3`, `#3`), folder-qualified path (`usecase/3-search-history`, `review/6-...`), wiki basename (`context`, `domain`, `architecture`, `actors`, `nfr`, `roadmap`, `bootstrap`), or a full `a4/…` path. Resolve to the underlying `a4/` file via `Glob`. If the id or path resolves uniquely, carry the target into Step 3. If the target lives under `a4/archive/`, inform the user it is archived and ask whether to restore (`git mv` back into its original folder) before continuing.
- **Free-text description** (e.g., "I want to build a chat app") → Step 2 (Fresh Start). The user is starting something new.
- **Empty argument** — route by workspace state:
  - `a4/` absent or empty → Step 2 (Fresh Start).
  - `a4/` has wiki pages or issues → Step 3 (workspace-wide diagnosis; no targeted item).

### 1.2 Note on workspace state

Compass reads workspace state directly from per-item frontmatter under `a4/` in Step 3 (Glob + targeted reads). `a4/INDEX.md`, if present, is a precomputed dashboard regenerated only by `/a4:index`; treat it as a stale view, not source of truth. Do not aggregate state here — defer the scan to Step 3.

---

## Step 2: Fresh Start

The workspace is empty or the user described a vague intent.

### 2.0 Brownfield detection and pipeline-shape choice

Before showing the catalog, detect whether the project has implementation code outside `a4/` and, if so, ask the user to pick one of three pipeline shapes (Reverse / Minimal / Full). The full detection signatures, the exact one-question prompt, the No-shape fall-through rule, and the per-choice routing (including which Skill invocation to make for (a)/(b)/(c)) are in [`references/brownfield-routing.md`](references/brownfield-routing.md). Read that file before running this step.

When no implementation code is detected, skip 2.0 and go straight to the catalog.

### 2.1 Catalog

Ask: **"What are you trying to do?"** and present the four-group catalog (Ideation / Pipeline interactive / Pipeline autonomous / Standalone) from [`references/catalog.md`](references/catalog.md). Read that file and show its tables verbatim — it is the single source of truth for compass routing.

Based on the user's answer, invoke the chosen skill via the Skill tool:
```
Skill({ skill: "a4:<skill-name>", args: "<user's topic or file path>" })
```

---

## Step 3: Gap Diagnosis

The workspace has existing wiki pages or issues. Detect drift, locate the gap, and recommend the next skill.

### 3.1 Detect drift

Before reading state, surface accumulated wiki↔issue drift from since the last session:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/drift_detector.py" "$ROOT/a4"
```

The detector writes one review item per new finding into `a4/review/`, deduplicated against existing open / in-progress / discarded `source: drift-detector` items. Any new items are surfaced in Step 3.3 below alongside pre-existing open drift. `a4/INDEX.md` is **not** refreshed here — the new review items are visible via Step 3.2's frontmatter scans, and the dashboard updates next time `/a4:index` runs.

### 3.2 Read workspace state

Scan per-item frontmatter directly under `a4/` (Glob + Read). The frontmatter is the source of truth; do not rely on `a4/INDEX.md` since it may be stale.

- **Wiki pages present** and their `updated:` dates — read frontmatter from `a4/{context,domain,architecture,actors,nfr,roadmap,bootstrap}.md`.
- **Issue counts** per folder × status — glob `a4/{usecase,task,review,decision,idea}/*.md` and aggregate by `status:`.
- **Drift alerts** — open / in-progress `review/*.md` with `source: drift-detector`, grouped by `priority:`.
- **Milestone progress** — group tasks by `milestone:`, count resolved vs open.

Keep the scan to a single pass and budget for it accordingly. If Step 1.1 resolved a **specific target**, additionally read that file's full body and frontmatter — it drives the Step 3.3 recommendation more than aggregate state does.

### 3.3 Diagnose the gap layer

Apply the layered trace defined in [`references/gap-diagnosis.md`](references/gap-diagnosis.md): detect the workspace shape (3.3.0), then walk Layer 0 → 6 against the state collected in 3.2 and stop at the first layer with actionable work. For a targeted Step 1.1 argument, focus the trace on layers upstream of the target (e.g., a blocked task points back to its `depends_on` predecessor). Carry the detected shape into Step 3.4 so the user sees the assumption.

### 3.4 Present diagnosis

Report in this format:

```
## Workspace Status

Shape: <Full | Reverse-then-forward | Reverse-only | Minimal | No shape>

| Layer | State |
|-------|-------|
| Wiki pages | <N of 7 present, list missing> |
| Open issues | <usecase: N draft / M implementing / …; task: …; review: …> |
| Drift alerts | <N open (H high, M medium, L low)> |
| Milestones | <milestone-name: X/Y complete> (only for active milestones) |

## Diagnosis

<1-3 sentences on where the gap is and why>

## Recommendation

→ **/a4:<skill> [iterate]**: <what to do and why>
```

Wait for the user's confirmation, then invoke the recommended skill:

```
Skill({ skill: "a4:<skill-name>", args: "<target ref or 'iterate'>" })
```

`<target ref>` is the specific issue or wiki page the iteration should open (e.g., `review/6-missing-validation`, `usecase/3-search-history`, `architecture`). Iteration skills accept path-like arguments and resolve them internally. For generic resumes, `iterate` alone is sufficient.

If the user disagrees with the recommendation, discuss alternatives and let them choose.

---

### 3.5 Archive suggestion (targeted items only)

If Step 1.1 resolved a specific target **and** that item's `status` is a terminal state (`done` / `complete` / `resolved` / `final`), after presenting the diagnosis offer to archive it:

> "Item `<folder>/<id>-<slug>` is closed. Move to `a4/archive/`?"

Do **not** move automatically. On user confirmation:

```bash
git mv a4/<folder>/<id>-<slug>.md a4/archive/
git commit -m "docs(a4): archive <folder>/<id>-<slug>"
```

Workspace-wide completion is rare and user-driven — compass does not auto-suggest batch archive. Folder location is the archived flag; no frontmatter change is needed.
