# Workflow Context Authoring

A context page is a **knowledge-backed framing reference**. It records the original idea, problem framing, scope boundaries, and optional UI/navigation framing that other work items and knowledge pages assume.

Context is curated knowledge. It is stored in the configured knowledge backend, not the issue backend.

Companion contracts:

- `./knowledge-body.md`

## Storage role

Context pages are knowledge pages. Do not store context pages in the issue backend.

## Purpose

Use context for upstream framing:

- Original idea or starting prompt.
- Problem framing.
- Scope boundaries.
- Coarse success definition.
- UI screen/navigation narrative when useful.

Every other work item or knowledge page indirectly assumes the framing captured here.

Do not use context for detailed use case flows, domain glossary, implementation design, or task plans.

## Body shape

Required:

```markdown
## Original Idea

<verbatim original user input or imported project brief>

## Problem Framing

<who has the problem, what is failing, and what success looks like at a coarse level>
```

Optional:

- `## Scope` — explicit in-scope and out-of-scope boundaries.
- `## Screens` — UI screen/navigation grouping when the project has UI flows.
- `## Success Criteria` — coarse project-level success definition.
- `## Related Work` — use cases, epics, specs, research, or reviews related to framing.
- `## Change Log` — required for material updates. See `./knowledge-body.md`.

Unknown Title Case H2 headings are tolerated when they clarify project framing.

## Original idea rule

Preserve the original input as faithfully as possible.

If context is created from a conversation, quote or clearly mark the initial user-provided idea. Later clarifications should be appended or summarized separately; do not rewrite the original idea so heavily that the starting point disappears.

If importing an existing project, use the imported project brief or source link instead of inventing an original idea.

## Problem framing rule

`## Problem Framing` should answer:

- Who has the problem?
- What current situation or solution is failing?
- Why does it matter?
- What would coarse success look like?

Keep this section at framing level. Detailed flows belong in use case pages. Implementation shape belongs in architecture or specs.

## Screens

Use `## Screens` only for UI-heavy projects where navigation framing helps organize use cases.

Each screen entry should include:

- Screen name or slug.
- Purpose.
- Related use cases.
- Optional mockup or prototype link.

Do not embed large mockups inline. Link to design artifacts or generated previews.

## Change log

Every material context change should include a `## Change Log` entry linking to the causing work item.

```markdown
## Change Log

- 2026-05-13 — PROJ-123 — Narrowed initial scope to admin onboarding.
```

Do not duplicate issue discussion in the page.

## Content boundaries

Use these boundaries to place framing content. Do not encode these as metadata relationships.

- Use `actors` for actor roster and definitions.
- Use `domain` for shared vocabulary and concepts.
- Use `usecase` curated pages for detailed user-visible flows.
- Use `architecture` for system shape.
- Use `spec` for implementation contracts.
- Use `nfr` for non-functional targets.

## Common mistakes

- Missing `## Original Idea` or `## Problem Framing`.
- Rewriting the original idea until the starting point is lost.
- Putting detailed use case flows in context.
- Putting domain concepts or actor rosters in context.
- Using context as a roadmap or task list.
- Using local projection paths or local file identity as canonical identity.

## Do not

- Do not store context as an issue.
- Do not use page comments as a substitute for review items when framing feedback needs workflow tracking.
- Do not auto-trigger a skill just because context is being written; follow the authoring resolver policy.
