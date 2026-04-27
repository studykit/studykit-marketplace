# a4

Manages `a4/` as a git-native wiki + issue tracker — usecase, architecture, and implementation-plan authoring, plus autonomous execution, brainstorming, and decision records.

## Prerequisites

The shared `get-api-docs` skill must also be available in the global skills set. a4 agents use this shared skill for current third-party API and SDK documentation lookup.

## Components

### Skills

| Name | Purpose |
|------|---------|
| `usecase` | Collaborative usecase specification design |
| `domain` | Cross-cutting Domain Model extraction (concepts, relationships, state transitions) |
| `arch` | Architecture design and review |
| `roadmap` | Implementation roadmap creation and review |
| `auto-bootstrap` | Autonomous project bootstrap with research |
| `auto-usecase` | Reverse-engineer or batch-shape UCs from a codebase / idea / brainstorm (no interview; not a twin of `usecase`) |
| `spark-brainstorm` | Structured brainstorming sessions |
| `research` | Standalone research facilitator; writes a portable artifact at `./research/<slug>.md` (outside `a4/`) referenced by spec files |
| `research-review` | Reviews a research artifact at `./research/<slug>.md` via the `research-reviewer` agent; applies accepted revisions |
| `spec` | Records a spec reached through conversation as `a4/spec/<id>-<slug>.md`; cites related research via `[[research/<slug>]]` wikilinks in body; nudges affected wiki pages |
| `compass` | Project direction and next-step guidance |
| `handoff` | Point-in-time session snapshot for cross-session continuity |
| `drift` | Wiki-drift detector; emits review items with `wiki_impact` |
| `validate` | Runs frontmatter-schema, body-convention, and cross-file status-consistency validators over `a4/` |
| `idea` | Quick-capture a one-line idea as `a4/idea/<id>-<slug>.md` |
| `web-design-mock` | Web design mock generation |
| `get-api-docs` | Shared global skill for current API/SDK documentation lookup |

### Hooks

Four hook flows share the same events, dispatched through a single Python entry point:

1. **Single-file validation** (blocking) — accumulate `a4/*.md` edits; validate at Stop; exit 2 on frontmatter/body violations so Claude retries.
2. **Cross-file status consistency** (non-blocking) — scan `a4/` on SessionStart and after each edit; inject findings as `additionalContext` so the LLM sees mismatches on the next turn without a retry loop.
3. **`implemented_by` reconciliation** (non-blocking) — refresh UC `implemented_by:` reverse-links on SessionStart so drift from cross-branch edits or manual task edits is healed before work begins.
4. **Issue-id resolution** (non-blocking) — scan UserPromptSubmit for `#<id>` references; inject the resolved `a4/<type>/<id>-<slug>.md` path so Claude reads the file directly instead of searching. Per-session dedupe — once an id has been announced, repeats stay silent.

| Event | Script | Purpose |
|-------|--------|---------|
| `PostToolUse` (`Write\|Edit\|MultiEdit`) | `scripts/a4_hook.py post-edit` | Record the edited `$project/a4/**/*.md` path to a session-scoped file, then run `validate_status_consistency.py --file <edited>` and inject mismatches in that file's connected component as `additionalContext`. Non-blocking. |
| `Stop` | `scripts/a4_hook.py stop` | Run `validate_frontmatter.py` + `validate_body.py` on each recorded file (single-file mode; workspace-wide id-uniqueness deferred to `/a4:validate`). Violations → `exit 2` with stderr so Claude retries. Clean → record file deleted. `stop_hook_active` → silent exit to avoid loops. Internal errors → exit 0 with stderr warning. |
| `SessionEnd` | `hooks/cleanup-edited-a4.sh` | Delete this session's record files (`a4-edited-<sid>.txt`, `a4-resolved-ids-<sid>.txt`). Always exits 0. |
| `SessionStart` | `hooks/sweep-old-edited-a4.sh` | `find -mtime +1 -delete` orphan record files from crashed sessions where SessionEnd never fired. Always exits 0. |
| `SessionStart` | `scripts/a4_hook.py session-start` | Refresh UC `implemented_by:` reverse-links (write; emits `systemMessage` + `additionalContext` when UCs change), then run `validate_status_consistency.py` and inject workspace-wide mismatches as `additionalContext`. Non-blocking; silent on clean. |
| `UserPromptSubmit` | `scripts/a4_hook.py user-prompt` | Match `#<id>` tokens in the prompt (`(?<![\w#])#(\d+)\b`); for each, glob `a4/{usecase,task,review,spec,idea}/<id>-*.md` and `a4/archive/**/<id>-*.md`; inject resolved paths as `additionalContext`. Skips ids already resolved this session via `a4-resolved-ids-<sid>.txt`. Non-blocking; silent on no match. |

**Scope.** Only files under `$project/a4/` are recorded by single-file validation. Pre-existing violations in files the user did not touch this session are not re-reported. Run `/a4:validate` manually for a full workspace sweep. Status consistency, by contrast, always scans workspace-wide — cross-file by definition.

**Design principles.** See `references/hook-conventions.md` for state classification, lifecycle symmetry, language choice, in-event ordering, non-blocking policy, and output channel usage.

### Agents

| Name | Purpose |
|------|---------|
| `api-researcher` | Find and return current API documentation |
| `arch-reviewer` | Review architecture designs |
| `research-reviewer` | Review research artifacts for source quality, option balance, bias, and decision neutrality |
| `domain-reviewer` | Review `domain.md` against UCs and architecture; emit per-finding review items |
| `task-implementer` | Implement tasks and write unit tests |
| `mock-html-generator` | Generate HTML mockups |
| `roadmap-reviewer` | Review implementation roadmaps |
| `test-runner` | Run tests and produce reports |
| `usecase-composer` | Compose usecase specifications |
| `usecase-explorer` | Explore and discover usecases |
| `usecase-reviewer` | Review usecase specifications |
| `usecase-reviser` | Revise usecases based on feedback |
| `workspace-assistant` | Forked-context delegate for workspace queries: find (body reading, multi-step lookup, summarization with `path:line` citations), snapshot (full or sectioned dashboard via `workspace_state.py`), and transition (executes caller-named `(file, target_status)` pairs via `transition_status.py`) |

## Document Layout (`a4/`)

`a4/` is a git-native **wiki + issue tracker** for the workspace — flat wiki pages describe the project shape; type-scoped folders hold lifecycle-tracked issues. Full model: `plugins/a4/spec/archive/2026-04-23-spec-as-wiki-and-issues.decide.md`.

```
<project-root>/
  a4/                                       # Markdown-only documentation workspace
    context.md architecture.md domain.md     # Wiki pages (flat):
    actors.md nfr.md roadmap.md bootstrap.md # one file per cross-cutting concern

    usecase/<id>-<slug>.md                    # Use Cases
    task/<id>-<slug>.md                       # Executable work units (Jira sense; kind: feature|spike|bug)
    review/<id>-<slug>.md                     # Findings, gaps, questions (unified)
    spec/<id>-<slug>.md                        # specs
    idea/<id>-<slug>.md                       # Pre-pipeline quick-capture ideas

    spark/<YYYY-MM-DD-HHmm>-<slug>.brainstorm.md
    archive/                                  # Closed items; folder = archived flag

  spike/                                    # PoC code for kind: spike tasks (sibling of a4/)
    <task-id>-<slug>/                       # Active spike (parallel to a4/task/<id>-<slug>.md)
    archive/<task-id>-<slug>/               # Archived after spike completes (manual git mv)

  research/                                 # Portable research artifacts from /a4:research
    <slug>.md                               # Cited from a4/spec/ body via [[research/<slug>]] wikilinks
```

### Wiki vs. issues

- **Wiki pages** describe the project shape. Each cross-cutting concern (context, domain, architecture, actors, nfr, plan, bootstrap) is one flat file at `a4/` root — no `overview.md` catchall. Wiki pages have no lifecycle but are continuously updated by related issue state changes.
- **Issues** are lifecycle-tracked items in type-scoped folders. Each carries independent `status`, `updated`, `labels`, `milestone` in frontmatter — "what's open?" is answerable without reading prose.
- **Review items unify open items, gaps, and questions** — all three share the `review/` folder, distinguished by `kind: finding | gap | question`.
- **Ideas vs. reviews** — `review/` captures gaps in the **current** spec that (usually) block progress; `idea/` captures **independent possibilities** that never block. Lifecycle differs: review items are worked on (`open | in-progress | resolved | discarded`); ideas are graduated or dropped (`open | promoted | discarded`). Capture ideas via `/a4:idea <line>`. Full rationale: `plugins/a4/spec/archive/2026-04-24-idea-slot.decide.md`.
- **Spike vs. feature task** — every task carries `kind: feature | spike | bug`. `feature` is the default (regular implementation work); `spike` is time-boxed exploration whose throwaway code lives at project-root `spike/<id>-<slug>/` (outside `a4/`); `bug` is a defect fix. Closed spikes are archived by manual `git mv` to `spike/archive/<id>-<slug>/`. Full rationale: `plugins/a4/spec/archive/2026-04-24-experiments-slot.decide.md`.

### Conventions

- **Ids are globally monotonic integers** (GitHub issue semantics) — unique across all folders. Allocator: `scripts/allocate_id.py` computes `max(existing ids) + 1`.
- **Filenames are `<id>-<slug>.md`.** Folder indicates type; no `uc-`/`task-`/`rev-`/`d-` prefix.
- **Obsidian markdown throughout.** Body uses `[[wikilinks]]` and `![[embeds]]`; frontmatter paths are plain strings (no brackets, no extension) for dataview compatibility.
- **Forward-direction relationships only** in frontmatter: `depends_on`, `implements`, `target`, `wiki_impact`, `spec`, `supersedes`, `parent`, `related`. Reverse views (`blocks`, `implemented_by`, `children`, …) are computed by dataview.

### Wiki update protocol

Wiki pages carry no lifecycle but are continuously updated. All edits flow through **review items** as the unified conduit:

1. Modified sections carry sequential footnote markers (`[^1]`, `[^2]`, …) inline; a `## Changes` section at page bottom resolves each to `YYYY-MM-DD — [[causing-issue]]`.
2. Three entry paths converge on review items: single-edit skills nudge in-situ ("does this change need a wiki update?"); reviewer agents emit review items with `wiki_impact` set; bulk-generation skills invoke `/a4:drift` as a final step.
3. **Close guard** — a review item with non-empty `wiki_impact` warns on close if any referenced wiki page lacks a footnote pointing back to the causing issue (warning + override; user retains final say).

### Derived views

Use Case Diagram, authorization matrix, open-issue lists, milestone progress — all **rendered from source on demand**, never hand-maintained. Obsidian dataview can render these directly inside the vault; the `workspace-assistant` agent (snapshot mode) renders a parallel plain-markdown view to stdout for sessions that aren't using Obsidian.

### Workspace dashboard

The `workspace-assistant` agent (snapshot mode) renders the current workspace state to stdout — no file is written. Sections: Wiki pages, Stage progress, Issue counts, Use cases by source, Drift alerts, Open reviews, Active tasks, Blocked items, Milestones, Recent activity, Open ideas, Open sparks. The dashboard is a fresh **view** computed each run from per-item frontmatter (the source of truth), so re-rendering is always safe. `/a4:compass` consumes the same script (`scripts/workspace_state.py`) for its layered gap diagnosis.

### Archive

Closed items are archived by `git mv`-ing them into `a4/archive/`. Folder location is the flag — there is no `archived:` frontmatter field. The move is always user-confirmed.
