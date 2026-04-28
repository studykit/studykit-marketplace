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
    spec/<id>-<slug>.md        # Living specifications (status: draft | active | deprecated | superseded)
    review/<id>-<slug>.md      # Findings / gaps / questions (kind: finding | gap | question)
    idea/<id>-<slug>.md        # Pre-pipeline quick-capture
    spark/<YYYY-MM-DD-HHmm>-<slug>.brainstorm.md
    archive/                   # Closed items; folder = archived flag

  spike/<task-id>-<slug>/      # PoC code for kind: spike tasks (sibling of a4/)
  research/<slug>.md           # Portable research artifacts (sibling of a4/, referenced by specs)
```

**Conventions**:

- **Global monotonic ids.** `id` is unique across the entire workspace (GitHub-issue semantics). Allocated by `scripts/allocate_id.py`.
- **Filenames.** `<id>-<slug>.md`. Folder indicates type — no `uc-` / `task-` prefix.
- **Wiki updates flow through review items.** Wiki pages have no lifecycle but change continuously; edits are nudged by single-edit skills, deferred via `kind: gap` review items, and reconciled by the drift detector. The `<change-logs>` section on each wiki page records causes (dated bullets with markdown links to the causing issue).
- **Tagged-XML body format.** Each file declares `type:` in frontmatter matching its body root tag; sections are column-0 `<tag>...</tag>` blocks (lowercase, kebab-case) with markdown content. Body links are standard markdown `[text](relative/path.md)`. Frontmatter list paths stay plain strings without `.md`.

## Two `spec/` layers — do not confuse them

The word "spec" appears at two layers:

- **`<project-root>/a4/spec/`** (workspace) — 1st-class issue family. Living specifications about the *user's product* (formats, protocols, schemas, renderer rules, CLI surfaces). Authored by `/a4:spec`, governed by the frontmatter contract, status-managed by `transition_status.py`. This is what end users produce when running a4.
- **`plugins/a4/spec/`** (plugin meta-design) — Design notes about the **a4 plugin itself** (skill split, schema choices, hook architecture). Plain markdown, not validated by a4 scripts, not reachable by user-project skills. Active records live directly in `plugins/a4/spec/`.

The two layers share a name on purpose (a4 dogfoods its own spec-first model on itself), but they live in different roots and obey different rules. When this document or any reference says "spec" without qualification, **assume the workspace layer** unless the surrounding context is plugin-internal.

ADRs are retired at both layers — workspace decisions live inside spec bodies (free-form `## Decision Log` notes); plugin meta-design decisions live as plain spec/decision notes under `plugins/a4/spec/`.

## References — read before editing

Reference docs in `plugins/a4/references/` are the authoritative source for cross-cutting concerns. Read the relevant one before changing any skill/script that touches it:

- `frontmatter-schema.md` — frontmatter contract (also required by root CLAUDE.md)
- `body-conventions.md` — body tag form, `<change-logs>` / `<log>` rules, link form
- `pipeline-shapes.md` — Full / Reverse-engineer / Minimal / No-shape; read before changing shape-aware skills (`auto-bootstrap`, `run`, `compass`)
- `skill-modes.md` — interactive vs autonomous, forward vs reverse axes
- `wiki-authorship.md` — who can write each wiki page; cross-stage feedback policy
- `spec-triggers.md` — when a spec is warranted
- `iterate-mechanics.md` — iterate-mode contract for skills
- `hook-conventions.md` — hook contract

## Per-section reads and path-scoped rules

- `scripts/extract_section.py` reads one section out of an a4 file
  without loading the whole markdown. Modes: `<file> <tag>`,
  `<file> --list`, `<file> <tag> --json`. It reuses the fence-aware
  scanner from `validate_body.py`, so outline-shaped tags inside fenced
  code blocks are not mistaken for section boundaries.
- `rules/` ships path-scoped rule files (`paths:` frontmatter). They do
  **not** auto-load in user projects until explicitly installed via the
  `/a4:install-rules` slash command, which symlinks each rule file into
  `<project-root>/.claude/rules/`. `/a4:uninstall-rules` removes only
  the plugin-sourced symlinks. Symlinks (not copies) so plugin updates
  propagate.
- `rules/a4-section-enum.md` is generator-owned. Its bullet block lives
  between `<!-- BEGIN section-enum -->` / `<!-- END section-enum -->`
  markers and is rewritten by `scripts/generate_section_enum.py`. The
  pre-commit hook re-checks for drift whenever any
  `scripts/body_schemas/*.xsd` or the rule file is staged.
- `rules/a4-workspace-policies.md` is the **cross-cutting baseline**
  rule (`paths: ["a4/**/*.md"]`). It auto-loads on any a4 file Read
  and consolidates the policies that apply uniformly: writer-owned
  fields (`status:` / `updated:` / `<log>` / reverse-links), id
  allocation, frontmatter path form vs body link form, body tag form,
  `<change-logs>` discipline, primary-author boundary + cross-stage
  stop/continue, iterate-flow writer mechanics, and the `#<id>`
  commit-subject form. Per-type rules build on top — they do not
  redefine these policies.
- `rules/a4-<type>-authoring.md` files are hand-edited per-type
  authoring guides. Two flavors share the shape:
  - **Issue-family rules** scope to `a4/<type>/**/*.md` (folder glob).
    They consolidate the schema, lifecycle, body shape, and "do not"
    rules for one issue family. Current instances:
    `a4-spec-authoring.md`, `a4-task-authoring.md`,
    `a4-usecase-authoring.md`, `a4-review-authoring.md`.
  - **Wiki-page rules** scope to a single file path
    (`a4/<basename>.md`). Wiki pages have no id / status / lifecycle,
    so the rule focuses on the authorship table from
    `references/wiki-authorship.md` (primary author, in-situ
    allowances), the `<change-logs>` discipline, and what each section
    must / must not contain. Current instances:
    `a4-architecture-authoring.md`, `a4-context-authoring.md`,
    `a4-domain-authoring.md`, `a4-actors-authoring.md`,
    `a4-nfr-authoring.md`, `a4-roadmap-authoring.md`,
    `a4-bootstrap-authoring.md`.

  Both flavors have no generator backing and no pre-commit drift
  check; they are normal prose that must be revised by hand when the
  source schemas, skills, or `wiki-authorship.md` change. Add new
  ones for other types or wiki pages by copying the shape. Per-type
  rules should defer cross-cutting items to `a4-workspace-policies.md`
  rather than re-stating them, so policy changes flow through one
  file.

## Subagents do not auto-inherit project-level rules

Per the official subagent docs: "Subagents receive only this system
prompt (plus basic environment details), not the full Claude Code
system prompt", and "Subagents don't inherit skills from the parent
conversation". The same applies to path-scoped rules from
`.claude/rules/` — they may not auto-load when a subagent reads
matching files.

a4 subagents that author or emit a4 files therefore include an
"Authoring contracts" section near the top of their system prompt
body that explicitly directs them to read the relevant rule files at
startup. Subagents currently carrying that section:

- **Authors / revisers** (write a4 issue + wiki files):
  `usecase-composer`, `usecase-reviser`.
- **Reviewers** (emit `kind: finding | gap | question` review items):
  `usecase-reviewer`, `arch-reviewer`, `domain-reviewer`,
  `roadmap-reviewer`.
- **Implementer / runner** (write code + emit reviews + commit with
  `#<id>` form): `task-implementer`, `test-runner`.

Other agents (`api-researcher`, `mock-html-generator`,
`research-reviewer`, `usecase-explorer`, `workspace-assistant`) do not
write a4 issue files in normal operation and currently do not embed
the authoring-contracts section. Add the section if a future change
broadens an agent's responsibilities to issue authorship.

## Skill-generated frontmatter is script-managed

Frontmatter on files written by a4 skills (under `<project-root>/a4/`) is the responsibility of scripts in `plugins/a4/scripts/`, not hand edits. This keeps cross-file consistency and reverse-links intact.

- Status transitions go through `transition_status.py`. Skills never write `status:` directly after the initial create.
- Status enums, transitions, and terminal/in-progress sets live in `scripts/status_model.py` — the canonical model imported by the writer, validators, workspace state, and search. Add new status values there first; consumers pick them up automatically. The ASCII transition diagrams in `references/frontmatter-schema.md` are generated from this module by `scripts/generate_status_diagrams.py`; the repo's pre-commit hook (`.githooks/pre-commit`) runs `--check` whenever either file is staged, and `--write` syncs the doc.
- Reverse-link fields (e.g., `usecase.implemented_by:`) are owned by refresh scripts (`refresh_implemented_by.py`) and are recomputed on SessionStart. Do not hand-edit them.
- Forward-link fields (e.g., `task.implements:`, `task.spec:`) are user input but path-validated by `validate_frontmatter.py`.
- When adding a new link or status field, add the corresponding script first; do not introduce frontmatter that no script reads or writes.
