# a4

Manages `a4/` as a git-native wiki + issue tracker — usecase, architecture, and implementation-plan authoring, plus autonomous execution, brainstorming, and decision records.

## Prerequisites

The `find-docs` skill must be installed. Set it up via [ctx7 CLI](https://context7.com/docs/clients/cli):

```bash
ctx7 setup --cli --claude       # Claude Code (~/.claude/skills)
```

The shared `get-api-docs` skill must also be available in the global skills set. a4 agents use this shared skill for current third-party API and SDK documentation lookup.

## Components

### Skills

| Name | Purpose |
|------|---------|
| `usecase` | Collaborative usecase specification design |
| `arch` | Architecture design and review |
| `plan` | Implementation plan creation and review |
| `auto-bootstrap` | Autonomous project bootstrap with research |
| `auto-usecase` | Autonomous usecase generation |
| `spark-brainstorm` | Structured brainstorming sessions |
| `spark-decide` | Solution discovery facilitator; writes an ADR as `a4/decision/<id>-<slug>.md` |
| `compass` | Project direction and next-step guidance |
| `handoff` | Point-in-time session snapshot for cross-session continuity |
| `drift` | Wiki-drift detector; emits review items with `wiki_impact` |
| `index` | Regenerates `a4/INDEX.md` dashboard |
| `validate` | Runs frontmatter-schema and body-convention validators over `a4/` |
| `idea` | Quick-capture a one-line idea as `a4/idea/<id>-<slug>.md` |
| `web-design-mock` | Web design mock generation |
| `get-api-docs` | Shared global skill for current API/SDK documentation lookup |

### Hooks

Session-scoped accumulate-then-validate pattern. Edits to `a4/*.md` are recorded as they happen; the record is drained and validated at Stop, cleaned up at SessionEnd, and orphan records swept at SessionStart.

| Event | Script | Purpose |
|-------|--------|---------|
| `PostToolUse` (`Write\|Edit\|MultiEdit`) | `hooks/record-edited-a4.sh` | Append absolute path of any edited `$project/a4/**/*.md` to `$project/.claude/tmp/a4-edited/a4-edited-<session_id>.txt`. Always exits 0. |
| `Stop` | `hooks/validate-edited-a4.sh` | Run `validate_frontmatter.py` + `validate_body.py` on each recorded file (single-file mode; workspace-wide id-uniqueness deferred to `/a4:validate`). Violations → `exit 2` with stderr so Claude retries with the feedback. Clean → record file deleted. `stop_hook_active` → silent exit to avoid loops. Internal errors (missing scripts, unexpected rc) → exit 0 with stderr warning; never block on hook bugs. |
| `SessionEnd` | `hooks/cleanup-edited-a4.sh` | Delete this session's record file. Always exits 0. |
| `SessionStart` | `hooks/sweep-old-edited-a4.sh` | `find -mtime +1 -delete` orphan records from crashed sessions where SessionEnd never fired. Always exits 0. |

**Scope.** Only files under `$project/a4/` are recorded. Pre-existing violations in files the user did not touch this session are not re-reported — keeps the hook quiet on legacy workspaces. Run `/a4:validate` manually for a full workspace sweep.

### Agents

| Name | Purpose |
|------|---------|
| `api-researcher` | Find and return current API documentation |
| `arch-reviewer` | Review architecture designs |
| `decision-reviewer` | Review decision records |
| `domain-updater` | Update domain models |
| `task-implementer` | Implement tasks and write unit tests |
| `mock-html-generator` | Generate HTML mockups |
| `plan-reviewer` | Review implementation plans |
| `test-runner` | Run tests and produce reports |
| `usecase-composer` | Compose usecase specifications |
| `usecase-explorer` | Explore and discover usecases |
| `usecase-reviewer` | Review usecase specifications |
| `usecase-reviser` | Revise usecases based on feedback |

## Document Layout (`a4/`)

`a4/` is a git-native **wiki + issue tracker** for the workspace — flat wiki pages describe the project shape; type-scoped folders hold lifecycle-tracked issues. Full model: `plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md`.

```
<project-root>/
  a4/                                       # Markdown-only documentation workspace
    context.md architecture.md domain.md     # Wiki pages (flat):
    actors.md nfr.md plan.md bootstrap.md    # one file per cross-cutting concern

    usecase/<id>-<slug>.md                    # Use Cases
    task/<id>-<slug>.md                       # Executable work units (Jira sense; kind: feature|spike|bug)
    review/<id>-<slug>.md                     # Findings, gaps, questions (unified)
    decision/<id>-<slug>.md                   # ADRs
    idea/<id>-<slug>.md                       # Pre-pipeline quick-capture ideas

    spark/<YYYY-MM-DD-HHmm>-<slug>.brainstorm.md
    archive/                                  # Closed items; folder = archived flag
    INDEX.md                                  # Regenerated dashboard

  spike/                                    # PoC code for kind: spike tasks (sibling of a4/)
    <task-id>-<slug>/                       # Active spike (parallel to a4/task/<id>-<slug>.md)
    archive/<task-id>-<slug>/               # Archived after spike completes (manual git mv)
```

### Wiki vs. issues

- **Wiki pages** describe the project shape. Each cross-cutting concern (context, domain, architecture, actors, nfr, plan, bootstrap) is one flat file at `a4/` root — no `overview.md` catchall. Wiki pages have no lifecycle but are continuously updated by related issue state changes.
- **Issues** are lifecycle-tracked items in type-scoped folders. Each carries independent `status`, `updated`, `labels`, `milestone` in frontmatter — "what's open?" is answerable without reading prose.
- **Review items unify open items, gaps, and questions** — all three share the `review/` folder, distinguished by `kind: finding | gap | question`.
- **Ideas vs. reviews** — `review/` captures gaps in the **current** spec that (usually) block progress; `idea/` captures **independent possibilities** that never block. Lifecycle differs: review items are worked on (`open | in-progress | resolved | dismissed`); ideas are graduated or dropped (`open | promoted | discarded`). Capture ideas via `/a4:idea <line>`. Full rationale: `plugins/a4/spec/2026-04-24-idea-slot.decide.md`.
- **Spike vs. feature task** — every task carries `kind: feature | spike | bug`. `feature` is the default (regular implementation work); `spike` is time-boxed exploration whose throwaway code lives at project-root `spike/<id>-<slug>/` (outside `a4/`); `bug` is a defect fix. Closed spikes are archived by manual `git mv` to `spike/archive/<id>-<slug>/`. Full rationale: `plugins/a4/spec/2026-04-24-experiments-slot.decide.md`.

### Conventions

- **Ids are globally monotonic integers** (GitHub issue semantics) — unique across all folders. Allocator: `scripts/allocate_id.py` computes `max(existing ids) + 1`.
- **Filenames are `<id>-<slug>.md`.** Folder indicates type; no `uc-`/`task-`/`rev-`/`d-` prefix.
- **Obsidian markdown throughout.** Body uses `[[wikilinks]]` and `![[embeds]]`; frontmatter paths are plain strings (no brackets, no extension) for dataview compatibility.
- **Forward-direction relationships only** in frontmatter: `depends_on`, `implements`, `target`, `wiki_impact`, `justified_by`, `supersedes`, `parent`, `related`. Reverse views (`blocks`, `implemented_by`, `children`, …) are computed by dataview.

### Wiki update protocol

Wiki pages carry no lifecycle but are continuously updated. All edits flow through **review items** as the unified conduit:

1. Modified sections carry sequential footnote markers (`[^1]`, `[^2]`, …) inline; a `## Changes` section at page bottom resolves each to `YYYY-MM-DD — [[causing-issue]]`.
2. Three entry paths converge on review items: single-edit skills nudge in-situ ("does this change need a wiki update?"); reviewer agents emit review items with `wiki_impact` set; bulk-generation skills invoke `/a4:drift` as a final step.
3. **Close guard** — a review item with non-empty `wiki_impact` warns on close if any referenced wiki page lacks a footnote pointing back to the causing issue (warning + override; user retains final say).

### Derived views

Use Case Diagram, authorization matrix, open-issue lists, milestone progress — all **rendered from source on demand**, never hand-maintained. Obsidian dataview powers interactive rendering; `INDEX.md` carries static markdown fallbacks (wrapped in `<!-- static-fallback-start/end -->` markers) for plain-text viewers.

### Workspace dashboard

`a4/INDEX.md` is regenerated by compass (Step 0) or on-demand via `/a4:index`. Sections: Wiki pages, Stage progress, Open issues, Drift alerts, Milestones, Recent activity, Open ideas, Spark. Each pairs a dataview block with a static fallback. INDEX is a **view** (source of truth = wiki pages and issue files), so regenerating is always safe.

### Archive

Closed items are archived by `git mv`-ing them into `a4/archive/`. Folder location is the flag — there is no `archived:` frontmatter field. The move is always user-confirmed.
