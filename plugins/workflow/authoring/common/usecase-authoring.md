# Workflow Use Case Authoring

A workflow use case describes **how an actor interacts with the system to achieve a goal in a specific situation**, with a user-visible flow and expected outcome.

Use cases have two authoring surfaces:

1. An issue-backed item for discovery, questions, discussion, status, and feedback.
2. A knowledge-backed curated page for the settled use case content.

The issue item is always created first. The curated knowledge page is created or updated when there is stable content worth publishing.

Companion contracts:

- `./issue-body.md`
- `./knowledge-body.md`
- Issue rules: `./issue-authoring.md`

## Storage role

`usecase` has two roles.

| Role | Backend | Purpose |
| --- | --- | --- |
| Workflow issue | Configured issue backend | Discovery, questions, review, status, discussion, and task linkage. |
| Curated knowledge page | Configured knowledge backend | Stable use case content used by implementation and testing. |

The workflow issue may exist without a curated page while the use case is being shaped. The curated page should link back to the workflow issue when published.

## Abstraction discipline

Use cases stay at the user level.

Write:

- What the actor does.
- What the actor sees.
- What outcome the actor expects.
- User-visible validation and error behavior.

Do not write:

- Database tables.
- Queue names.
- Service internals.
- Framework mechanics.
- Implementation algorithms.

Internal mechanics belong in `architecture`, `spec`, or implementation tasks.

## Workflow issue body

The workflow issue body should summarize discovery state and link to the curated page when available.

Recommended sections:

```markdown
## Description

<why this use case is being explored and who needs it>

## Actors

- <actor>

## Current Draft

<short current summary or link to curated page draft>

## Open Questions

- <question>
```

Optional sections:

- `## Related Work` — related tasks, specs, reviews, research, or pages.
- `## Supersedes` — prior use case when replacing one.
- `## Resume` — current-state snapshot while shaping. See `./issue-body.md`.

Use comments for conversation, interview notes, and feedback threads.

## Curated page body

The curated use case page should contain the stable user-facing content.

Required:

```markdown
## Goal

<what the actor wants to accomplish>

## Situation

<trigger and context>

## Flow

1. <user-visible step>
2. <user-visible response or next action>

## Expected Outcome

<observable successful outcome>
```

Optional:

- `## Actors` — actor list when not obvious from the flow.
- `## Validation` — user-visible input constraints, limits, or required formats.
- `## Error Handling` — what the actor sees when things fail.
- `## Related Work` — workflow issues, tasks, specs, or research.
- `## Supersedes` — prior use case page when replacing one.
- `## Change Log` — required for material updates. See `./knowledge-body.md`.

Do not include raw discovery discussion in the curated page.

## Publishing rule

Publish or update the curated page when:

- The actor and goal are clear.
- The flow is stable enough to guide tasks.
- Expected outcome is explicit.
- Blocking open questions are resolved or intentionally deferred.
- User-visible validation and error handling are known or explicitly out of scope.

The first publication should add a `## Change Log` entry linking to the workflow issue.

## Task linkage

Tasks that implement the use case should link to the curated page or workflow issue through the `implements` relationship according to the selected authoring files.

Prefer the curated page when it exists, because it contains the stable implementation-facing content. Use the workflow issue when the curated page has not been published yet.

## Knowledge side effects

Authoring or revising a use case may require updates to other knowledge pages:

- New actor → `actors` page.
- New domain concept → `domain` page.
- Scope or problem framing change → `context` page.
- New screen or interaction group → `context` or product-facing page.
- New non-functional requirement → `nfr` page.
- New implementation contract → `spec` page.

If the update is deferred, create a `review` item with `kind: gap` targeting the affected knowledge page and the causing use case issue/page.

## Splitting a use case

Split a use case when the actor goal forks or the flow contains multiple independent goals.

When splitting:

1. Confirm the split with the user.
2. Create separate workflow issues for the child use cases.
3. Publish or update curated pages when each child is stable.
4. Link parent and child workflow issues according to the selected issue authoring files.
5. Do not use supersession unless an older published use case is being replaced.

## Common mistakes

- Writing internal system mechanics into the use case.
- Publishing a curated page before the user-visible flow is stable.
- Leaving the workflow issue without a link to the curated page after publication.
- Putting long discovery discussion into the curated page.
- Creating tasks from a use case whose flow or expected outcome is still unclear.
- Using local projection paths or local integer ids as canonical identity.

## Do not

- Do not create the curated page before the workflow issue unless importing existing documents.
- Do not store use case discussion only in the knowledge page.
- Do not pack multiple actor goals into one use case.
- Do not auto-trigger a skill just because a use case is being written; follow the authoring resolver policy.
