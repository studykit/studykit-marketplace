---
name: a4-workspace-policies
description: Cross-cutting policies that apply to every file under `a4/`. Auto-loaded whenever Claude reads any `a4/**/*.md` file. Per-type authoring rules (`a4-task-feature-authoring.md`, `a4-task-bug-authoring.md`, `a4-task-spike-authoring.md`, `a4-architecture-authoring.md`, etc.) build on top of these policies and only document type-specific shape.
paths: ["a4/**/*.md"]
---

# a4 — workspace-wide policies

These rules apply to **every** file under `a4/`, regardless of type or
location. They are the working contract for any LLM about to read,
draft, edit, or review an a4 artifact. Per-type authoring rules (e.g.,
`a4-task-feature-authoring.md`, `a4-task-bug-authoring.md`,
`a4-task-spike-authoring.md`, `a4-architecture-authoring.md`) describe
type-specific frontmatter / body / lifecycle on top of these
cross-cutting policies — they do not redefine them.

The deeper specs live in `references/`:

- [`frontmatter-schema.md`](../references/frontmatter-schema.md) — full field schema, lifecycle tables, validator behavior.
- [`body-conventions.md`](../references/body-conventions.md) — body tag form, blank-line discipline, link form, `<change-logs>` / `<log>` rules, wiki update protocol.
- [`wiki-authorship.md`](../references/wiki-authorship.md) — primary-author table, cross-stage feedback policy.
- [`iterate-mechanics.md`](../references/iterate-mechanics.md) — review-item walk procedure.
- [`commit-message-convention.md`](../references/commit-message-convention.md) — `#<id>` commit subject form.
- [`spec-triggers.md`](../references/spec-triggers.md) — when a spec is warranted.

Read those before deviating from the rules below. This rule is the
**reminder card**, not the spec.

## 1. Writer-owned fields — never hand-edit

Several frontmatter fields are owned by `scripts/transition_status.py`
or other writer scripts. Skills, agents, and humans never write these
directly — they call the writer.

| Field | Owner script | Where it lives |
|---|---|---|
| `status:` (issue families) | `scripts/transition_status.py` | task, usecase, spec, review, idea, brainstorm |
| `updated:` (wiki + issue) | writer (any status flip; manual bump only when prose-edited a wiki page outside any flip) | every a4 file |
| `<log>` body section | writer (one bullet per transition) | task, usecase, spec, review |
| `implemented_by:` | `scripts/refresh_implemented_by.py` | usecase |
| `cited_by:` | `scripts/register_research_citation.py` | research (outside `a4/`, but same rule) |
| `research:` (spec) + `<research>` body | `scripts/register_research_citation.py` | spec |
| `<cited-by>` body (research) | `scripts/register_research_citation.py` | research |
| Cascade-driven status (UC discarded → tasks discarded; UC revising → progress/failing tasks → pending; spec active → predecessors superseded) | `transition_status.py` cascades | task, usecase, spec |

The exception, documented per-rule: post-hoc `task` creation at
`status: complete` writes the **first** `<log>` entry directly because
the writer never logged a transition for that path. Every subsequent
entry is the writer's.

## 2. ID allocation — `allocate_id.py` only

- IDs are **globally monotonic across the entire `a4/` workspace**,
  GitHub-issue style. Tasks, UCs, specs, reviews, ideas all share one
  number space.
- Allocate via:
  ```bash
  uv run "../scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
  ```
- **Never** invent, reuse, or renumber an id. Gaps are fine — the
  Stop hook will not flag them.
- Filename form: `<id>-<slug>.md` (no `task-` / `usecase-` prefix —
  the folder names the type).

## 3. Path-reference form

a4 makes a deliberate distinction between frontmatter values and body
links:

- **Frontmatter list values** (e.g., `implements:`, `depends_on:`,
  `supersedes:`, `target:`, `spec:`, `research:`) are **plain strings
  without `.md` and without brackets**:
  ```yaml
  implements: [usecase/3-search-history, usecase/4-render-preview]
  depends_on: [task/4-parse-config]
  ```
- **Body cross-references** are **standard markdown links with `.md`
  retained**:
  ```markdown
  Relates to [usecase/3-search-history](../usecase/3-search-history.md).
  ```

The two forms are not interchangeable. The frontmatter validator
rejects bracketed paths; the body validator accepts only fenced /
markdown links inside section blocks.

## 4. Body tag form

Body sections use **column-0** `<tag>...</tag>` blocks:

- Open and close lines start at column 0 (no leading whitespace).
- Tag names are **lowercase + kebab-case**.
- **No attributes**. No self-closing. No same-tag nesting (sections
  do not nest; every section sits at the body's top level).
- Unknown kebab-case tags are tolerated by each XSD's openContent —
  the per-type rule lists which sections are required vs optional.
- Use H3+ markdown headings inside sections freely. **H1 (`# Title`)
  is forbidden in the body** — title belongs to frontmatter `title:`
  on issue files, or the file basename on wiki pages.

Anything in the body that is not whitespace must live inside a
`<tag>...</tag>` block. The validator name for stray content is
`body-stray-content`.

## 5. `<change-logs>` discipline

Every wiki page (and every issue file with materially edited body
content post-create) tracks edits in `<change-logs>`:

```markdown
<change-logs>

- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — <short note>
- YYYY-MM-DD — [usecase/<id>-<slug>](usecase/<id>-<slug>.md) — <short note>

</change-logs>
```

Rules:

- **Append-only.** Earlier bullets are never edited or removed.
- **Every bullet has a markdown link** to the causing issue / spec /
  review item. Bare-text bullets break drift detection and the wiki
  close-guard.
- **Create the section if absent.** Per the per-type XSD,
  `<change-logs>` is optional but expected after the first non-trivial
  edit.
- **The wiki close guard** warns when a review item with
  `wiki_impact: [<wiki>]` transitions to `resolved` but the named
  wiki has no bullet pointing back at the review id. Drift detector
  re-surfaces close-guard violations.

## 6. Wiki authorship — primary author + review-item escape hatch

Each wiki page has exactly one primary author skill. Other skills may
edit only under the limited in-situ rules in
[`wiki-authorship.md`](../references/wiki-authorship.md);
everything else flows through review items.

Quick-reference summary (full table is in `wiki-authorship.md`):

| Wiki page | Primary author |
|---|---|
| `context.md`, `actors.md`, `nfr.md` | `usecase` |
| `domain.md` | `domain` (limited shared with `arch`) |
| `architecture.md` | `arch` (no other skill edits in-situ) |
| `bootstrap.md` | `auto-bootstrap` (single source of truth for L&V) |
| `roadmap.md` | `roadmap` |

When you find yourself wanting to edit a wiki page from any skill that
is **not** its primary author and not within the limited in-situ
allowance, **stop** and emit a review item:

```yaml
type: review
kind: gap | finding
target: <wiki-basename>          # e.g., architecture
wiki_impact: [<wiki-basename>]
source: self | <reviewer-name> | drift-detector
priority: high | medium | low
```

The owning skill's `iterate` mode picks up the review item later.

## 7. Cross-stage feedback — stop vs continue

When a stage discovers a problem upstream of itself, it picks one of
two responses based on **whether its output is valid before the
upstream issue is fixed**:

- **Strong dependency** — output depends directly on upstream
  correctness; continuing produces output that the upstream fix will
  invalidate. → **stop**.
- **Weak dependency** — output is independently meaningful; the
  upstream fix may suggest a re-run, but current output is still
  useful. → **continue + review item**.

Stage-by-stage decisions are tabulated in
[`wiki-authorship.md`](../references/wiki-authorship.md)
§Cross-stage feedback policy. Highlights:

- `roadmap`, `run` Step 4, `roadmap-reviewer` → **stop** on arch / UC
  upstream issues.
- `auto-bootstrap`, `usecase iterate`, `domain`, `auto-usecase`,
  `arch iterate` → **continue + review item**.

## 8. Iterate flows — writer-only review walk

When walking review items in any iterate mode (`usecase iterate`,
`domain iterate`, `arch iterate`, `roadmap iterate`, `run iterate`):

- Filter the backlog per the stage's filter expression
  (see [`iterate-mechanics.md`](../references/iterate-mechanics.md) §1).
- **Pick → in-progress** via `transition_status.py --to in-progress`.
- **Resolve → resolved** via `transition_status.py --to resolved`.
- **Discard → discarded** via `transition_status.py --to discarded`.
- Never hand-edit `status:` / `updated:` / `<log>` on review items.
- Never delete review item files. `discarded` is the writer-managed
  terminal state.

Stage-specific work between writer calls (impact rules, cycle
counters, scope handling) lives in each SKILL.md's Iteration Entry
section, not here.

## 9. Commit message form

a4 commits use `#<id>`-bearing Conventional-Commits subjects:

```
#<id1> [#<id2> ...] <type>(a4): <description>
```

ID-less form (plugin meta-edits, ambient docs):

```
<type>(a4): <description>
```

`<type>` ∈ `feat | fix | docs | refactor | chore | test | merge`.
`merge(a4)` is reserved for `/a4:run`'s `--no-ff` integration commits
that fold a `task-implementer` worktree branch into local main.

Multiple ids are space-separated and appear before the
Conventional-Commits prefix. The `#<id>` prefix is what makes
`git log --grep="#42"` return artifact 42's full lifecycle.

Per-skill commit-point details (when to commit, which files to stage)
live in each SKILL.md's "Commit Points" section. Subject form is
[`commit-message-convention.md`](../references/commit-message-convention.md)'s
job.

## 10. Universally-applicable Don'ts

- **Don't hand-edit writer-owned fields** (§1).
- **Don't invent or renumber ids** (§2).
- **Don't bracket frontmatter paths or omit `.md` from body links** (§3).
- **Don't write H1 in body, attribute-bearing tags, or stray text outside section blocks** (§4).
- **Don't append `<change-logs>` bullets without a markdown link to the cause** (§5).
- **Don't edit a wiki page from a non-primary-author skill outside the limited in-situ scope** — emit a review item (§6).
- **Don't continue a stage when its output depends on an unresolved upstream issue (strong dependency)** — stop and route to the upstream `iterate` (§7).
- **Don't delete review item files** — `discarded` is terminal (§8).

## When to read this rule explicitly

You don't normally need to — it auto-loads on every a4 file Read. But
read it when:

- You're authoring a new skill / agent / script that touches `a4/`.
- A reviewer flagged a violation you don't recognize — start here
  before drilling into the per-type rule.
- You're updating one of the cross-cutting references (any change to
  `wiki-authorship.md` / `iterate-mechanics.md` / `body-conventions.md`
  may need the §6–§8 summaries here refreshed).
