# Workflow Domain Authoring

A domain page is a **knowledge-backed shared vocabulary reference**. It catalogs cross-cutting product and business concepts used by use cases, specs, architecture, tasks, reviews, and research.

Domain is curated knowledge. It is stored in the configured knowledge backend, not the issue backend.

Companion contracts:

- `./metadata-contract.md`
- `./knowledge-body.md`
- Provider binding: `./providers/confluence-page-authoring.md` or `./providers/github-wiki-authoring.md`

## Storage role

`domain` is stored in the knowledge backend.

Supported knowledge providers:

- Confluence
- GitHub Wiki

Issue-backed work may cause domain updates, but the domain page itself is a knowledge page.

## Purpose

Use domain for shared vocabulary:

- Domain entities.
- Value objects.
- Important product terms.
- Lifecycle states.
- Invariants.
- Concept relationships.

Domain terms should be reused consistently in use cases, specs, architecture, tasks, and reviews.

Do not use domain for runtime components, framework constructs, or implementation classes unless those names are also domain concepts.

## Required metadata

Represent this metadata using provider-native fields when available.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | Always `domain`. Use page property, label, metadata block, or index metadata depending on provider. |
| `title` | yes | Usually `Domain` or project-specific equivalent. |
| `related` | optional | Use cases, specs, architecture, reviews, research, or tasks related to domain changes. |
| `labels` | optional | Provider labels/tags. |

Provider identity replaces local file path identity. Use page identity from the knowledge provider.

## Body shape

Required:

```markdown
## Concepts

<glossary of entities, value objects, and significant domain terms>
```

Each concept should include:

- Name.
- One-paragraph definition.
- Examples when useful.
- Invariants or constraints when important.

Optional:

- `## Relationships` — associations, compositions, aggregates, ownership, cardinality.
- `## State Transitions` — named lifecycle states, allowed next states, and triggers.
- `## Related Work` — workflow issues, specs, use cases, research, reviews, or architecture pages that inform the vocabulary.
- `## Change Log` — required for material updates. See `./knowledge-body.md`.

Unknown Title Case H2 headings are tolerated when they clarify the domain model.

## Concept stability

Domain terms are reference targets for use cases, specs, architecture, and code.

Do not rename a concept silently. If a rename is needed:

1. Update the domain page.
2. Add a `## Change Log` entry with the causing workflow artifact.
3. Update affected use cases, specs, architecture, tasks, and reviews, or create review items for deferred updates.

## Relationship and state notation

Prefer compact, scannable formats:

- Tables.
- Mermaid diagrams.
- Short bullet lists.
- ASCII diagrams.

Avoid long prose when a table or diagram would make relationships clearer.

## Relationship to other knowledge pages

- Use `architecture` for runtime components and integration boundaries.
- Use `context` for product/problem framing.
- Use `spec` for prescriptive contracts.
- Use `usecase` curated pages for user-visible interactions.
- Use `nfr` for non-functional targets.

## Drift and feedback

If a concept appears repeatedly in use cases, specs, architecture, or tasks but is missing from domain, create a `review` item with `kind: gap` targeting the domain page and the causing artifact.

If architecture uses a domain term differently from this page, create a `review` item with `kind: finding` targeting both pages.

## Change log

Every material domain change should include a `## Change Log` entry linking to the causing workflow artifact.

```markdown
## Change Log

- 2026-05-13 — PROJ-123 — Added Workspace as distinct from Organization.
```

Do not duplicate the issue discussion in the page.

## Common mistakes

- Missing `## Concepts`.
- Putting architecture components or framework constructs in domain.
- Renaming concepts without managing downstream references.
- Defining the same concept with different names.
- Writing relationship/state diagrams as long prose.
- Using local projection paths or local file identity as provider-backed identity.

## Do not

- Do not store domain as an issue.
- Do not use page comments as a substitute for review items when terminology feedback needs workflow tracking.
- Do not auto-trigger a skill just because domain is being written; follow the authoring resolver policy.
