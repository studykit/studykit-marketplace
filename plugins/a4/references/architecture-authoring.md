# a4 — architecture wiki authoring

`a4/architecture.md` is the **most-depended-on wiki page** in the workspace. It is read directly by `bootstrap.md` (verify environment), `roadmap.md` (component → milestone mapping), and every `task/*.md` (`<interface-contracts>` links into it). Allowing in-situ edits from non-architecture contexts would let contract drift propagate before review — hence the single-author rule.

Companion to [`./frontmatter-schema.md §Wiki pages`](./frontmatter-schema.md), `./body-conventions.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: architecture
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `architecture`. The frontmatter validator rejects mismatches between `type:` and the file basename.
- Wiki pages have **no** `id`, no `status`, no `<log>`, no lifecycle. They change continuously; the `<change-logs>` body section records the why.
- No `created:` field on wiki pages — the `<original-idea>` / problem-framing-style "first appeared" content lives in `context.md`.

## Body shape

(Tag form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required:**

- `<overview>` — high-level architectural narrative; how the system fits together, what trade-offs shaped it.
- `<components>` — per-component definitions. Each component lists its responsibility, the interface it exposes (consumed by tasks via `<interface-contracts>` links), and any cross-component dependencies.
- `<technology-stack>` — runtime, framework, libraries, persistence, build tooling. The chosen stack — not a "considered options" list (that belongs in a spec).
- `<test-strategy>` — how the system is tested. Unit / integration / e2e split, isolation strategy, fixtures. Consistency here matters because every implementation reads it to align test code.

**Optional, emit only when the conversation produced content for them:**

- `<component-diagram>` — diagrams (mermaid, ASCII, or links to external SVG / PNG kept under `a4/diagrams/`). Skip when prose + table is clearer than a picture.
- `<external-dependencies>` — third-party services, vendor APIs, or upstream systems the architecture depends on. Skip when self-contained.
- `<change-logs>` — append-only audit trail of why this page was edited (dated bullets with markdown links to the causing review item, spec, or UC). The wiki-update protocol requires a bullet whenever a non-trivial change lands.

Unknown kebab-case tags are tolerated.

### Component anchor stability

`<components>` exposes anchor-targeted headings that tasks reference in their `<interface-contracts>` section (`[architecture#SessionService](../architecture.md#sessionservice)`). Keep component heading text stable — renaming a component requires a review item explaining the cascade because every task that links into it is affected.

## Common mistakes (architecture-specific)

- **Required section missing** (`<overview>`, `<components>`, `<technology-stack>`, `<test-strategy>`).
- **`type:` mismatch** with filename → frontmatter validator error.

(Universal validator catches — stray body content, attribute-bearing tags, same-tag nesting, H1 in body — are documented in `./body-conventions.md`.)

## Don't (architecture-specific)

(Universal Don'ts — non-primary-author edits, hand-editing writer-owned fields, bare-text `<change-logs>` bullets — apply on top of these.)

- **Don't write Launch & Verify content here.** That belongs in `bootstrap.md`'s `<verify>` section, the single source of truth. Reference bootstrap by markdown link if needed.
- **Don't write a roadmap / milestone schedule here.** Milestones belong in `roadmap.md`'s `<plan>` section.
- **Don't list considered options in `<technology-stack>`.** The chosen stack lives here; the comparison and rejected alternatives belong in a spec under `a4/spec/`.
- **Don't rename a component heading silently.** Renames cascade to every task's `<interface-contracts>` link. Open a review item to manage the cascade.
- **Don't pack a decision rationale into `<overview>`.** Decisions belong in a spec's `<decision-log>`. The architecture page records the *current* shape, not how it was reached.
