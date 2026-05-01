# a4 — architecture wiki authoring

`a4/architecture.md` is the **most-depended-on wiki page** in the workspace. It is read directly by `bootstrap.md` (verify environment), `roadmap.md` (component → milestone mapping), and every task file across the four issue family folders (`task/`, `bug/`, `spike/`, `research/`) — their `## Interface Contracts` sections link into it. Allowing in-situ edits from non-architecture contexts would let contract drift propagate before review — hence the single-author rule.

Frontmatter contract: see `./frontmatter-universals.md` § Wiki family. Body conventions: see `./wiki-body.md` (`## Change Logs`, Wiki Update Protocol).

Note: no `created:` field on wiki pages — "first appeared" content lives in `context.md` `## Original Idea`.

## Body shape

**Required:**

- `## Overview` — high-level architectural narrative; how the system fits together, what trade-offs shaped it.
- `## Components` — per-component definitions. Each component lists its responsibility, the interface it exposes (consumed by tasks via `## Interface Contracts` links), and any cross-component dependencies.
- `## Technology Stack` — runtime, framework, libraries, persistence, build tooling. The chosen stack — not a "considered options" list (that belongs in a spec).
- `## Test Strategy` — how the system is tested. Unit / integration / e2e split, isolation strategy, fixtures. Consistency here matters because every implementation reads it to align test code.

**Optional, emit only when the conversation produced content for them:**

- `## Component Diagram` — diagrams (mermaid, ASCII, or links to external SVG / PNG kept under `a4/diagrams/`). Skip when prose + table is clearer than a picture.
- `## External Dependencies` — third-party services, vendor APIs, or upstream systems the architecture depends on. Skip when self-contained.
- `## Change Logs` — append-only audit trail of why this page was edited (dated bullets with markdown links to the causing review item, spec, or UC). The Wiki Update Protocol requires a bullet whenever a non-trivial change lands. Format and discipline: `./wiki-body.md`.

Unknown H2 headings are tolerated.

### Component anchor stability

`## Components` exposes anchor-targeted headings that tasks reference in their `## Interface Contracts` section (`[architecture#SessionService](../architecture.md#sessionservice)`). Keep component heading text stable — renaming a component requires a review item explaining the cascade because every task that links into it is affected.

## Common mistakes (architecture-specific)

- **Required section missing** (`## Overview`, `## Components`, `## Technology Stack`, `## Test Strategy`).
- **`type:` mismatch** with filename — the `type:` value must equal the file basename.

## Don't (architecture-specific)

(Universal Don'ts — non-primary-author edits, hand-editing writer-owned fields, bare-text `## Change Logs` bullets — apply on top of these.)

- **Don't write Launch & Verify content here.** That belongs in `bootstrap.md`'s `## Verify` section, the single source of truth. Reference bootstrap by markdown link if needed.
- **Don't write a roadmap / milestone schedule here.** Milestones belong in `roadmap.md`'s `## Plan` section.
- **Don't list considered options in `## Technology Stack`.** The chosen stack lives here; the comparison and rejected alternatives belong in a spec under `a4/spec/`.
- **Don't rename a component heading silently.** Renames cascade to every task's `## Interface Contracts` link. Open a review item to manage the cascade.
- **Don't pack a decision rationale into `## Overview`.** Decisions belong in a spec's `## Decision Log`. The architecture page records the *current* shape, not how it was reached.
