# a4 plugin — working notes

## `<project-root>/a4/` is the user-project workspace

When an a4 skill runs in a user project, it reads and writes a single workspace at `<project-root>/a4/` — a git-native **wiki + issue tracker** in plain markdown.

**Layout** :

```
<project-root>/
  a4/
    context.md domain.md architecture.md         # Wiki pages (flat, no lifecycle):
    actors.md  nfr.md    roadmap.md  bootstrap.md  # one file per cross-cutting concern
    usecase/<id>-<slug>.md     # Use Cases
    task/<id>-<slug>.md        # Executable work units (kind: feature | spike | bug)
    decision/<id>-<slug>.md    # ADRs (status: draft | final | superseded)
    review/<id>-<slug>.md      # Findings / gaps / questions (kind: finding | gap | question)
    idea/<id>-<slug>.md        # Pre-pipeline quick-capture
    spark/<YYYY-MM-DD-HHmm>-<slug>.brainstorm.md
    archive/                   # Closed items; folder = archived flag

  spike/<task-id>-<slug>/      # PoC code for kind: spike tasks (sibling of a4/)
  research/<slug>.md           # Portable research artifacts (sibling of a4/, referenced by ADRs)
```

**Conventions**:

- **Global monotonic ids.** `id` is unique across the entire workspace (GitHub-issue semantics). Allocated by `scripts/allocate_id.py`.
- **Filenames.** `<id>-<slug>.md`. Folder indicates type — no `uc-` / `task-` prefix.
- **Wiki updates flow through review items.** Wiki pages have no lifecycle but change continuously; edits are nudged by single-edit skills, deferred via `kind: gap` review items, and reconciled by the drift detector. Footnote markers (`[^N]`) + `## Changes` section record causes.
- **Obsidian markdown throughout.** Body uses `[[wikilinks]]` and `![[embeds]]`. Frontmatter paths are plain strings (no brackets, no `.md`).

## `plugins/a4/spec/` is plugin meta-design, not user output

`plugins/a4/spec/` records ADRs about the **a4 plugin itself** — design decisions made while building a4 (skill split, schema choices, hook architecture, etc.). It is *not* the output of running an a4 skill.

**Layout.** Active ADRs live directly in `plugins/a4/spec/`. 

## References — read before editing

Reference docs in `plugins/a4/references/` are the authoritative source for cross-cutting concerns. Read the relevant one before changing any skill/script that touches it:

- `frontmatter-schema.md` — frontmatter contract (also required by root CLAUDE.md)
- `pipeline-shapes.md` — Full / Reverse-engineer / Minimal / No-shape; read before changing shape-aware skills (`auto-bootstrap`, `run`, `compass`)
- `skill-modes.md` — interactive vs autonomous, forward vs reverse axes
- `wiki-authorship.md` — who can write each wiki page; cross-stage feedback policy
- `adr-triggers.md` — when an ADR is warranted
- `iterate-mechanics.md` — iterate-mode contract for skills
- `obsidian-conventions.md` — wikilinks, embeds, change footnotes
- `hook-conventions.md` — hook contract

## Skill-generated frontmatter is script-managed

Frontmatter on files written by a4 skills (under `<project-root>/a4/`) is the responsibility of scripts in `plugins/a4/scripts/`, not hand edits. This keeps cross-file consistency and reverse-links intact.

- Status transitions go through `transition_status.py`. Skills never write `status:` directly after the initial create.
- Status enums, transitions, and terminal/in-progress sets live in `scripts/status_model.py` — the canonical model imported by the writer, validators, workspace state, and search. Add new status values there first; consumers pick them up automatically. The ASCII transition diagrams in `references/frontmatter-schema.md` are generated from this module by `scripts/generate_status_diagrams.py`; the repo's pre-commit hook (`.githooks/pre-commit`) runs `--check` whenever either file is staged, and `--write` syncs the doc.
- Reverse-link fields (e.g., `usecase.implemented_by:`) are owned by refresh scripts (`refresh_implemented_by.py`) and are recomputed on SessionStart. Do not hand-edit them.
- Forward-link fields (e.g., `task.implements:`, `task.justified_by:`) are user input but path-validated by `validate_frontmatter.py`.
- When adding a new link or status field, add the corresponding script first; do not introduce frontmatter that no script reads or writes.
