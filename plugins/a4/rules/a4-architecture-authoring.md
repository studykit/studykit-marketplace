---
name: a4-architecture-authoring
description: Authoring rules for the a4 architecture wiki. Auto-loaded when reading or editing `a4/architecture.md`.
paths: ["a4/architecture.md"]
---

# a4 — architecture wiki authoring guide

`a4/architecture.md` is the **most-depended-on wiki page** in the
workspace. It is read directly by `bootstrap.md` (verify environment),
`roadmap.md` (component → milestone mapping), every `task/*.md`
(`<interface-contracts>` links into it), and `/a4:run` (AC source for
UC-less tasks). Allowing in-situ edits from non-architecture stages
would let contract drift propagate before review — hence the
single-author rule.

> **Workspace-wide policies** — writer-owned fields, id allocation,
> path-reference form, tag form, `<change-logs>` discipline, wiki
> authorship boundary, cross-stage feedback, commit message form —
> live in [`a4-workspace-policies.md`](a4-workspace-policies.md) and
> load automatically alongside this rule. This rule covers the
> architecture-wiki-specific contract on top.

This rule is the working contract for any LLM about to read, draft, or
edit the architecture wiki. The full schema lives in
[`references/frontmatter-schema.md §Wiki pages`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md).

## How to author — always via `/a4:arch`

Do **not** hand-craft `architecture.md` with `Write`. Always invoke
`/a4:arch` so the component design, technology stack, test strategy,
and `<change-logs>` audit trail are produced through the same flow.
The skill has a forward draft mode and an iterate mode; iterate is
the resolution path for `target: architecture` review items.

If you must read the file to answer a question, prefer
`extract_section.py a4/architecture.md <tag>` over loading the whole
markdown (see `a4-section-enum.md`).

## Authorship — architecture is single-author

`/a4:arch` is the **only** in-situ editor of `architecture.md`. No
other skill edits in-situ; everything else flows through review items
with `target: architecture` (and `wiki_impact: [architecture]` when
applicable). The general primary-author rule + cross-stage feedback
policy is in `a4-workspace-policies.md` §6 and §7.

If you find yourself wanting to edit `architecture.md` from any
context other than `/a4:arch`, **stop** and emit a review item.

## Frontmatter contract (do not deviate)

```yaml
---
type: architecture
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `architecture`. The frontmatter validator
  rejects mismatches between `type:` and the file basename.
- Wiki pages have **no** `id`, no `status`, no `<log>`, no lifecycle.
  They change continuously; the `<change-logs>` body section records
  the why.
- No `created:` field on wiki pages — the `<original-idea>` /
  problem-framing-style "first appeared" content lives in
  `context.md`.

## Body shape

(Tag form / link form / H1-forbidden are universal — see
`a4-workspace-policies.md` §4.)

**Required (enforced by `body_schemas/architecture.xsd`):**

- `<overview>` — high-level architectural narrative; how the system
  fits together, what trade-offs shaped it.
- `<components>` — per-component definitions. Each component lists
  its responsibility, the interface it exposes (consumed by tasks via
  `<interface-contracts>` links), and any cross-component
  dependencies.
- `<technology-stack>` — runtime, framework, libraries, persistence,
  build tooling. The chosen stack — not a "considered options" list
  (that belongs in a spec).
- `<test-strategy>` — how the system is tested. Unit / integration /
  e2e split, isolation strategy, fixtures. Read by every
  `task-implementer` to align test code; consistency here matters.

**Optional, emit only when the conversation produced content for them:**

- `<component-diagram>` — diagrams (mermaid, ASCII, or links to
  external SVG / PNG kept under `a4/diagrams/`). Skip when prose +
  table is clearer than a picture.
- `<external-dependencies>` — third-party services, vendor APIs, or
  upstream systems the architecture depends on. Skip when self-
  contained.
- `<change-logs>` — append-only audit trail of why this page was
  edited (dated bullets with markdown links to the causing review
  item, spec, or UC). The wiki-update protocol requires a bullet
  whenever a non-trivial change lands.

Unknown kebab-case tags are tolerated by the XSD's openContent.

### Component anchor stability

`<components>` exposes anchor-targeted headings that tasks reference
in their `<interface-contracts>` section
(`[architecture#SessionService](../architecture.md#sessionservice)`).
Keep component heading text stable — renaming a component requires a
review item explaining the cascade because every task that links
into it is affected.

## Common mistakes the validator catches (architecture-specific)

- **Required section missing** (`<overview>`, `<components>`,
  `<technology-stack>`, `<test-strategy>`) → `body-xsd`.
- **`type:` mismatch** with filename → frontmatter validator error.

(Universal validator catches — stray body content, attribute-bearing
tags, same-tag nesting, H1 in body — are documented in
`a4-workspace-policies.md` §4. `<change-logs>` discipline is in §5.)

To validate manually before commit:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/validate_body.py" \
  "<project-root>/a4" --file architecture.md
```

## Don't (architecture-specific)

(Universal Don'ts — non-primary-author edits, hand-editing writer-
owned fields, bare-text `<change-logs>` bullets — are in
`a4-workspace-policies.md` §10.)

- **Don't write Launch & Verify content here.** That belongs in
  `bootstrap.md`'s `<verify>` section, the single source of truth.
  Reference bootstrap by markdown link if needed.
- **Don't write a roadmap / milestone schedule here.** Milestones
  belong in `roadmap.md`'s `<plan>` section.
- **Don't list considered options in `<technology-stack>`.** The
  chosen stack lives here; the comparison and rejected alternatives
  belong in a spec under `a4/spec/`.
- **Don't rename a component heading silently.** Renames cascade to
  every task's `<interface-contracts>` link. Open a review item to
  manage the cascade.
- **Don't pack a decision rationale into `<overview>`.** Decisions
  belong in a spec's `<decision-log>`. The architecture page records
  the *current* shape, not how it was reached.

## After authoring

`/a4:arch` does not commit; the file is left in the working tree
along with any review items that the iterate flow flipped to
`resolved`. The next-step suggestion depends on workspace state —
typically `/a4:auto-bootstrap` (re-verify environment) or
`/a4:roadmap iterate` (propagate component changes into milestones).

When an architecture change has substantial downstream impact (new
component, contract change, technology swap), suggest re-running
`/a4:auto-bootstrap` and `/a4:roadmap iterate` before further coding
work.

## Cross-references

- [`references/frontmatter-schema.md §Wiki pages`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md) —
  full field schema, body-section table, validator behavior.
- [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md) —
  primary-author table, why architecture is more restrictive than
  domain, cross-stage stop/continue policy.
- [`references/body-conventions.md`](${CLAUDE_PLUGIN_ROOT}/references/body-conventions.md) —
  tag form, blank-line discipline, link form,
  `<change-logs>` rules, wiki update protocol.
- [`references/iterate-mechanics.md`](${CLAUDE_PLUGIN_ROOT}/references/iterate-mechanics.md) —
  the iterate procedure and close guard.
- [`skills/arch/SKILL.md`](${CLAUDE_PLUGIN_ROOT}/skills/arch/SKILL.md) —
  the authoring skill itself; this rule complements it for read/edit
  contexts where the skill is not invoked.
- `body_schemas/architecture.xsd` — the source of truth for required
  vs optional sections; the `a4-section-enum` rule's bullet block is
  generated from it.
