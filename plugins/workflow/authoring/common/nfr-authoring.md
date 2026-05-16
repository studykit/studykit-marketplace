# Workflow NFR Authoring

An NFR page is a **knowledge-backed non-functional requirements reference**. It records measurable cross-cutting properties such as performance, security, scalability, accessibility, reliability, privacy, compliance, and operational constraints.

NFR is curated knowledge. It is stored in the configured knowledge backend, not the issue backend.

Companion contracts:

- `./knowledge-body.md`

## Storage role

`nfr` is stored in the knowledge backend.

Issue-backed work may cause NFR updates, but the NFR page itself is a knowledge page.

## Purpose

Use NFR for measurable cross-cutting requirements:

- Performance targets.
- Security requirements.
- Scalability bounds.
- Accessibility requirements.
- Reliability and availability targets.
- Privacy or compliance constraints.
- Operational constraints.

NFRs should affect use cases, architecture, specs, tests, or implementation priorities.

Do not use NFR for functional behavior. Functional behavior belongs in use cases and specs.

## Body shape

Required:

```markdown
## Requirements

| ID | Description | Affected Scope | Measurable Criteria | Verification |
| --- | --- | --- | --- | --- |
| NFR-1 | Cold-start response latency | All login flows | p95 < 200 ms | Performance test or production metric |
```

Recommended columns:

- **ID** — stable short identifier, useful for references.
- **Description** — concise requirement statement.
- **Affected Scope** — use cases, specs, systems, or `(all)`.
- **Measurable Criteria** — threshold, standard, check, or measurable condition.
- **Verification** — how the requirement is verified.

Optional:

- `## Rationale` — why the NFR matters when not obvious.
- `## Related Work` — issues, specs, reviews, research, use cases, or architecture pages related to NFR changes.
- `## Change Log` — required for material updates. See `./knowledge-body.md`.

Unknown Title Case H2 headings are tolerated when they clarify NFRs.

## Measurability rule

Every NFR should be measurable.

Avoid vague requirements:

- "The app should be fast."
- "Security should be strong."
- "The UI should be accessible."

Prefer measurable forms:

- "p95 response latency under 200 ms for authenticated search."
- "All admin actions require audit log entries with actor, timestamp, action, and target."
- "UI meets WCAG 2.2 AA for the onboarding flow."

If a requirement cannot yet be measured, create a `review` item with `kind: question` or `gap` rather than adding an aspirational NFR.

## Artifact boundaries

NFR records the target.

- `architecture` records the design response.
- `ci` records how tests/checks run.
- `spec` records precise contracts when an NFR affects an API, schema, protocol, or format.

Do not put implementation strategies in the NFR page unless they are part of the requirement itself.

## Verification

Each NFR should have a verification path:

- Automated test.
- CI check.
- Monitoring query.
- Audit process.
- Manual review procedure.
- Compliance evidence.

If verification is not yet known, mark it as an open question and create a review item if it blocks work.

## Change log

Every material NFR change should include a `## Change Log` entry linking to the causing workflow artifact.

```markdown
## Change Log

- 2026-05-13 — PROJ-123 — Added p95 latency target for login flow.
```

Do not duplicate issue discussion in the page.

## Common mistakes

- Missing `## Requirements`.
- Writing aspirational requirements without measurable criteria.
- Putting functional behavior here instead of use cases/specs.
- Putting implementation strategy here instead of architecture/spec.
- Adding NFRs with no verification path or follow-up review item.
- Using local projection paths or local file identity as canonical identity.

## Do not

- Do not store NFRs as issues.
- Do not use page comments as a substitute for review items when NFR feedback needs workflow tracking.
- Do not auto-trigger a skill just because NFRs are being written; follow the authoring resolver policy.
