# a4 — roadmap wiki authoring

`a4/roadmap.md` is the **milestone narrative wiki**. It groups UCs into milestones, names the dependency graph between them, and records Shared Integration Points the architecture exposes.

Frontmatter contract: see `./frontmatter-universals.md` § Wiki family. Body conventions: see `./body-conventions.md`.

## Body shape

(Heading form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required:**

- `## Plan` — the entire roadmap content lives in this single section, organized internally with H3+ headings:
  - **Milestone narrative.** What each milestone delivers, in user terms (links to the UCs it ships).
  - **Dependency graph.** Which milestones depend on which (mermaid or table form). Derived from each UC's `## Dependencies` body narrative, `task.depends_on:` chains, and architecture Shared Integration Points.
  - **Shared Integration Points.** Architecture interfaces that multiple milestones touch — typically named with markdown links into `architecture.md` `## Components`.
  - **Launch & Verify pointer.** A one-line link pointing at `bootstrap.md` (`See [bootstrap](bootstrap.md) for environment setup, build commands, and the verified smoke test.`). **No Launch & Verify content lives here** — `bootstrap.md` is the single source of truth.

**Optional:**

- `## Change Logs` — append-only audit trail of why this page was edited (dated bullets with markdown links to the causing UC, review item, or spec).

Unknown H2 headings are tolerated.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained. Every UC reference in the milestone narrative and every architecture component reference in Shared Integration Points uses this form.

## `## Change Logs` discipline

```markdown
## Change Logs

- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — milestone-2 reshaped after arch fix
- YYYY-MM-DD — [usecase/<id>-<slug>](usecase/<id>-<slug>.md) — added to milestone-3
```

Create the section if absent. The wiki close guard surfaces missing bullets when a review item whose `target:` lists `roadmap` transitions to `resolved`.

## Common mistakes (roadmap-specific)

- **Required section missing** (`## Plan`).

(Universal body conventions — stray content above the first H2, malformed headings, sections nested inside other sections, H1 in body, `type:` mismatch with filename — are documented in `./body-conventions.md` and `./frontmatter-universals.md`.)

## Don't

- **Don't write Launch & Verify content here.** A one-line link to `bootstrap.md` is the contract.
- **Don't define new architecture components here.** Components live in `architecture.md`. The roadmap references them.
- **Don't author tasks here.** Tasks live in `a4/<type>/<id>-<slug>.md` under one of the four issue family folders (`task/`, `bug/`, `spike/`, `research/`). The roadmap names milestones; tasks deliver them.
- **Don't pack architecture rationale.** Decisions belong in specs; the architecture page records the *current* shape; the roadmap records the *delivery sequence*.
- **Don't append `## Change Logs` bullets without a markdown link.**
