# a4 Issue Frontmatter

Issue-side frontmatter rules — every file under `a4/usecase/`, `a4/task/`, `a4/bug/`, `a4/spike/`, `a4/research/`, `a4/umbrella/`, `a4/review/`, `a4/spec/`, `a4/idea/`, `a4/brainstorm/`. Per-type field tables: each `<type>-authoring.md`. Cross-cutting rules shared with wiki pages (`type:`, path-reference format, empty collections, unknown fields) live in `./frontmatter-common.md`.

## `id`

- Ids are **monotonically increasing integers, global to the workspace** — unique across every issue folder in a given `a4/` (GitHub-issue semantics).
- Allocate via the id allocator before writing. **Never invent, never reuse, never re-pack after deletion.** Use the allocated integer as the file's `id:` and as the numeric prefix in the filename (`<id>-<slug>.md`).

  ```bash
  ../scripts/allocate_id.py <absolute path to project's a4/ directory>
  ```

- Wiki pages do **not** carry `id:`.

## Title placeholders

Lifecycle-tracked types whose `title:` graduates from "draft scratch" to "name the project will commit to" forbid placeholder tokens once the file leaves drafting status. Tolerated *only* at the early/drafting status; advancing without replacing them is a post-draft authoring violation.

Forbidden tokens (case-insensitive substring match):

- `TBD`
- `???`
- `<placeholder>`
- `<todo>`
- `TODO:`
- `<title>`-shaped strings (literal `<...>` placeholder text)

Lifecycle gate by type:

| Type | Placeholder allowed at | Forbidden once status reaches |
|------|------------------------|--------------------------------|
| `usecase` | `draft` | `ready` (and beyond — `implementing` / `shipped` / `superseded`) |
| `spec` | `draft` | `active` (and beyond — `deprecated` / `superseded`) |

Other types do not enforce this; their titles may carry placeholder text throughout (in practice, idea / brainstorm / review titles tend to be concrete from the start).

## Relationships

The schema fixes **one direction per relationship** — the forward direction is canonical. Reverse directions are **derived on demand** (grep, script back-scan), not stored. No stored-reverse field currently exists; if a future need arises (status gate, automated check, hot query), a script must own writes for the field and the rationale must be documented here before introduction.

| Forward (stored) | Reverse | Storage |
|------------------|---------|---------|
| `depends_on` | `blocks` | derived |
| `implements` | (UC → tasks) | derived |
| `supersedes` | `superseded_by` | derived |
| `parent` | `children` | derived |
| `target` | (review backlinks; wiki-page backlinks) | derived |
| `promoted` | (idea / brainstorm → promotion-target backlinks) | derived |
| `related` | (symmetric; no reverse) | — |

## Status changes and cascades

Every status change on `usecase`, the four issue families (`task` / `bug` / `spike` / `research`), `review`, and `spec` is **edited directly** on the file. When the change lands, any configured cross-file cascade runs:

- Task reset on UC `revising` — across all four issue families, tasks at `progress`/`failing` → `queued`.
- Task / review discard cascade on UC `discarded` — across all four issue families.
- Supersedes-chain flip on UC `shipped` (predecessor UC: `shipped → superseded`).
- Supersedes-chain flip on spec `active` (predecessor spec: `active|deprecated → superseded`).

The cascade does **not** touch `## Resume` or `## Log` (see `./issue-body.md`) — both are hand-maintained. For cases the cascade cannot mechanically reach (`idea` / `brainstorm` `promoted`), drift between `status:` and supporting cross-references is invalid and reported separately at validation time.

Edge cases:

- **Illegal jumps** (e.g. `shipped → ready`, outside the family's lifecycle) — cascades do not run; validation surfaces the jump as an error (working-tree-vs-HEAD diff against allowed transitions).
- **Legal jumps that bypass the cascade** (edits via `git checkout`, external editors, direct script writes) — related files left unflipped. Validation re-surfaces the missing cascade work for the categories listed above.
- **Recovery** —
  - Supersedes-chain: `../scripts/validate.py --fix` (workspace-wide, idempotent).
  - Reverse-link (revising / discarded cascades): re-edit the UC's `status:` to re-run the cascade.

## Structural relationship fields

Shared across all issue types. Omit empty fields, or use `[]`. `null` (or `~`, or an empty scalar like `parent:` with nothing after the colon) is never valid — see `./frontmatter-common.md` § Empty values.

| Field | Applies to | Points at | Meaning |
|-------|-----------|-----------|---------|
| `depends_on` | task | task | Tasks that must complete before this one (lifecycle blocker) |
| `implements` | task | usecase | Use cases delivered by this task |
| `target` | review | any issue path(s) and/or wiki basename(s) | What this review item is about and which wiki pages must record the resolution; mixed lists allowed |
| `spec` | task (`task` / `bug` only) | spec | Specs that govern this task |
| `supersedes` | spec, usecase | prior spec(s) / usecase(s) | This item replaces the referenced item(s) of the same family |
| `promoted` | idea, brainstorm | spec, usecase, task, brainstorm | Where this item's content graduated to (brainstorm: many ideas → concrete artifacts; idea: one captured thought → concrete artifact) |
| `parent` | any issue except `umbrella` | issue (issue-family children — `task` / `bug` / `spike` / `research` — accept any issue-family parent or `umbrella`; `usecase` / `spec` parents restricted to same-type; `umbrella` itself takes no parent) | Parent in a decomposition / derivation hierarchy or aggregation grouping. Home for narrative shared across siblings — see `./issue-body.md` § `## Log` and `./umbrella-authoring.md`. The child's `parent:` makes the parent discoverable for reverse `children` lookup |
| `related` | any | any | Generic catchall for ties not fitting other fields but warranting frontmatter-level searchability |

Soft references (see-also, mentions) are backtick-wrapped backlinks (`` `../usecase/3-search-history.md` ``) in body prose, not frontmatter.

### `parent` and cross-cutting narrative

`parent` plays two roles, sharing the field:

- **Derivation parent** — `parent` points at the issue this one was spawned from. A `bug` from a `task` may set `parent: task/<id>-<slug>`; a follow-up `task` from a `spike` may set `parent: spike/<id>-<slug>`. Cross-type within the issue family (`task` / `bug` / `spike` / `research`) is allowed.
- **Aggregation parent** — `parent` points at an `umbrella/<id>-<slug>`, a file purpose-built to host shared narrative for several sibling children. See `./umbrella-authoring.md`.

Both forms use the same `parent:` field, so reverse `children` lookups (`grep`, `scripts/search.py --references-via parent`) find every child regardless of parent type.

`usecase` and `spec` use `parent` only in same-type form (UC split, spec supersedes-chain hierarchies). `umbrella` itself takes no parent — nested umbrellas are not supported in this revision.

The parent is the agreed home for **narrative spanning its children** — decisions affecting several siblings, shared approach, cross-sibling trade-offs. That belongs in the parent's `## Log`, not duplicated across each child. See `./issue-body.md#log` for entry format and `./issue-body.md#inline-cross-references-for-cross-cutting-narrative` for the inline cross-reference rule (a child entry depending on a parent decision must inline-cite the parent path so a session reading the child alone can discover the next file to open).

Setting frontmatter `parent:` on a child is what makes the parent discoverable. If a sibling group is meant to share a narrative home, every child must set `parent:` — without it, the parent's `## Log` is unreachable from the child file.
