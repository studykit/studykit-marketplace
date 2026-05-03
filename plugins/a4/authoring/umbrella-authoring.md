# a4 — umbrella authoring

An umbrella at `a4/umbrella/<id>-<slug>.md` is a **narrative-aggregation parent** — a file purpose-built to host the cross-cutting narrative that several issue-family children (`task` / `bug` / `spike` / `research`) share. It is *not* an implementation unit: an umbrella has no `## Change Plan`, no `## Unit Test Strategy`, no per-cycle implement loop. The work is done by its children; the umbrella exists so the next session reading any one child can discover the shared decisions through that child's `parent:` pointer.

Companion to `./frontmatter-issue.md`, `./issue-body.md`. Narrative-home semantics (entry format, inline cross-references): `./issue-body.md#log`. The `parent:` discovery contract: `./frontmatter-issue.md` § `parent` and shared narrative.

## When to create an umbrella

Create one when at least one of the following holds:

- **Pre-decomposition** — A larger piece of work is going to be split into ≥ 2 children before any child is written. Author the umbrella first; subsequent children carry `parent: umbrella/<id>-<slug>` from creation.
- **Retroactive aggregation** — ≥ 2 sibling issues already exist and a cross-cutting decision has come up that affects more than one of them. At the moment that decision needs a recorded home, create the umbrella, set each affected child's `parent:` to it, and record the decision in the umbrella's `## Log`.
- **Repeated cross-cutting decisions** — When the cross-cutting narrative is no longer a one-off (≥ 2 distinct decisions affect the same sibling group), prefer an umbrella over duplicating notes in each child's `## Log`.

Do **not** create an umbrella when:

- A single child is enough — no aggregation. The child's own `## Log` is sufficient.
- Sibling children exist but are genuinely unrelated. No shared narrative to home.
- Two siblings + one cross-cutting decision. Borderline — recording the decision inline once in each child (with cross-reference per `./issue-body.md#inline-cross-references-for-cross-cutting-narrative`) is acceptable; promote to an umbrella when a second decision arrives.

Derivation parents (a follow-up `task` whose `parent:` is the originating `spike`, a `bug` spawned from a `task`) are a different mechanism — those use another issue-family file as parent and do not need an umbrella. Umbrella exists for *aggregation*, not *derivation*.

## Frontmatter contract (do not deviate)

```yaml
---
type: umbrella
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: open | complete | discarded
related: []            # catchall for cross-references
labels: []             # free-form tags
---
```

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `umbrella` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `open` \| `complete` \| `discarded` |
| `related` | no | list of paths | catchall cross-references |
| `labels` | no | list of strings | free-form tags |


`implements` / `spec` / `depends_on` / `artifacts` / `cycle` / `parent` are **forbidden** on umbrella — declaring any is an error:

- `implements` / `spec` — children carry these forward anchors; the umbrella does not deliver UCs or follow specs directly. If children all implement the same UC, that's already visible from each child's `implements:`.
- `depends_on` — sequencing belongs to children.
- `artifacts` — umbrellas hold no artifact directory. Per-child artifacts use `artifacts/<type>/<child-id>-<child-slug>/`.
- `cycle` — umbrellas have no implement loop. Children carry their own cycles.
- `parent` — nested umbrellas are not supported in this revision. Each umbrella is top-level aggregation.

- `title` required and must not be a placeholder; `<title>`-shaped strings are invalid.
- `type: umbrella` is fixed for files under `a4/umbrella/`.
- `id:` see `./frontmatter-issue.md` § `id`.

### Lifecycle

| Status | Meaning | Allowed transitions |
|--------|---------|---------------------|
| `open` | Active narrative home for at least one mid-flight child | → `complete`, → `discarded` |
| `complete` | Author judges the umbrella's purpose fulfilled — usually after all relevant children reach `complete` and the integration outcome is met | → `open` (re-open if work resumes), → `discarded` |
| `discarded` | The umbrella is no longer the right grouping (children moved under a different parent or stand alone). Write `## Why Discarded` |  — (terminal) |

`complete` is **author-judged** — no automatic cascade from child status. The author flips `status:` directly when the integration outcome is met. If a single child remains mid-flight, prefer keeping the umbrella `open`.

When all children are `complete` or `discarded` and the umbrella is still `open`, the workspace state is mildly inconsistent but not an error — the author may have intentionally left the umbrella open for further follow-up children.

Direct edits refresh `updated:` automatically, but no automatic cascade flips umbrella status based on children. There is no umbrella-driven cascade onto children either: discarding an umbrella does not discard its children. If the children should also be discarded, flip them individually.

## Body shape

**Required:**

- `## Description` — what the children together accomplish. Brief — one or two paragraphs. Link the children inline by markdown link when narratively useful.
- `## Children` — explicit append-only list of child paths as markdown links, one bullet per child. The reverse-`parent:` lookup remains the authoritative membership; this section exists so a human reader sees the membership at a glance.

  ```markdown
  ## Children

  - [task/17-search-history](../task/17-search-history.md)
  - [task/18-search-pagination](../task/18-search-pagination.md)
  - [bug/9-cache-key-collision](../bug/9-cache-key-collision.md)
  ```

  Order is the order in which children were added (chronological). When a child is later discarded or moves under a different parent, leave the bullet but annotate (`— moved to umbrella/22-...`, `— discarded 2026-05-08`) — append-only history beats silent deletion.

- `## Log` — the aggregation narrative. **This is the umbrella's reason for existing.** Format and inline cross-reference rules per `./issue-body.md#log`. Decisions recorded here are the *source* that children inline-cite from their own `## Log` entries.

**Optional, emit only when applicable:**

- `## Acceptance Criteria` — integration outcome that is not naturally any single child's AC. Skip when implicit ("all children deliver and tests pass"). Use it when the umbrella has its own observable (e.g., "search-history feature works end-to-end across UC 3 and UC 7").
- `## Resume` — current-state snapshot. Strongly recommended while at `open` (the only mid-flight state). See `./issue-body.md#resume`.
- `## Why Discarded` — populated on `discarded`. Dated bullet (`<YYYY-MM-DD> — <reason text>`).

Unknown H2 headings are tolerated.

## Authoring children that point at an umbrella

Set the child's frontmatter `parent: umbrella/<id>-<slug>` at creation (or as soon as the umbrella exists). Without this, the umbrella is unreachable from the child file.

When the child writes a `## Resume` or `## Log` entry that depends on the umbrella's narrative, inline-cite the umbrella path inside the entry per `./issue-body.md#inline-cross-references-for-cross-cutting-narrative`:

```markdown
## Log

- Approach: follow the caching strategy decided in [umbrella/5-search](../umbrella/5-search.md) `## Log`. This child only diverges on test-fixture shape.
```

Frontmatter `parent:` makes the umbrella *discoverable*; the inline citation makes it *necessary to read* — only when the entry actually depends on it. Self-contained child entries need no cross-reference.

## Common mistakes

- **Required section missing** (`## Description`, `## Children`, `## Log`).
- **Children listed only via reverse-`parent:`** — emit the body `## Children` section as the human-readable index.
- **Forbidden field set** (`implements`, `spec`, `depends_on`, `artifacts`, `cycle`, `parent`) — declaring any is invalid. Move the field to the children where it belongs.
- **Wrong folder** — umbrella files must live under `a4/umbrella/`. A `type: umbrella` file outside that folder is a routing error.

## Don't

- **Don't author implementation in the umbrella.** No `## Change Plan`, no `## Unit Test Strategy`. The work belongs to children.
- **Don't treat the umbrella as a decision document.** Long-lived design decisions belong in `spec/`. The umbrella's `## Log` carries *implementation-progress narrative* that spans children.
- **Don't nest umbrellas.** `parent:` on an umbrella is forbidden in this revision.
- **Don't delete an umbrella after its purpose ends.** Flip to `complete` or `discarded` and let the file stay; reverse `parent:` lookups from children remain valid.
- **Don't duplicate the umbrella's narrative across children.** That defeats the point. Each child's `## Log` carries only what is local to that child plus inline citations to the umbrella when they share a decision.
