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

This rule is the working contract for any LLM about to read, draft, or
edit the architecture wiki. The full schema lives in
[`references/frontmatter-schema.md §Wiki pages`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md);
authorship boundaries live in
[`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md);
body-tag mechanics live in
[`references/body-conventions.md`](${CLAUDE_PLUGIN_ROOT}/references/body-conventions.md).
Read those before deviating from the rules below.

## How to author — always via `/a4:arch`

Do **not** hand-craft `architecture.md` with `Write`. Always invoke
`/a4:arch` so the component design, technology stack, test strategy,
and `<change-logs>` audit trail are produced through the same flow.
The skill has a forward draft mode and an iterate mode; iterate is
the resolution path for `target: architecture` review items.

If you must read the file to answer a question, prefer
`extract_section.py a4/architecture.md <tag>` over loading the whole
markdown (see `a4-section-enum.md`).

## Authorship — who can edit this page

Per `references/wiki-authorship.md`:

- **`/a4:arch` is the primary author.** Any change to body
  sections originates from this skill.
- **No other skill edits in-situ.** When `/a4:usecase`, `/a4:domain`,
  `/a4:roadmap`, `/a4:auto-bootstrap`, or `task-implementer` discover
  an architecture issue, they emit a review item with
  `target: architecture` and (when applicable)
  `wiki_impact: [architecture]`. Resolution flows back through
  `/a4:arch iterate`.
- The cross-stage stop/continue policy decides whether the discovering
  stage halts (`roadmap`, `run`) or continues with a review item
  (`auto-bootstrap`, `usecase iterate`, `domain iterate`,
  `auto-usecase`).

If you find yourself wanting to edit `architecture.md` from any
context other than `/a4:arch`, **stop** and emit the review item
instead.

## Frontmatter contract (do not deviate)

```yaml
---
type: architecture
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `architecture`. The frontmatter validator
  rejects mismatches between `type:` and the file basename.
- `updated:` is an unquoted ISO date. Bump on every edit (including
  in-situ `<change-logs>` bullet appends).
- Wiki pages have **no** `id`, no `status`, no `<log>`, no lifecycle.
  They change continuously; the `<change-logs>` body section records
  the why.
- No `created:` field on wiki pages — the `<original-idea>` /
  problem-framing-style "first appeared" content lives in
  `context.md`.

## Body shape

The body is a sequence of column-0 `<section>...</section>` blocks
(lowercase + kebab-case), with markdown content between the open and
close lines. H1 (`# Title`) is forbidden in the body. Use H3+ headings
inside sections freely.

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

### Body-link form

Body cross-references are standard markdown links —
`[text](relative/path.md)` — with the `.md` extension retained
(e.g., `[task/5-render-markdown](task/5-render-markdown.md)`,
`[review/9-arch-rename-cascade](review/9-arch-rename-cascade.md)`).

`<components>` exposes anchor-targeted headings that tasks reference
in their `<interface-contracts>` section
(`[architecture#SessionService](../architecture.md#sessionservice)`).
Keep component heading text stable — renaming a component requires a
review item explaining the cascade because every task that links
into it is affected.

## `<change-logs>` discipline

Every non-trivial edit appends a bullet:

```markdown
<change-logs>

- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — <short note>
- YYYY-MM-DD — [spec/<id>-<slug>](spec/<id>-<slug>.md) — <short note>

</change-logs>
```

Create the section if absent. Order is append-only — earlier bullets
are never edited or removed.

The wiki **close guard** (per
`references/iterate-mechanics.md`) warns when a review item with
`wiki_impact: [architecture]` transitions to `resolved` but no bullet
points back at it. The drift detector re-surfaces violations.

## Common mistakes the validator catches

- **Stray content outside section blocks** → `body-stray-content`.
  Anything in the body that is not whitespace must live inside a
  `<tag>...</tag>` block.
- **Required section missing** (`<overview>`, `<components>`,
  `<technology-stack>`, `<test-strategy>`) → `body-xsd`.
- **Inline or attribute-bearing tags** → `body-tag-invalid`. Open
  and close lines must be on column 0; no attributes; no
  self-closing.
- **Same-tag nesting** → `body-tag-invalid`. Sections do not nest;
  every section sits at the body's top level.
- **H1 in body** → `body-stray-content`. Wiki pages have no
  frontmatter `title:` field; the page name is the file basename.
- **`type:` mismatch** with filename → frontmatter validator error.

To validate manually before commit:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/validate_body.py" \
  "<project-root>/a4" --file architecture.md
```

## Don't

- **Don't edit from any skill other than `/a4:arch`.** Emit a review
  item with `target: architecture`.
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
- **Don't append to `<change-logs>` without a markdown link to the
  causing issue.** Bare-text bullets break the close-guard / drift
  detection chain.
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
