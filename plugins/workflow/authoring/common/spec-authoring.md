# Workflow Spec Authoring

A workflow spec is a **knowledge-backed prescriptive implementation contract** for a single artifact: an API shape, schema, protocol, renderer rule, CLI surface, file format, integration contract, or other downstream implementation shape.

Specs are curated knowledge artifacts. They are stored in the configured knowledge backend, not the issue backend.

Companion contracts:

- `./knowledge-body.md`

## Storage role

`spec` is stored in the knowledge backend.

Issue-backed work may create, review, or apply a spec, but the spec itself is a knowledge page.

## Supersession

Supersession is an explicit authoring decision.

When a new spec replaces an older spec:

1. Add the older spec under `## Supersedes`.
2. Explain the replacement in the new spec body.
3. Add `## Change Log` entries to affected pages as needed.

Do not edit an old spec body merely to describe the new contract. The new spec carries the new contract. The old spec may point to the replacement when that update is useful and safe.

## Body shape

Required:

```markdown
## Context

<why this spec exists, what artifact it covers, and what is out of scope>

## Specification

<prescriptive contract>
```

`## Specification` is the heart of the spec. It should contain rules, fields, grammar, examples, API shape, protocols, constraints, or other details downstream work must follow.

Optional sections:

- `## Supersedes` — required when the spec replaces prior specs.
- `## Related Work` — tasks, reviews, use cases, research, or epics related to this spec.
- `## Open Questions` — unresolved aspects the spec deliberately defers.
- `## Consequences` — downstream effects for code, tooling, operations, or users.
- `## Examples` — concrete cases that pin down the rules.
- `## Decision Log` — concise rationale entries for decisions embedded in the spec.
- `## Rejected Alternatives` — options considered and why they lost.
- `## Change Log` — semantic cause index for material edits. See `./knowledge-body.md`.
- `## Sources` — external sources or research reports used as evidence.

Unknown Title Case H2 headings are tolerated when they clarify the contract.

## Decision rationale

Use `## Decision Log` for durable rationale.

```markdown
## Decision Log

- 2026-05-13 — Chose opaque session tokens over JWTs because revocation latency is a hard requirement. Related: PROJ-123.
```

Earlier entries are append-only. If a decision changes, append a new entry explaining the correction.

Do not introduce a separate decisions artifact for routine spec-local rationale.

## Related work and research

Specs may be informed by research, use cases, tasks, reviews, and architecture/domain pages.

Use canonical references in body text:

```markdown
## Related Work

- PROJ-123
- #456
- [OAuth Integration Evaluation](https://example.com/pages/oauth-integration-evaluation)
```

Research should provide evidence. The spec makes the decision.

## Change log

Every material update should add a concise `## Change Log` entry linking to the causing workflow artifact.

```markdown
## Change Log

- 2026-05-13 — PROJ-123 — Activated initial auth session contract.
```

Do not duplicate issue discussion or review threads in the spec.

## Readiness rule

A spec should not be used as an implementation contract until:

- `## Context` is present and clear.
- `## Specification` is present and prescriptive.
- Open questions that block implementation are resolved or explicitly deferred.
- Supersession links are visible when replacing another spec.
- Related work and sources needed to understand the decision are linked.

## Common mistakes

- Missing `## Context` or `## Specification`.
- Treating the spec as a discussion thread instead of a curated contract.
- Packing several unrelated contracts into one spec.
- Hiding implementation decisions in task issues instead of updating or creating a spec.
- Treating a spec as implementation-ready while blocking open questions remain unresolved.
- Using local projection paths or local integer ids as canonical identity.

## Do not

- Do not store specs as issue-backed tasks.
- Do not author specs for routine implementation details such as variable names or formatting choices.
- Do not make research conclusions directly prescriptive; cite research and record the spec decision separately.
- Do not auto-trigger a skill just because a spec is being written; follow the authoring resolver policy.
