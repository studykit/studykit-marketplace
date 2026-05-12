# Workflow Architecture Authoring

An architecture page is a **knowledge-backed design-intent reference** for the current system shape: components, responsibilities, integration boundaries, technology stack, and test strategy.

Architecture is curated knowledge. It is stored in the configured knowledge backend, not the issue backend.

Companion contracts:

- `./metadata-contract.md`
- `./knowledge-body.md`
- Provider binding: `./providers/confluence-page-authoring.md` or `./providers/github-knowledge-authoring.md`

## Storage role

`architecture` is stored in the knowledge backend.

Supported knowledge providers:

- Confluence
- GitHub repository `wiki/`

Issue-backed tasks, bugs, spikes, reviews, use cases, and research may cause architecture updates, but the architecture page itself is a knowledge page.

## Purpose

Architecture records the current design shape that implementation work should align with.

Use it for:

- System overview.
- Component responsibilities.
- Interfaces exposed or consumed by components.
- Cross-component dependencies.
- Technology stack.
- Testing strategy at the system level.

Do not use it for:

- Long decision rationale.
- Raw discussion.
- Roadmaps.
- Task-level implementation plans.
- Detailed API/schema contracts that belong in specs.

## Required metadata

Represent this metadata using provider-native fields when available.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | Always `architecture`. Use page property, label, metadata block, or index metadata depending on provider. |
| `title` | yes | Usually `Architecture` or project-specific equivalent. |
| `status` | optional | Use when the provider supports page lifecycle state. |
| `related` | optional | Specs, epics, tasks, reviews, use cases, or research that materially relate to the page. |
| `labels` | optional | Provider labels/tags. |

Provider identity replaces local file path identity. Use page identity from the knowledge provider.

## Body shape

Required:

```markdown
## Overview

<high-level architectural narrative>

## Components

<component definitions, responsibilities, interfaces, and dependencies>

## Technology Stack

<chosen runtime, framework, libraries, persistence, build tooling>

## Test Strategy

<unit/integration/e2e split, isolation strategy, fixtures, and test boundaries>
```

Optional:

- `## Component Diagram` — Mermaid, ASCII, or link to external diagram artifact.
- `## External Dependencies` — third-party services, vendor APIs, upstream systems.
- `## Related Work` — issues, specs, reviews, use cases, or research that inform the architecture.
- `## Change Log` — required for material updates. See `./knowledge-body.md`.

Unknown Title Case H2 headings are tolerated when they clarify current architecture.

## Component anchors

Component headings are reference targets for tasks, bugs, specs, and reviews.

Keep component names stable. If a component is renamed:

1. Update the architecture page.
2. Add a `## Change Log` entry with the causing workflow artifact.
3. Update affected specs/tasks/reviews or create review items for deferred updates.

Do not silently rename component headings.

## Decision rationale

Architecture records the current shape. Durable rationale belongs in specs, especially `## Decision Log` or `## Rejected Alternatives`.

A short rationale sentence is acceptable when it helps readers understand the current shape. Long comparisons and rejected options belong in a spec or research report.

## Change log

Every material architecture change should include a `## Change Log` entry linking to the causing workflow artifact.

```markdown
## Change Log

- 2026-05-13 — PROJ-123 — Split AuthService and SessionService responsibilities.
```

Do not duplicate the issue discussion in the page.

## Relationship to other knowledge pages

- Use `domain` for vocabulary, concepts, relationships, and state transitions.
- Use `context` for problem framing, product scope, and original idea.
- Use `nfr` for non-functional requirements.
- Use `ci` for exact test commands and CI execution contract.
- Use `spec` for prescriptive API/schema/protocol contracts.

## Common mistakes

- Missing `## Overview`, `## Components`, `## Technology Stack`, or `## Test Strategy`.
- Writing executable test commands here instead of `ci`.
- Using architecture as a roadmap or milestone plan.
- Listing considered options in `## Technology Stack` instead of recording chosen stack only.
- Packing long decision rationale into `## Overview` instead of a spec.
- Renaming component headings without updating references or creating review items.
- Using local projection paths or local file identity as provider-backed identity.

## Do not

- Do not store architecture as an issue.
- Do not use page comments as a substitute for review items when feedback needs workflow tracking.
- Do not auto-trigger a skill just because architecture is being written; follow the authoring resolver policy.
