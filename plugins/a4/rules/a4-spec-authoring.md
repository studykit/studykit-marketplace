---
name: a4-spec-authoring
description: Authoring rules for a4 spec files. Auto-loaded when reading or editing anything under `a4/spec/`.
paths: ["a4/spec/**/*.md"]
---

# a4 — spec authoring guide

A spec at `a4/spec/<id>-<slug>.md` is a **living, prescriptive
specification** of an artifact the project commits to — a format,
protocol, schema, renderer rule, CLI surface, or any shape downstream
code, validators, and review items must conform to. Specs replace the
retired ADR family; design rationale lives inline as
`<decision-log>` entries co-located with the spec they shaped.

> **Workspace-wide policies** — writer-owned fields, id allocation,
> path-reference form, tag form, `<change-logs>` discipline, wiki
> authorship, cross-stage feedback, commit message form — live in
> [`a4-workspace-policies.md`](a4-workspace-policies.md) and load
> automatically alongside this rule. This rule covers the
> spec-specific contract on top.

This rule is the working contract for any LLM about to read, draft, or
edit a spec file. The full schema and rationale live in
[`references/frontmatter-schema.md §Spec`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md);
trigger detection lives in
[`references/spec-triggers.md`](${CLAUDE_PLUGIN_ROOT}/references/spec-triggers.md).

## When a spec is warranted

A moment is spec-worthy when **all** of these hold:

- **Multiple viable options exist** — not forced by the framework, the
  stack, or a hard constraint.
- **The trade-off is non-trivial** — picking option A vs B changes
  downstream effort, surface area, or cost meaningfully.
- **It is non-recoverable from code alone** — the *why* lives outside
  the codebase; reading code later would not reveal it.
- **It is plausibly revisitable** — future evidence could justify
  superseding it.

If any condition fails, the moment is probably **not** spec-worthy.
See the anti-patterns below.

### Conversational triggers

Surface a spec offer when these appear in dialogue:

- **B1 — multi-option enumeration:** "A or B", "REST vs GraphQL",
  "Postgres or Mongo".
- **B2 — trade-off language:** "we trade X for Y", "the cost of Z is
  …", "장단점이 있다".
- **B3 — uncertainty markers:** "not sure", "torn between", "더
  생각해봐야". Clarify first whether it is decision-pending
  (→ spec) or evidence-pending (→ research) — leave
  `<open-questions>` open if neither resolves quickly.
- **B4 — prior-spec references:** "we decided X before, but now…".
  This is a **supersede candidate** — author with
  `supersedes: [spec/<prior-id>-<slug>]` populated; do not edit the
  prior spec body.
- **B5 — task-implementer architectural-choice exit:** mid-task
  implementation surfaces a design alternative not yet captured.
  Halt, emit a `kind: gap` review item with `target: spec/`, return
  failure naming the review id; the user resolves via `/a4:spec`.
- **B6 — mid-`/a4:run` architecture-impacting choice:** same exit
  shape as B5 from the human-driven side.

### Anti-patterns — do **not** author a spec for these

- **Routine choices.** Variable names, folder layout, code formatting.
  Belongs in style guides or simply in the code.
- **Framework-mandated.** No alternative exists within the chosen
  stack — there is no decision to record.
- **Post-hoc justification.** Code is already written and the
  conversation is just explaining what is there. Specs are decisions;
  if no decision remains, do not retroactively author one.
- **Multiple decisions in one spec.** Three independent decisions →
  three specs, each with its own `<decision-log>` and supersede chain.
- **Bug fixes that just use the right tool.** Switching to the
  correct API call is a fix, not a decision.

## How to author — always via `/a4:spec`

Do **not** hand-craft a spec file with `Write`. Always invoke
`/a4:spec` so id allocation, slug derivation, frontmatter shape, body
validation, supersedes cascades, research-citation registration, and
the wiki nudge all run through the same skill. The skill detects
three modes from the seed and the recent conversation:

- **(a) Activate existing.** The seed names a `draft` spec already on
  disk; the skill confirms once and calls
  `transition_status.py --to active`.
- **(b) Revise existing.** The seed (or conversation) refines an
  `active` spec; the skill edits the body in place and appends a
  dated `<decision-log>` entry. `status:` stays `active`.
- **(c) New record.** Default. The skill drafts the body, writes the
  file at `status: draft`, then optionally activates it.

If you must read a spec to answer a question, prefer
`extract_section.py <file> <tag>` over loading the whole file (see
`a4-section-enum.md`).

## Frontmatter contract (do not deviate)

```yaml
---
type: spec
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: <draft | active | deprecated | superseded>
decision: "<one-line shape summary>"
supersedes: []        # list of paths, e.g. [spec/8-caching-strategy]
research: []          # list of paths, e.g. [research/<slug>]
related: []           # catchall for cross-references
labels: []            # free-form tags (alias: tags)
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

- `id` is allocated by `scripts/allocate_id.py` (workspace-global,
  monotonic). Never invent or reuse an id.
- `title` is required and must not be a placeholder; the writer
  rejects `<title>`-shaped strings.
- `decision` is the one-liner that summarizes the chosen shape — the
  same string `transition_status.py --reason` will quote in the
  `<log>` entry on `→ active`.
- `supersedes:` lists prior specs this one replaces. The writer
  cascades `{active|deprecated} → superseded` on the listed targets
  during the new spec's `→ active` transition. Targets at `draft` are
  reported as `not-supersedable` and left alone.
- `research:` is **registrar-owned**. Do not hand-edit it; invoke
  `register_research_citation.py` so the four-place atom (spec
  frontmatter `research:`, spec body `<research>`, research
  frontmatter `cited_by:`, research body `<cited-by>`) stays in sync.
- `related:` is **not** the slot for research links — those go to
  `research:` exclusively. `related:` is for cross-references between
  issue-family artifacts.
- Path values are plain strings without `.md` and without brackets
  (e.g., `spec/8-caching-strategy`, not `[spec/8-caching-strategy.md]`).
- Both `created` and `updated` are unquoted ISO dates. Bump
  `updated:` on every revision; the writer bumps it on status flips.

### Lifecycle and writer ownership

```
draft      → active | deprecated
active     → deprecated | superseded
deprecated → superseded
superseded → (terminal)
```

- All status changes flow through
  `scripts/transition_status.py`. Skills and humans never write
  `status:` directly after the initial create.
- `draft → superseded` is **disallowed** — supersession presumes the
  predecessor was at one point live.
- `active → superseded` is **automatic** — it fires when a successor
  spec with `supersedes: [<this>]` reaches `active`. Do not flip it
  by hand.
- `deprecated` is opt-in retirement, valid even before a successor
  exists. There is **no reverse path** from `deprecated → active`;
  author a new spec (with `supersedes:` pointing back) to revive the
  shape.

## Body shape

The body is a sequence of column-0 `<section>...</section>` blocks
(lowercase + kebab-case), with markdown content between the open and
close lines. H1 (`# Title`) is forbidden in the body — title belongs
to frontmatter `title:`. Use H3+ headings inside sections freely.

**Required (enforced by `body_schemas/spec.xsd`):**

- `<context>` — why this spec exists; what artifact it describes;
  the scope it covers.
- `<specification>` — the prescriptive content. Grammar, fields,
  format rules, examples. This is the heart of the spec.

**Optional, emit only when the conversation produced content for them:**

- `<decision-log>` — append-only, dated bullets summarizing what was
  chosen and why. **The only sanctioned slot for ADR-style
  rationale.** Earlier entries are never edited or removed;
  corrections are added as new entries that explain why prior
  reasoning no longer holds.
- `<open-questions>` — unresolved aspects the spec deliberately
  defers. Better than forcing premature closure.
- `<rejected-alternatives>` — the options considered and why they
  lost. Pairs naturally with `<decision-log>`.
- `<consequences>` — downstream effects (positive, negative, or
  neutral) the spec creates.
- `<examples>` — concrete cases that pin down the prescriptive rules.
- `<research>` — registrar-owned markdown links to citing research
  files. Do not hand-edit; invoke
  `register_research_citation.py`.
- `<change-logs>` — append-only audit trail of why this file was
  edited (dated bullets with markdown links to the causing issue).
- `<log>` — writer-owned status-transition trail
  (`YYYY-MM-DD — <from> → <to> — <reason>`). Never write into
  `<log>` directly.

Unknown kebab-case tags are tolerated by the XSD's openContent
(`<benchmarks>`, `<migration-notes>`, etc.). A `<migration-plan>`
section is **not** used — migration work belongs in
`task/<id>-<slug>.md`.

### Body-link form

Body cross-references are standard markdown links —
`[text](relative/path.md)` — with the `.md` extension retained.
Frontmatter list paths are different (plain strings, no `.md`).

## Common mistakes the validator catches

- **Stray content outside section blocks** → `body-stray-content`.
  Anything in the body that is not whitespace must live inside a
  `<tag>...</tag>` block.
- **`<context>` or `<specification>` missing** → `body-xsd`. Both
  are required by the XSD; the writer rejects the `→ active` flip
  until they are present and non-empty.
- **Inline or attribute-bearing tags** → `body-tag-invalid`. Open
  and close lines must be on column 0; no attributes; no
  self-closing.
- **Same-tag nesting** → `body-tag-invalid`. Sections do not nest;
  every section sits at the body's top level.
- **H1 in body** → `body-stray-content`. Title is frontmatter-only.

To validate manually before commit:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/validate_body.py" \
  "<project-root>/a4" --file spec/<id>-<slug>.md
```

## Don't

- **Don't hand-edit `status:`.** Use `transition_status.py`.
- **Don't hand-edit `research:` / `<research>` / `<cited-by>`.** Use
  `register_research_citation.py`.
- **Don't hand-edit `<log>`** (except the documented post-hoc
  `complete` task case — does not apply to specs).
- **Don't auto-populate `supersedes:`.** It is an explicit user
  decision in the authoring conversation.
- **Don't edit a prior spec's body to mark it superseded.**
  Supersession is captured in the *new* spec's frontmatter
  `supersedes:`; the writer cascades the prior spec's status
  automatically.
- **Don't pack multiple decisions into one spec.** One `/a4:spec`
  invocation per decision; each gets its own id, supersede chain,
  and `<decision-log>`.
- **Don't author a spec post-hoc just to document existing code.**
  Specs are decisions, not retrospectives.
- **Don't introduce a separate `decisions/` slot.** All decision
  rationale lives inside the spec body's `<decision-log>`.

## After authoring

`/a4:spec` performs the in-situ wiki nudge — mapping the spec's
scope to affected wiki pages (`architecture.md`, `context.md`,
`domain.md`, `actors.md`, `nfr.md`), confirming with the user, and
either editing with a dated `<change-logs>` bullet linking to the
spec, or deferring to a `kind: gap` review item. The skill does not
commit; the file (and any cascaded supersedes-target edits) is left
in the working tree for the user to commit at their convenience.

## Cross-references

- [`references/frontmatter-schema.md §Spec`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md) —
  full field schema, lifecycle, and validator behavior.
- [`references/spec-triggers.md`](${CLAUDE_PLUGIN_ROOT}/references/spec-triggers.md) —
  conversational and content-aware trigger catalog, plus
  anti-patterns.
- [`references/body-conventions.md`](${CLAUDE_PLUGIN_ROOT}/references/body-conventions.md) —
  tag form, blank-line discipline, link form,
  `<change-logs>` / `<log>` rules.
- [`skills/spec/SKILL.md`](${CLAUDE_PLUGIN_ROOT}/skills/spec/SKILL.md) —
  the authoring skill itself; this rule complements it for
  read/edit contexts where the skill is not invoked.
- `body_schemas/spec.xsd` — the source of truth for required vs
  optional sections; the `a4-section-enum` rule's bullet block is
  generated from it.
