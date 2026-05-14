# Workflow Use Case Authoring

A workflow use case describes **how an actor interacts with the system to achieve a goal in a specific situation**, with a user-visible flow and expected outcome.

Use cases are dual artifacts:

1. An issue-backed workflow artifact for discovery, questions, discussion, status, and feedback.
2. A knowledge-backed curated page for the settled use case content.

The issue artifact is always created first. The curated knowledge page is created or updated when there is stable content worth publishing.

Companion contracts:

- `./metadata-contract.md`
- `./issue-body.md`
- `./knowledge-body.md`
- Issue provider binding: `./providers/github-issue-authoring.md` or `./providers/jira-issue-authoring.md`
- Knowledge provider binding: `./providers/confluence-page-authoring.md` or `./providers/github-knowledge-authoring.md`

## Storage role

`usecase` has two roles.

| Role | Provider | Purpose |
| --- | --- | --- |
| Workflow issue | GitHub Issues or Jira | Discovery, questions, review, status, discussion, and task linkage. |
| Curated knowledge page | Confluence or GitHub repository `wiki/` | Stable use case content used by implementation and testing. |

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

## Workflow issue metadata

Represent this metadata using provider-native fields when available.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | `usecase`, or provider issue type/label/field equivalent. |
| `title` | yes | Short user-facing goal. |
| `status` | yes | Workflow status mapped to provider status. |
| `knowledge_page` | optional until published | Link to curated page after publication. |
| `actors` | recommended | Actor names or slugs. Metadata when possible; body otherwise. |
| `supersedes` | optional | Prior use case this one replaces. Visible body section required when present. |
| `related` | optional | Related tasks, specs, reviews, research, or pages. |
| `labels` | optional | Provider labels/tags. |

Provider identity replaces local integer ids. Use GitHub issue numbers or Jira keys for the workflow issue.

## Curated page metadata

Represent this metadata using provider-native page properties, labels, metadata block, or index metadata when available.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | `usecase`. |
| `title` | yes | Same or clearer title than the workflow issue. |
| `source_issue` | yes | Link back to the workflow issue that owns discovery and discussion. |
| `status` | recommended | Published/stable state when supported by provider. |
| `actors` | recommended | Actor names or slugs. |
| `supersedes` | optional | Prior curated use case page. |
| `related` | optional | Related tasks, specs, reviews, research, architecture, or domain pages. |

## Lifecycle

Recommended workflow issue lifecycle:

```text
draft → ready | discarded
ready → implementing | draft | discarded
implementing → revising | blocked | shipped | discarded
revising → ready | discarded
blocked → ready | discarded
shipped → superseded | discarded
superseded → terminal
discarded → terminal
```

Status meaning:

- `draft` — The use case is being discovered or shaped.
- `ready` — The curated content is sufficient to drive implementation work.
- `implementing` — Tasks are actively implementing the use case.
- `revising` — Implementation surfaced a use case change; curated content needs revision.
- `blocked` — Progress is blocked by a decision or missing input.
- `shipped` — Running system reflects the use case.
- `superseded` — A newer use case replaces this one.
- `discarded` — No longer applicable.

Provider mappings may vary:

- GitHub: Issue Field status when available.
- Jira: configured Jira workflow statuses.

The curated page should reflect stable content. Workflow transitions and discussion live on the issue.

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

## Related

- <provider-native ref or URL>
```

Optional sections:

- `## Target` — when the issue exists to revise or review an existing use case page.
- `## Resume` — current-state snapshot while shaping. See `./issue-body.md`.
- `## Log` — use sparingly; prefer provider comments for discussion. See `./issue-body.md`.

Use provider comments for conversation, interview notes, and feedback threads.

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

- `## Actors` — actor list when not obvious from metadata.
- `## Validation` — user-visible input constraints, limits, or required formats.
- `## Error Handling` — what the actor sees when things fail.
- `## Dependencies` — narrative dependencies on other use cases, specs, or pages only when the active provider binding allows a body fallback. Do not include blocked/dependency sections for GitHub workflow issues.
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

Tasks that implement the use case should link to the curated page or workflow issue in `## Implements`.

Prefer the curated page when it exists, because it contains the stable implementation-facing content. Use the workflow issue when the curated page has not been published yet.

## Wiki/knowledge side effects

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
4. Link parent and child artifacts using provider relationships when available and body links always.
5. Do not use supersession unless an older shipped/published use case is being replaced.

## Common mistakes

- Writing internal system mechanics into the use case.
- Publishing a curated page before the user-visible flow is stable.
- Leaving the workflow issue without a link to the curated page after publication.
- Putting long discovery discussion into the curated page.
- Creating tasks from a use case whose flow or expected outcome is still unclear.
- Using local projection paths or local integer ids as provider-backed identity.

## Do not

- Do not create the curated page before the workflow issue unless importing existing documents.
- Do not store use case discussion only in the knowledge page.
- Do not pack multiple actor goals into one use case.
- Do not auto-trigger a skill just because a use case is being written; follow the authoring resolver policy.
