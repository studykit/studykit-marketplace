# a4 — epic authoring

An epic at `a4/epic/<id>-<slug>.md` is a **multi-issue coordination parent** for a larger goal delivered by multiple child issues (`task` / `bug` / `spike` / `research`).

An epic may represent a user-facing feature, platform capability, subsystem implementation effort, migration, stabilization campaign, or cross-cutting quality initiative. It is *not* an implementation unit: an epic has no `## Change Plan`, no `## Unit Test Strategy`, no per-cycle implement loop. The work is done by its children.

The epic coordinates the child set by recording membership, optional integration-level acceptance criteria, current coordination state, and the shared narrative that spans multiple children. **Epic coordinates work; it does not define the product, architecture, or implementation contract.** User-facing behavior belongs in `usecase/`, implementation contracts in `spec/`, component shape in `architecture.md`, vocabulary in `domain.md`, and non-functional requirements in `nfr.md`.

Companion to `./frontmatter-issue.md`, `./issue-body.md`. Shared narrative semantics (entry format, inline cross-references): `./issue-body.md#log`. The `parent:` discovery contract: `./frontmatter-issue.md` § `parent` and shared narrative.

## When to create an epic

Create one when at least one of the following holds:

- **Pre-decomposition** — A larger piece of work is going to be split into ≥ 2 children before any child is written. Author the epic first; subsequent children carry `parent: epic/<id>-<slug>` from creation.
- **Retroactive coordination** — ≥ 2 sibling issues already exist and a cross-cutting decision has come up that affects more than one of them. At the moment that decision needs a recorded home, create the epic, set each affected child's `parent:` to it, and record the decision in the epic's `## Log`.
- **Repeated cross-cutting decisions** — When the cross-cutting narrative is no longer a one-off (≥ 2 distinct decisions affect the same sibling group), prefer an epic over duplicating notes in each child's `## Log`.

Do **not** create an epic when:

- A single child is enough — no coordination parent. The child's own `## Log` is sufficient.
- Sibling children exist but are genuinely unrelated. No shared narrative to home.
- Two siblings + one cross-cutting decision. Borderline — recording the decision inline once in each child (with cross-reference per `./issue-body.md#inline-cross-references-for-cross-cutting-narrative`) is acceptable; promote to an epic when a second decision arrives.

Derivation parents (a follow-up `task` whose `parent:` is the originating `spike`, a `bug` spawned from a `task`) are a different mechanism — those use another issue-family file as parent and do not need an epic. Epic exists for *coordination*, not *derivation*.

## Frontmatter contract (do not deviate)

```yaml
---
type: epic
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: open | done | discarded
related: []            # catchall for cross-references
labels: []             # free-form tags
---
```

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `epic` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `open` \| `done` \| `discarded` |
| `related` | no | list of paths | catchall cross-references |
| `labels` | no | list of strings | free-form tags |


`implements` / `spec` / `depends_on` / `artifacts` / `cycle` / `parent` are **forbidden** on epic — declaring any is an error:

- `implements` / `spec` — children carry these forward anchors; the epic does not deliver UCs or follow specs directly. If children all implement the same UC, that's already visible from each child's `implements:`.
- `depends_on` — sequencing belongs to children.
- `artifacts` — epics hold no artifact directory. Per-child artifacts use `artifacts/<type>/<child-id>-<child-slug>/`.
- `cycle` — epics have no implement loop. Children carry their own cycles.
- `parent` — nested epics are not supported in this revision. Each epic is a top-level coordination parent.

- `title` required and must not be a placeholder; `<title>`-shaped strings are invalid.
- `type: epic` is fixed for files under `a4/epic/`.
- `id:` see `./frontmatter-issue.md` § `id`.

### Lifecycle

| Status | Meaning | Allowed transitions |
|--------|---------|---------------------|
| `open` | Active coordination home for at least one mid-flight child | → `done`, → `discarded` |
| `done` | Author judges the epic's purpose fulfilled — usually after all relevant children reach `done` and the integration outcome is met | → `open` (re-open if work resumes), → `discarded` |
| `discarded` | The epic is no longer the right grouping (children moved under a different parent or stand alone). Write `## Why Discarded` |  — (terminal) |

`done` is **author-judged** — no automatic cascade from child status. The author flips `status:` directly when the integration outcome is met. If a single child remains mid-flight, prefer keeping the epic `open`.

When all children are `done` or `discarded` and the epic is still `open`, the workspace state is mildly inconsistent but not an error — the author may have intentionally left the epic open for further follow-up children.

No automatic cascade flips epic status based on children. There is no epic-driven cascade onto children either: discarding an epic does not discard its children. If the children should also be discarded, flip them individually.

## Body shape

**Required:**

- `## Description` — what the children together accomplish. Brief — one or two paragraphs. Link the children inline by backlink when narratively useful.
- `## Children` — explicit append-only list of child paths as timestamped backlink bullets, one bullet per child. Bullet form per `./body-conventions.md` § Bullet backlink. The reverse-`parent:` lookup remains the authoritative membership; this section exists so a human reader sees the membership at a glance.

  ```markdown
  ## Children

  - 2026-04-23 09:14 `../task/17-search-history.md`
  - 2026-04-25 14:02 `../task/18-search-pagination.md`
  - 2026-05-01 11:30 `../bug/9-cache-key-collision.md`
  ```

  Order is the order in which children were added (chronological). When a child is later discarded or moves under a different parent, leave the bullet but annotate (`— moved to epic/22-...`, `— discarded 2026-05-08 14:32`) — append-only history beats silent deletion.

- `## Log` — the shared coordination narrative. This is the epic's shared narrative contract: decisions, pivots, blockers, integration constraints, and cross-child trade-offs that span multiple children. Format and inline cross-reference rules per `./issue-body.md#log`. Decisions recorded here are the *source* that children inline-cite from their own `## Log` entries.

**Optional, emit only when applicable:**

- `## Acceptance Criteria` — integration outcome that is not naturally any single child's AC. Skip when implicit ("all children deliver and tests pass"). Use it when the epic has its own observable (e.g., "search-history feature works end-to-end across UC 3 and UC 7").
- `## Resume` — current-state snapshot. Strongly recommended while at `open` (the only mid-flight state). See `./issue-body.md#resume`.
- `## Why Discarded` — populated on `discarded`. Format: `./issue-body.md` § `## Why Discarded`.

Unknown H2 headings are tolerated.

## Authoring children that point at an epic

Set the child's frontmatter `parent: epic/<id>-<slug>` at creation (or as soon as the epic exists). Without this, the epic is unreachable from the child file.

When the child writes a `## Resume` or `## Log` entry that depends on the epic's narrative, inline-cite the epic path inside the entry per `./issue-body.md#inline-cross-references-for-cross-cutting-narrative`:

```markdown
## Log

- Approach: follow the caching strategy decided in `../epic/5-search.md` `## Log`. This child only diverges on test-fixture shape.
```

Frontmatter `parent:` makes the epic *discoverable*; the inline citation makes it *necessary to read* — only when the entry actually depends on it. Self-contained child entries need no cross-reference.

## Common mistakes

- **Required section missing** (`## Description`, `## Children`, `## Log`).
- **Children listed only via reverse-`parent:`** — emit the body `## Children` section as the human-readable index.
- **Forbidden field set** (`implements`, `spec`, `depends_on`, `artifacts`, `cycle`, `parent`) — declaring any is invalid. Move the field to the children where it belongs.
- **Wrong folder** — epic files must live under `a4/epic/`. A `type: epic` file outside that folder is a routing error.

## Don't

- **Don't author implementation in the epic.** No `## Change Plan`, no `## Unit Test Strategy`. The work belongs to children.
- **Don't treat the epic as a decision document.** Long-lived design decisions belong in `spec/`. The epic's `## Log` carries shared coordination narrative that spans children.
- **Don't nest epics.** `parent:` on an epic is forbidden in this revision.
- **Don't delete an epic after its purpose ends.** Flip to `done` or `discarded` and let the file stay; reverse `parent:` lookups from children remain valid.
- **Don't duplicate the epic's narrative across children.** That defeats the point. Each child's `## Log` carries only what is local to that child plus inline citations to the epic when they share a decision.
