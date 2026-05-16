# Workflow Actors Authoring

An actors page is a **knowledge-backed actor roster**. It defines people, organizations, systems, and external services that use cases reference.

Actors are curated knowledge. They are stored in the configured knowledge backend, not the issue backend.

Companion contracts:

- `./knowledge-body.md`

## Storage role

`actors` is stored in the knowledge backend.

Issue-backed work may cause actor updates, but the actors page itself is a knowledge page.

## Purpose

Use actors for the canonical roster of roles that participate in use cases.

Actors may be:

- People.
- Teams.
- Organizations.
- External systems.
- Platform/system actors.

Actor names or slugs should be reused consistently in use cases, specs, tasks, and reviews.

## Required metadata

Represent this metadata structurally when possible.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | Always `actors`. Use structured page metadata or index metadata depending on backend support. |
| `title` | yes | Usually `Actors` or project-specific equivalent. |
| `tags` | optional | Classification tags. |

Use canonical page identity. Do not use local projection paths as identity.

## Relationships

Represent relationships using structured page metadata, index metadata, or visible relationship sections according to the selected provider authoring files.

| Relationship | Required | Notes |
| --- | --- | --- |
| `related` | optional | Use cases, context, specs, reviews, or tasks related to actor changes. |

## Body shape

Required:

```markdown
## Roster

| Slug | Type | Role / Privileges | Description |
| --- | --- | --- | --- |
| meeting-organizer | person | Creates and shares meeting summaries | Person responsible for meeting follow-up. |
| platform | system | Performs automated background actions | The product system itself. |
```

Recommended columns:

- **Slug** — stable kebab-case or workspace-approved identifier.
- **Type** — `person`, `team`, `organization`, `system`, or configured equivalent.
- **Role / Privileges** — what this actor is allowed to do.
- **Description** — short explanation of who or what the actor is.

Optional:

- `## Authorization Notes` — cross-cutting authorization notes that affect several use cases.
- `## Related Work` — use cases, reviews, specs, or tasks related to actor changes.
- `## Change Log` — required for material updates. See `./knowledge-body.md`.

Unknown Title Case H2 headings are tolerated when they clarify actors or authorization context.

## Slug discipline

Actor slugs are referenced by use cases and sometimes by tasks, specs, or reviews.

A slug should:

- Match the user-facing role, not an implementation detail.
- Be stable.
- Be unique within the roster.
- Be concise and readable.

Do not rename a slug silently. If a rename is needed:

1. Update the actors page.
2. Add a `## Change Log` entry with the causing workflow artifact.
3. Update affected use cases, tasks, specs, and reviews, or create review items for deferred updates.

## Authorization guidance

Keep the roster concise.

- Actor privilege summaries belong in `## Roster`.
- Per-use-case authorization behavior belongs in curated use case pages.
- Technical enforcement details belong in `architecture` or `spec`.
- Product/problem framing belongs in `context`.

## Drift and feedback

If a use case references an actor not present in the roster, create a `review` item with `kind: finding` targeting the use case and actors page.

If a new actor appears during use case discovery, update the roster or create a `review` item with `kind: gap` if the update is deferred.

## Change log

Every material actors change should include a `## Change Log` entry linking to the causing workflow artifact.

```markdown
## Change Log

- 2026-05-13 — PROJ-123 — Added billing-admin actor.
```

Do not duplicate issue discussion in the page.

## Common mistakes

- Missing `## Roster`.
- Renaming a slug without updating downstream use cases.
- Using implementation details as actor names.
- Putting long actor backstories here instead of context.
- Putting detailed authorization flows here instead of use cases/specs.
- Using local projection paths or local file identity as canonical identity.

## Do not

- Do not store actors as an issue.
- Do not use page comments as a substitute for review items when actor feedback needs workflow tracking.
- Do not auto-trigger a skill just because actors are being written; follow the authoring resolver policy.
