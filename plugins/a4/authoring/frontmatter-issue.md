# a4 Issue Frontmatter

Issue-side frontmatter rules — applies to every file under `a4/usecase/`, `a4/task/`, `a4/bug/`, `a4/spike/`, `a4/research/`, `a4/umbrella/`, `a4/review/`, `a4/spec/`, `a4/idea/`, `a4/brainstorm/`. Per-type field tables live in each `<type>-authoring.md`. Cross-cutting rules shared with wiki pages (`type:`, path-reference format, empty collections, unknown fields) live in `./frontmatter-common.md`. Universal common fields (`created`, `updated`) live in `./frontmatter-common.md`.

## `id`

- Ids are **monotonically increasing integers, global to the workspace** — unique across every issue folder in a given `a4/` (GitHub-issue semantics).
- Allocate via the id allocator before writing a new issue file. **Never invent, never reuse, never re-pack after deletion.** Use the allocated integer as the file's `id:` and as the numeric prefix in the filename (`<id>-<slug>.md`).

  ```bash
  uv run ../scripts/allocate_id.py <absolute path to project's a4/ directory>
  ```

- Wiki pages do **not** carry an `id:` field — they have no issue-tracker identity.

## Title placeholders

Lifecycle-tracked types whose `title:` graduates from "draft scratch text" to "name the project will commit to" forbid placeholder tokens once the file leaves its drafting status. Placeholders are tolerated *only* at the early/drafting status; advancing the lifecycle without replacing them is a post-draft authoring violation.

Forbidden placeholder tokens (case-insensitive substring match):

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

Other types do not enforce this rule; their titles may carry placeholder text throughout their lifecycle if the author chooses (in practice, idea / brainstorm / review titles tend to be concrete from the start).

## Relationships

The schema fixes **one direction per relationship** — the forward direction is the canonical source. Reverse directions are **derived on demand** (grep, script back-scan) rather than stored. There is currently no stored-reverse field; if a future need arises (a status gate, automated check, or hot query that justifies bypassing derive-on-demand), a script must own writes for the field and the rationale must be documented here before the field is introduced.

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

Every status change on `usecase`, the four issue families (`task` / `bug` / `spike` / `research`), `review`, and `spec` files is **edited directly** on the file. When the change lands, `updated:` refreshes automatically on the primary file, and any cross-file cascade runs:

- Task reset on UC `revising` — across all four issue families, tasks at `progress`/`failing` → `queued`.
- Task / review discard cascade on UC `discarded` — across all four issue families.
- Supersedes-chain flip on UC `shipped` (predecessor UC: `shipped → superseded`).
- Supersedes-chain flip on spec `active` (predecessor spec: `active|deprecated → superseded`).

The automatic cascade does **not** touch the body's optional `## Resume` or `## Log` sections (see `./issue-body.md`) — both are hand-maintained when an author wants a body-level resume snapshot or audit trail. For cases the cascade cannot mechanically reach (`idea` / `brainstorm` `promoted`), drift between `status:` and the supporting cross-references is invalid and is reported separately at validation time.

Edge cases:

- **Illegal jumps** (e.g. `shipped → ready`, outside the family's lifecycle table) — `updated:` and cross-file cascades do not run; validation surfaces the jump as an error (working-tree-vs-HEAD diff against the family's allowed transitions).
- **Legal jumps that bypass the automatic cascade** (edits via `git checkout`, external editors, direct script writes) — related files are left unflipped. Validation re-surfaces the missing cascade work for the categories listed above (`task.queued` revising cascade, `task.discarded` cascade, `review.discarded` cascade, supersedes chain).
- **Recovery** —
  - Supersedes-chain: `../scripts/validate.py --fix` (workspace-wide, idempotent).
  - Reverse-link (revising / discarded cascades): re-edit the UC's `status:` to re-run the automatic cascade.

## Structural relationship fields

Shared across all issue types. Omit fields that are empty, or use `[]`.

| Field | Applies to | Points at | Meaning |
|-------|-----------|-----------|---------|
| `depends_on` | task | task | Tasks that must complete before this one (lifecycle blocker) |
| `implements` | task | usecase | Use cases delivered by this task |
| `target` | review | any issue path(s) and/or wiki basename(s) | What this review item is about and which wiki pages must record the resolution; mixed lists are allowed |
| `spec` | task (`task` / `bug` only) | spec | Specs that govern this task |
| `supersedes` | spec, usecase | prior spec(s) / usecase(s) | This item replaces the referenced item(s) of the same family |
| `promoted` | idea, brainstorm | spec, usecase, task, brainstorm | Where this item's content graduated to (brainstorm: one-to-many ideas grow into concrete artifacts; idea: a single captured thought becomes a concrete artifact) |
| `parent` | any issue except `umbrella` | issue (issue-family children — `task` / `bug` / `spike` / `research` — accept any issue-family parent or an `umbrella` parent; `usecase` and `spec` parents are restricted to same-type; `umbrella` itself takes no parent) | Parent in a decomposition / derivation hierarchy or aggregation grouping. Used as the home for narrative shared across siblings — see `./issue-body.md` § `## Log` and `./umbrella-authoring.md`. When set, the child's frontmatter `parent:` is what makes the parent discoverable for reverse `children` lookup |
| `related` | any | any | Generic catchall for ties that don't fit other fields but warrant frontmatter-level searchability |

Soft references (see-also, mentions) are expressed as standard markdown links (`[text](relative/path.md)`) in body prose, not frontmatter.

### `parent` and cross-cutting narrative

`parent` plays two roles, and they share the field:

- **Derivation parent** — `parent` points at the issue this one was spawned from. A `bug` surfaced by a `task` may set `parent: task/<id>-<slug>`, a follow-up `task` produced by a `spike` may set `parent: spike/<id>-<slug>`. Cross-type within the issue family (`task` / `bug` / `spike` / `research`) is allowed.
- **Aggregation parent** — `parent` points at an `umbrella/<id>-<slug>`, a file purpose-built to host the shared narrative for several sibling children. See `./umbrella-authoring.md` for when to create an umbrella vs. when not to.

Both forms use the same `parent:` field, so reverse `children` lookups (`grep`, `scripts/search.py --references-via parent`) find every child regardless of whether the parent is another issue or an umbrella.

`usecase` and `spec` use `parent` only in same-type form (UC split, spec supersedes-chain hierarchies). `umbrella` itself takes no parent — nested umbrellas are not supported in this revision.

The parent file is the agreed home for **narrative that spans its children** — decisions that affect several siblings together, shared approach, cross-sibling trade-offs. That narrative belongs in the parent's `## Log`, not duplicated across each child. See `./issue-body.md#log` for the entry format and `./issue-body.md#inline-cross-references-for-cross-cutting-narrative` for the inline cross-reference rule (a child `## Resume` or `## Log` entry that depends on a decision recorded in the parent must inline-cite the parent path so a session reading the child file alone can discover the next file to open).

Setting frontmatter `parent:` on a child is what makes the parent discoverable. If a sibling group is meant to share a narrative home, every child must set `parent:` — without it, the parent's `## Log` is unreachable from the child file.
