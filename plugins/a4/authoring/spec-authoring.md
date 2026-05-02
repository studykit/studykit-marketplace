# a4 — spec authoring

A spec at `a4/spec/<id>-<slug>.md` is the **prescriptive implementation contract** for a single artifact — an API shape, schema, protocol, renderer rule, CLI surface, file format, or any other shape downstream code and review items must conform to.

Spec authoring is self-contained. Related artifacts (`usecase/`, `domain.md`, `architecture.md`) are helpful inputs when they exist — link them from `## Context` or `related:` — but they are not prerequisites; a spec can be written when none of them exist yet.

Companion to `./frontmatter-issue.md`, `./issue-body.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: spec
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: <draft | active | deprecated | superseded>
supersedes: []        # list of paths, e.g. [spec/8-caching-strategy]
related: []           # catchall for cross-references — e.g. supporting research tasks
labels: []            # free-form tags (alias: tags)
---
```

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `spec` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | spec title |
| `status` | yes | enum | `draft` \| `active` \| `deprecated` \| `superseded` |
| `supersedes` | no | list of paths | prior specs replaced |
| `related` | no | list of paths | catchall (use this slot for soft cross-references including any informing research task) |
| `labels` | no | list of strings | free-form tags |
| `tags` | no | list of strings | free-form (alias of `labels`; either is accepted) |


- `id:` see `./frontmatter-issue.md` § `id` for the allocator command and contract.
- `title` is required. Placeholder tokens (`TBD`, `???`, `<placeholder>`, `<todo>`, `TODO:`, `<title>`-shaped strings) are tolerated at `status: draft` but forbidden once the spec reaches `status: active` (and beyond) — see `./frontmatter-issue.md#title-placeholders`.
- `supersedes:` lists prior specs this one replaces. The writer cascades `{active|deprecated} → superseded` on the listed targets during the new spec's `→ active` transition. Targets at `draft` are reported as `not-supersedable` and left alone.
- `related:` is the soft-link slot — use it for cross-references between issue-family artifacts, including any `type: research` task that informed this spec (e.g., `related: [research/42-grpc-streaming]`). There is no stored-reverse contract; reverse lookups are derived on demand via grep / `../scripts/search.py`.
- Path values are plain strings without `.md` and without brackets (e.g., `spec/8-caching-strategy`, not `[spec/8-caching-strategy.md]`).

### Lifecycle and writer ownership

```
draft      → active | deprecated
active     → deprecated | superseded
deprecated → superseded
superseded → (terminal)
```

- Edit `status:` directly. The transition refreshes `updated:` automatically and runs any cross-file cascade.
- `draft → superseded` is **disallowed** — supersession presumes the predecessor was at one point live.
- `active → superseded` is **automatic** — it fires when a successor spec with `supersedes: [<this>]` reaches `active`. Do not flip it by hand.
- `deprecated` is opt-in retirement, valid even before a successor exists. There is **no reverse path** from `deprecated → active`; author a new spec (with `supersedes:` pointing back) to revive the shape.

## Body shape

The body is a sequence of column-0 H2 markdown headings in Title Case (e.g., `## Context`, `## Specification`), with markdown content following each heading until the next H2 or end of file. H1 (`# Title`) is forbidden in the body — title belongs to frontmatter `title:`. Use H3+ headings inside sections freely.

**Required:**

- `## Context` — why this spec exists; what artifact it describes; the scope it covers.
- `## Specification` — the prescriptive content. Grammar, fields, format rules, examples. This is the heart of the spec.

**Optional content sections, emit only when there is content:**

- `## Open Questions` — unresolved aspects the spec deliberately defers. Better than forcing premature closure.
- `## Consequences` — downstream effects (positive, negative, or neutral) the spec creates for code, tooling, or operations.
- `## Examples` — concrete cases that pin down the prescriptive rules.
- `## Resume` — current-state snapshot for the next session: current approach, current blocker, open questions, next step. Freely rewritten as work progresses. Strongly recommended while the spec is at `draft` (the only mid-flight state — `active` is a stable contract, not in-flight). See `./issue-body.md#resume`.
- `## Log` — append-only narrative of meaningful events that have shaped this spec (blocker resolutions, approach changes worth remembering). Do not duplicate `## Resume` content here. See `./issue-body.md#log`.

**Optional appendum sections (record-keeping; emit only when there is content):**

- `## Decision Log` — append-only, dated bullets recording what was chosen and why, kept as a reference for future readers. Earlier entries are never edited or removed; corrections are added as new entries that explain why prior reasoning no longer holds. Inline markdown links (e.g., `[research/42-grpc-streaming](../research/42-grpc-streaming.md)`) cite informing research tasks.
- `## Rejected Alternatives` — the options considered and why they lost. Inline citations to research tasks land here too when the rejection rationale leans on the investigation.

Unknown H2 headings are tolerated (`## Benchmarks`, `## Migration Notes`, etc.). A `## Migration Plan` section is **not** used — migration work belongs in a task file under one of the issue family folders (`a4/task/`, `a4/bug/`, etc.).

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained. Frontmatter list paths are different (plain strings, no `.md`).

## Common mistakes

- **Stray content above the first H2 heading.** Anything in the body that is not whitespace must live under an H2 heading.
- **`## Context` or `## Specification` missing.** Both are required; the `→ active` flip is invalid until they are present and non-empty.
- **H2 not in column 0 or not Title Case.** Section boundaries fire only on column-0 H2 headings whose text is Title Case with single-space separators.
- **Sections nested inside other sections.** Sections do not nest; every section sits at the body's top level. Use H3+ for inner structure.
- **H1 in body.** Title is frontmatter-only.

## Don't

- **Don't auto-populate `supersedes:`.** It is an explicit user decision in the authoring conversation.
- **Don't edit a prior spec's body to mark it superseded.** Supersession is captured in the *new* spec's frontmatter `supersedes:`; the prior spec's status flips automatically when the successor reaches `active`.
- **Don't pack multiple distinct artifacts into one spec.** One artifact per spec — one OpenAPI document, one schema, one protocol. Multiple artifacts → multiple specs, each with its own id and supersede chain.
- **Don't let the spec body absorb other concerns.** `## Specification` is the prescriptive shape only. User flows, domain glossaries, and runtime component layouts have their own homes (`usecase/`, `domain.md`, `architecture.md`) — write them there when those artifacts exist, and omit them from the spec when they don't, rather than letting the spec absorb them.
- **Don't author a spec for routine choices.** Variable names, folder layout, formatting belong in style guides or simply in the code — not in spec.
- **Don't introduce a separate `decisions/` slot.** When recorded, decision rationale lives in the spec body's `## Decision Log` appendum.
