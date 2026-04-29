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
| `research-review` | Reviews a `kind: research` task body via the `research-reviewer` agent; applies accepted revisions |
| `spec` | Records a spec reached through conversation as `a4/spec/<id>-<slug>.md`; soft-links related research tasks via standard markdown body links + optional `related:` frontmatter; nudges affected wiki pages |
| `compass` | Project direction and next-step guidance |
| `handoff` | Point-in-time session snapshot for cross-session continuity |
| `drift` | Wiki-drift detector; emits review items whose `target:` includes the affected wiki basenames |
| `validate` | Runs frontmatter-schema, body-convention, and cross-file status-consistency validators over `a4/` |
| `idea` | Quick-capture a one-line idea as `a4/idea/<id>-<slug>.md` |
| `web-design-mock` | Web design mock generation |
| `get-api-docs` | Shared global skill for current API/SDK documentation lookup |

### Hooks

Three hook flows share the same events, dispatched through a single Python entry point:

1. **Single-file validation** (blocking) — accumulate `a4/*.md` edits; validate at Stop; exit 2 on frontmatter violations so Claude retries.
2. **Cross-file status consistency** (non-blocking) — after each edit, run the `status` check on the edited file's connected component and inject findings as `additionalContext`. Workspace-wide sweeps are manual via `/a4:validate`; SessionStart no longer fires status reporting.
3. **Issue-id resolution** (non-blocking) — scan UserPromptSubmit for `#<id>` references; inject the resolved `a4/<type>/<id>-<slug>.md` path so Claude reads the file directly instead of searching. Per-session dedupe — once an id has been announced, repeats stay silent.

| Event | Script | Purpose |
|-------|--------|---------|
| `PostToolUse` (`Write\|Edit\|MultiEdit`) | `scripts/a4_hook.py post-edit` | Record the edited `$project/a4/**/*.md` path to a session-scoped file, then run the `status` check in file mode (connected component reached via `supersedes:`) and inject mismatches as `additionalContext`. Non-blocking. |
| `Stop` | `scripts/a4_hook.py stop` | Run the `frontmatter` check on each recorded file (single-file mode; workspace-wide id-uniqueness deferred to `/a4:validate`). Violations → `exit 2` with stderr so Claude retries. Clean → record file deleted. `stop_hook_active` → silent exit to avoid loops. Internal errors → exit 0 with stderr warning. |
| `SessionEnd` | `hooks/cleanup-edited-a4.sh` | Delete this session's record files (`a4-edited-<sid>.txt`, `a4-resolved-ids-<sid>.txt`). Always exits 0. |
| `SessionStart` | `hooks/sweep-old-edited-a4.sh` | `find -mtime +1 -delete` orphan record files from crashed sessions where SessionEnd never fired. Always exits 0. |
| `UserPromptSubmit` | `scripts/a4_hook.py user-prompt` | Match `#<id>` tokens in the prompt (`(?<![\w#])#(\d+)\b`); for each, glob `a4/{usecase,task,review,spec,idea}/<id>-*.md` and `a4/archive/**/<id>-*.md`; inject resolved paths as `additionalContext`. Skips ids already resolved this session via `a4-resolved-ids-<sid>.txt`. Non-blocking; silent on no match. |

**Scope.** Only files under `$project/a4/` are recorded by single-file validation. Pre-existing violations in files the user did not touch this session are not re-reported. Run `/a4:validate` for a full workspace sweep — status-consistency reporting is now manual rather than firing on SessionStart.

**Design principles.** See `docs/hook-conventions.md` for state classification, lifecycle symmetry, language choice, in-event ordering, non-blocking policy, and output channel usage.

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
    task/feature/<id>-<slug>.md               # Executable work units (Jira sense) — kind subfolder is required
    task/bug/<id>-<slug>.md                   #   so per-kind authoring rules auto-load on read/edit
    task/spike/<id>-<slug>.md
    task/research/<id>-<slug>.md              # Investigation tasks; body is the deliverable
    review/<id>-<slug>.md                     # Findings, gaps, questions (unified)
    spec/<id>-<slug>.md                        # specs
    idea/<id>-<slug>.md                       # Pre-pipeline quick-capture ideas

    spark/<YYYY-MM-DD-HHmm>-<slug>.brainstorm.md
    archive/                                  # Closed items; folder = archived flag

  artifacts/task/                           # Task artifact directories (sibling of a4/)
    spike/<id>-<slug>/                      # Active spike — PoC code, data, scratch notes
    spike/archive/<id>-<slug>/              # Archived after spike completes (manual git mv)
    research/<id>-<slug>/                   # Optional — raw data, charts, eval scripts
    feature/<id>-<slug>/                    # Optional — comparison samples, execution outputs
    bug/<id>-<slug>/                        # Optional — repro, logs, screenshots
```

### Wiki vs. issues

- **Wiki pages** describe the project shape. Each cross-cutting concern (context, domain, architecture, actors, nfr, plan, bootstrap) is one flat file at `a4/` root — no `overview.md` catchall. Wiki pages have no lifecycle but are continuously updated by related issue state changes.
- **Issues** are lifecycle-tracked items in type-scoped folders. Each carries independent `status`, `updated`, `labels` in frontmatter — "what's open?" is answerable without reading prose.
- **Review items unify open items, gaps, and questions** — all three share the `review/` folder, distinguished by `kind: finding | gap | question`.
- **Ideas vs. reviews** — `review/` captures gaps in the **current** spec that (usually) block progress; `idea/` captures **independent possibilities** that never block. Lifecycle differs: review items are worked on (`open | in-progress | resolved | discarded`); ideas are graduated or dropped (`open | promoted | discarded`). Capture ideas via `/a4:idea <line>`. Full rationale: `plugins/a4/spec/archive/2026-04-24-idea-slot.decide.md`.
- **Spike vs. feature vs. research task** — every task carries `kind: feature | spike | bug | research`. `feature` is the default (regular implementation work); `spike` is time-boxed exploration whose throwaway code lives at project-root `artifacts/task/spike/<id>-<slug>/` (outside `a4/`); `bug` is a defect fix; `research` is a written investigation whose body is the deliverable (sources consulted, findings, options). Any kind may opt in to an `artifacts/task/<kind>/<id>-<slug>/` sibling directory for byproducts that need to live alongside the task — see `plugins/a4/references/frontmatter-schema.md#task-artifacts-convention` for what each kind typically stores there. Closed spikes are archived by manual `git mv` to `artifacts/task/spike/archive/<id>-<slug>/`. Full rationale: `plugins/a4/spec/archive/2026-04-24-experiments-slot.decide.md`.
- **Task kind = subfolder.** Task files live under `a4/task/<kind>/<id>-<slug>.md`, where `<kind>` matches the `kind:` frontmatter (one of `feature` / `bug` / `spike` / `research`). The kind subfolder is the path scope that lets the matching per-kind authoring rule (`a4-task-feature-authoring.md`, `a4-task-bug-authoring.md`, `a4-task-spike-authoring.md`, `a4-task-research-authoring.md`) auto-load on read or edit. Reference forms in frontmatter (`implements`, `depends_on`, `target`, etc.) keep the bare `task/<id>-<slug>` shape (no kind segment) so refs stay stable when a task is moved between kinds.

### Conventions

- **Ids are globally monotonic integers** (GitHub issue semantics) — unique across all folders. Allocator: `scripts/allocate_id.py` computes `max(existing ids) + 1`.
- **Filenames are `<id>-<slug>.md`.** Folder indicates type; no `uc-`/`task-`/`rev-`/`d-` prefix.
- **Standard markdown links throughout.** Body uses `[text](relative/path.md)` (renderable by GitHub, VSCode, any markdown viewer); frontmatter paths are plain strings (no brackets, no extension) for stable machine parsing.
- **Forward-direction relationships only** in frontmatter: `depends_on`, `implements`, `target`, `spec`, `supersedes`, `parent`, `related`. Reverse views (`blocks`, `children`, UC ↔ task, …) are computed on demand (`search.py`, roadmap surfaces).

### Wiki update protocol

Wiki pages carry no lifecycle but are continuously updated. All edits flow through **review items** as the unified conduit:

1. Each substantive wiki edit appends a `## Change Logs` bullet — `- YYYY-MM-DD — [<causing-issue>](<relative-path>.md)` — pointing at the issue that drove the change. See `references/body-conventions.md §## Change Logs audit trail`.
2. Two entry paths converge on review items: single-edit skills nudge in-situ ("does this change need a wiki update?"); reviewer agents emit review items whose `target:` lists the affected wiki basenames.
3. **Close guard (advisory)** — when a review with one or more wiki targets transitions to `resolved`, ensure each referenced wiki page records the change in its `## Change Logs`. There is no automated re-surfacer at this point; re-run `/a4:validate` after wiki edits if you need a sweep.

### Derived views

Use Case Diagram, authorization matrix, open-issue lists, roadmap milestone narrative — all **rendered from source on demand**, never hand-maintained. Obsidian dataview can render these directly inside the vault; the `workspace-assistant` agent (snapshot mode) renders a parallel plain-markdown view to stdout for sessions that aren't using Obsidian.

### Workspace dashboard

The `workspace-assistant` agent (snapshot mode) renders the current workspace state to stdout — no file is written. Sections: Wiki pages, Stage progress, Issue counts, Use cases by source, Open reviews, Active tasks, Blocked items, Recent activity, Open ideas, Open sparks. The dashboard is a fresh **view** computed each run from per-item frontmatter (the source of truth), so re-rendering is always safe. `/a4:compass` consumes the same script (`scripts/workspace_state.py`) for its layered gap diagnosis.

### Archive

Closed items are archived by `git mv`-ing them into `a4/archive/`. Folder location is the flag — there is no `archived:` frontmatter field. The move is always user-confirmed.

## Migration: `spike/` → `artifacts/task/spike/` (a4 v5.0.0)

a4 v5.0.0 replaced the per-spike sidecar `<project-root>/spike/<id>-<slug>/` with the unified artifact directory `<project-root>/artifacts/task/<kind>/<id>-<slug>/`. Existing projects with a populated `spike/` tree should migrate by hand:

```bash
# 1. Move active spike directories under the new root.
mkdir -p artifacts/task/spike
git mv spike/* artifacts/task/spike/   # leaves spike/archive/ behind if present
[ -d spike/archive ] && git mv spike/archive artifacts/task/spike/archive
rmdir spike

# 2. Rewrite `files:` paths in spike task markdown.
#    macOS sed; for GNU sed drop the empty -i argument.
find a4/task/spike -name '*.md' -print0 \
  | xargs -0 sed -i '' \
      -e 's|^\(\s*-\s*\)spike/|\1artifacts/task/spike/|' \
      -e 's|files: \[spike/|files: [artifacts/task/spike/|g'

# 3. Verify and commit.
uv run plugins/a4/scripts/validate.py
git status
```

Validator changes that strictly enforce the new path prefixes are deferred to a follow-up release; for now the migration is documentation-driven. Tasks whose `files:` still reference `spike/...` keep working but no longer match the schema, so migrate when convenient.
