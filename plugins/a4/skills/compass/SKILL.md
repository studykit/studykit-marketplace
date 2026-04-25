---
name: compass
description: "This skill should be used when the user doesn't know which a4 skill to use, is stuck mid-pipeline, or needs help deciding the next step. Also maintains `a4/INDEX.md` as a workspace dashboard, refreshed on every invocation. Triggers: 'what should I do next', 'where do I go from here', 'which skill should I use', 'help me navigate', 'I'm stuck', 'next step', 'continue the pipeline', 'compass', or when the user invokes the a4 plugin without a specific skill name."
argument-hint: <issue id, path (e.g. usecase/3-search-history), wiki basename, or free-text description>
allowed-tools: Read, Write, Glob, Grep, Bash, Skill
---

# Pipeline Navigator

Helps users find the right skill or diagnose the next step in an ongoing pipeline. Also maintains a workspace dashboard at `a4/INDEX.md`.

Argument: **$ARGUMENTS**

## Step 0: Refresh INDEX

Before any other step, regenerate `a4/INDEX.md`. This is the workspace dashboard — a **view** of wiki-page state, stage progress, open issues, drift alerts, milestone progress, recent activity, and open sparks. The per-item frontmatter under `a4/` is the source of truth; INDEX is derived.

### 0.1 Detect project root and a4/ presence

```bash
ROOT=$(git rev-parse --show-toplevel)
```

If not inside a git repo, abort this step with a clear message and skip to Step 1.

If `$ROOT/a4/` does not exist (no workspace yet), skip INDEX regeneration and proceed to Step 1.

### 0.2 Run the refresher script

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/index_refresh.py" "$ROOT/a4"
```

The script reads frontmatter from `a4/{context,domain,architecture,actors,nfr,plan,bootstrap}.md` (wiki pages) and `a4/{usecase,task,review,decision,idea}/*.md` (issues) plus `a4/spark/*.md`, then fully overwrites `a4/INDEX.md`. Each section contains an Obsidian dataview query block (fixed literal text) and a static markdown fallback computed from current state, wrapped in `<!-- static-fallback-start: <id> -->` / `<!-- static-fallback-end: <id> -->` markers. Stage progress is static-only because it mixes wiki-page presence with cross-folder issue aggregates.

compass does **not** commit INDEX.md automatically — it is left in the working tree for the user or the next session-closing to pick up.

### 0.3 Continue

If the user invoked compass with no argument, read `a4/INDEX.md` and show the **Stage progress** and **Drift alerts** sections to the user before entering Step 1 — these two answer "where is the workspace at" faster than any other section. Otherwise proceed silently to Step 1.

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

Workspace state — wiki page presence, per-folder issue counts, open drift alerts, milestone progress — was already gathered by `index_refresh.py` in Step 0. Step 3 reads from the regenerated `a4/INDEX.md` and supplements with targeted frontmatter reads. Do not re-scan here.

---

## Step 2: Fresh Start

The workspace is empty or the user described a vague intent. Present the skill catalog and help them pick an entry point.

Ask: **"What are you trying to do?"** and show the options:

### Ideation
| Skill | What it does |
|-------|-------------|
| `spark-brainstorm` | Generate ideas with structured creative techniques |
| `research` | Investigate options or a topic; produces a portable artifact at `./research/<slug>.md` (outside `a4/`) for reference |
| `research-review` | Review a research artifact at `./research/<slug>.md` for source quality, option balance, bias, and neutrality |
| `decision` | Record a decision reached through conversation as `a4/decision/<id>-<slug>.md`, cite related research, nudge affected wiki pages |

### Pipeline (interactive)
| Skill | What it does |
|-------|-------------|
| `usecase` | Shape a vague idea into concrete Use Cases + Domain Model through dialogue |
| `arch` | Design architecture — tech stack, components, interfaces, test strategy |
| `roadmap` | Author the implementation roadmap and per-task files |
| `task` | Author a single task (feature / spike / bug) — UC-derived or ADR-justified |
| `run` | Run the agent loop — implement and test until all pass |

### Pipeline (autonomous)
| Skill | What it does |
|-------|-------------|
| `auto-usecase` | Auto-generate use cases without interview |
| `auto-bootstrap` | Set up project structure, dependencies, build, and test infrastructure |

### Standalone
| Skill | What it does |
|-------|-------------|
| `web-design-mock` | Create HTML/CSS mockups and prototypes |

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

The detector writes one review item per new finding into `a4/review/`, deduplicated against existing open / in-progress / discarded `source: drift-detector` items. Any new items are surfaced in Step 3.3 below alongside pre-existing open drift.

If the detector wrote new items, regenerate `a4/INDEX.md` so the Drift alerts section reflects them:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/index_refresh.py" "$ROOT/a4"
```

### 3.2 Read workspace state

Pull state from the regenerated `a4/INDEX.md` (Step 0 + possible Step 3.1 rerun):

- **Wiki pages present** and their `updated:` dates (from INDEX's Wiki pages section).
- **Issue counts** per folder × status (from INDEX's Open issues and Stage progress sections).
- **Drift alerts** — open / in-progress `review/*.md` with `source: drift-detector`, grouped by priority.
- **Milestone progress** — resolved / open per active milestone.

If Step 1.1 resolved a **specific target**, additionally read that file's full body and frontmatter — it drives the Step 3.3 recommendation more than aggregate state does.

### 3.3 Diagnose the gap layer

Trace from foundation to execution. Stop at the first layer that has actionable work. For a targeted Step 1.1 argument, focus the trace on layers upstream of the target (e.g., a blocked task points back to its `depends_on` predecessor).

**Layer 0 — Workspace foundation.** Does the workspace have any use cases yet?
- No UCs → recommend `/a4:usecase` (interactive) or `/a4:auto-usecase` (autonomous).

**Layer 1 — Wiki foundation.** Is each wiki page that has dependent issues present?
- UCs exist, `domain.md` missing → recommend `/a4:usecase iterate` (domain is articulated during UC work).
- UCs exist, `architecture.md` missing → recommend `/a4:arch`.
- `architecture.md` exists, `roadmap.md` missing, tasks expected → recommend `/a4:roadmap`.
- Any issue's `wiki_impact:` references a non-existent wiki page — the drift detector emits this as a high-priority `missing-wiki-page` finding; pick it up in Layer 2.

**Layer 2 — Drift alerts.** Any open `review/*.md` with `source: drift-detector`?
- High priority first (`close-guard`, `missing-wiki-page`). Each item's `target:` or `wiki_impact:` tells you which iteration skill owns the fix: `architecture`/`domain`/etc. → `/a4:arch iterate`; `usecase/*` → `/a4:usecase iterate`; `task/*` → `/a4:roadmap iterate` or `/a4:run iterate`.

**Layer 3 — Open review items (non-drift).** Any other open review items?
- Sort by `priority` (high → medium → low) then by `created:`. Recommend the iteration skill that owns each item's `target:`. Route by target: wiki-scoped → `/a4:arch iterate` or `/a4:usecase iterate` depending on which wiki; `task/*` → `/a4:roadmap iterate` or `/a4:run iterate`.

**Layer 4 — Active tasks.** Any `task/*.md` with `status: pending | implementing | failing`?
- Yes → recommend `/a4:run iterate` (resume implementation).

**Layer 5 — Blocked items.** Any item with `status: blocked`?
- Read its `depends_on` chain to find the nearest unblocked predecessor; recommend the skill that owns that predecessor.

**Layer 6 — Completion.** Everything `done` / `complete` / `resolved` / `final`?
- Suggest either a new iteration (fresh UCs for the next milestone) or per-item archive of any targeted closed item (see Step 3.5).

### 3.4 Present diagnosis

Report in this format:

```
## Workspace Status

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
