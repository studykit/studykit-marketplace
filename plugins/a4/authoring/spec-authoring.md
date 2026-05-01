# a4 — spec authoring

> **Audience:** Workspace authors writing `<project-root>/a4/**/*.md` files (or LLMs editing them on the user's behalf). Not for a4 plugin contributors — implementation references live in `../dev/`.

A spec at `a4/spec/<id>-<slug>.md` is a **living, prescriptive specification** of an artifact the project commits to — a format, protocol, schema, renderer rule, CLI surface, or any shape downstream code and review items must conform to. Design rationale for the chosen shape lives inline as `## Decision Log` entries in the same file.

Companion to `./frontmatter-universals.md`, `./body-conventions.md`.

## When a spec is warranted

A moment is spec-worthy when **all** of these hold:

- **Multiple viable options exist** — not forced by the framework, the stack, or a hard constraint.
- **The trade-off is non-trivial** — picking option A vs B changes downstream effort, surface area, or cost meaningfully.
- **It is non-recoverable from code alone** — the *why* lives outside the codebase; reading code later would not reveal it.
- **It is plausibly revisitable** — future evidence could justify superseding it.

If any condition fails, the moment is probably **not** spec-worthy. See the anti-patterns below.

### Anti-patterns — do **not** author a spec for these

- **Routine choices.** Variable names, folder layout, code formatting. Belongs in style guides or simply in the code.
- **Framework-mandated.** No alternative exists within the chosen stack — there is no decision to record.
- **Post-hoc justification.** Code is already written and the conversation is just explaining what is there. Specs are decisions; if no decision remains, do not retroactively author one.
- **Multiple decisions in one spec.** Three independent decisions → three specs, each with its own `## Decision Log` and supersede chain.
- **Bug fixes that just use the right tool.** Switching to the correct API call is a fix, not a decision.

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
created: YYYY-MM-DD
updated: YYYY-MM-DD
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
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | no | date | `YYYY-MM-DD` (bump when the spec is revised) |

- `id` is allocated by the id allocator (workspace-global, monotonic). Never invent or reuse an id.
- `title` is required. Placeholder tokens (`TBD`, `???`, `<placeholder>`, `<todo>`, `TODO:`, `<title>`-shaped strings) are tolerated at `status: draft` but forbidden once the spec reaches `status: active` (and beyond) — see `./frontmatter-universals.md#title-placeholders`.
- The chosen shape is summarized in the `## Context` body section and recorded as the first `## Decision Log` entry on `→ active`.
- `supersedes:` lists prior specs this one replaces. The writer cascades `{active|deprecated} → superseded` on the listed targets during the new spec's `→ active` transition. Targets at `draft` are reported as `not-supersedable` and left alone.
- `related:` is the soft-link slot — use it for cross-references between issue-family artifacts, including any `type: research` task that informed this spec (e.g., `related: [research/42-grpc-streaming]`). There is no stored-reverse contract; reverse lookups are derived on demand via grep / `../scripts/search.py`.
- Path values are plain strings without `.md` and without brackets (e.g., `spec/8-caching-strategy`, not `[spec/8-caching-strategy.md]`).
- Both `created` and `updated` are unquoted ISO dates. Bump `updated:` on every revision; the writer bumps it on status flips.

### Lifecycle and writer ownership

```
draft      → active | deprecated
active     → deprecated | superseded
deprecated → superseded
superseded → (terminal)
```

- Edit `status:` directly. The PostToolUse cascade hook detects the transition, refreshes `updated:`, and runs any cross-file cascade.
- `draft → superseded` is **disallowed** — supersession presumes the predecessor was at one point live.
- `active → superseded` is **automatic** — it fires when a successor spec with `supersedes: [<this>]` reaches `active`. Do not flip it by hand.
- `deprecated` is opt-in retirement, valid even before a successor exists. There is **no reverse path** from `deprecated → active`; author a new spec (with `supersedes:` pointing back) to revive the shape.

## Body shape

The body is a sequence of column-0 H2 markdown headings in Title Case (e.g., `## Context`, `## Specification`), with markdown content following each heading until the next H2 or end of file. H1 (`# Title`) is forbidden in the body — title belongs to frontmatter `title:`. Use H3+ headings inside sections freely.

**Required:**

- `## Context` — why this spec exists; what artifact it describes; the scope it covers.
- `## Specification` — the prescriptive content. Grammar, fields, format rules, examples. This is the heart of the spec.

**Optional, emit only when there is content for them:**

- `## Decision Log` — append-only, dated bullets summarizing what was chosen and why. **The only sanctioned slot for design rationale tied to this spec.** Earlier entries are never edited or removed; corrections are added as new entries that explain why prior reasoning no longer holds. Inline markdown links (e.g., `[research/42-grpc-streaming](../research/42-grpc-streaming.md)`) cite informing research tasks.
- `## Open Questions` — unresolved aspects the spec deliberately defers. Better than forcing premature closure.
- `## Rejected Alternatives` — the options considered and why they lost. Pairs naturally with `## Decision Log`. Inline citations to research tasks land here too when the rejection rationale leans on the investigation.
- `## Consequences` — downstream effects (positive, negative, or neutral) the spec creates.
- `## Examples` — concrete cases that pin down the prescriptive rules.
- `## Change Logs` — append-only audit trail of why this file was edited (dated bullets with markdown links to the causing issue).
- `## Log` — resume-context surface for a future session: current approach, blockers, decisions that diverge from upstream, open questions, next step. Strongly recommended while the spec is mid-flight (e.g., `drafting`). See `./body-conventions.md#log`.

Unknown H2 headings are tolerated (`## Benchmarks`, `## Migration Notes`, etc.). A `## Migration Plan` section is **not** used — migration work belongs in a task file under one of the issue family folders (`a4/task/`, `a4/bug/`, etc.).

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained. Frontmatter list paths are different (plain strings, no `.md`).

## Common mistakes

- **Stray content above the first H2 heading.** Anything in the body that is not whitespace must live under an H2 heading.
- **`## Context` or `## Specification` missing.** Both are required by convention; the writer rejects the `→ active` flip until they are present and non-empty.
- **H2 not in column 0 or not Title Case.** Section boundaries fire only on column-0 H2 headings whose text is Title Case with single-space separators.
- **Sections nested inside other sections.** Sections do not nest; every section sits at the body's top level. Use H3+ for inner structure.
- **H1 in body.** Title is frontmatter-only.

## Don't

- **Don't auto-populate `supersedes:`.** It is an explicit user decision in the authoring conversation.
- **Don't edit a prior spec's body to mark it superseded.** Supersession is captured in the *new* spec's frontmatter `supersedes:`; the cascade hook flips the prior spec's status automatically when the successor reaches `active`.
- **Don't pack multiple decisions into one spec.** One spec per decision; each gets its own id, supersede chain, and `## Decision Log`.
- **Don't author a spec post-hoc just to document existing code.** Specs are decisions, not retrospectives.
- **Don't introduce a separate `decisions/` slot.** All decision rationale lives inside the spec body's `## Decision Log`.
