# Workflow Epic Authoring

A workflow epic is an **issue-backed coordination parent** for a larger goal delivered by multiple child work items.

An epic may represent a user-facing feature, platform capability, subsystem implementation effort, migration, stabilization campaign, or cross-cutting quality initiative. It is not an implementation unit. The work is done by its children.

Epics are stored in the configured issue backend.

Companion contracts:

- `./body-conventions.md`
- Issue rules: `./issue-authoring.md`

## Storage role

`epic` is stored in the issue backend.

Use canonical issue identity. Do not use local integer ids.

## When to create an epic

Create an epic when one or more of these holds:

- A larger goal will be split into multiple child work items.
- Several existing issues need a shared coordination home.
- Cross-cutting decisions affect more than one child.
- Integration-level acceptance criteria span several children.
- A feature, migration, or stabilization campaign needs progress visibility.

Do not create an epic when:

- One child issue is enough.
- Issues are unrelated and have no shared narrative.
- A spec or architecture page is the real home for the decision.
- The work is only a single implementation task.

## Required metadata

Represent this metadata structurally when possible. If a field cannot be stored structurally, include the value in the body when the selected authoring files require it.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | Always `epic`. Use issue type or hierarchy type depending on backend support. |
| `title` | yes | Short summary of the coordinated goal. |
| `status` | yes | Workflow lifecycle status. |
| `tags` | optional | Classification tags. |

## Relationships

Represent relationships structurally when possible. Body representation depends on the selected provider and type authoring files.

| Relationship | Required | Notes |
| --- | --- | --- |
| `children` | recommended | Child issues. Use backend hierarchy links when available and always include `## Children`. |
| `related` | optional | Related specs, use cases, research, reviews, pages, or issues. |

Do not use implementation-only fields such as `implements`, `spec`, `depends_on`, artifact links, or implementation cycle counters on an epic. Children carry implementation anchors and dependencies.

## Lifecycle

Recommended semantic lifecycle:

```text
open → done | discarded
done → open | discarded
discarded → terminal
```

Status meaning:

- `open` — Active coordination home for one or more child items.
- `done` — The coordinated outcome is complete or no longer active.
- `discarded` — The grouping is no longer valid or useful.

Status and hierarchy mapping depend on the configured issue backend.

`done` is author-judged. Do not assume children automatically close the epic. If one child remains active, prefer keeping the epic `open` unless the remaining work has moved elsewhere.

Discarding an epic does not automatically discard children. Move or update children explicitly when the grouping changes.

## Children and membership

Use structured hierarchy when available.

Always include a visible `## Children` section as the human-readable index.

```markdown
## Children

- #123 — Add login API
- #124 — Add login retry tests
- PROJ-456 — Fix token refresh regression
```

Keep child entries readable. If a child moves, is discarded, or changes scope, annotate the entry or add a new note rather than silently deleting history.

## Shared narrative

The epic is the home for narrative that spans children:

- Cross-child decisions.
- Integration constraints.
- Shared blockers.
- Sequencing choices.
- Scope changes that affect several children.

Use comments for discussion. Keep the epic body as the current coordination summary.

Children should link to the epic when their own approach depends on epic-level narrative.

## Body shape

Required:

```markdown
## Description

<what the children together accomplish and why they are grouped>

## Children

- <child ref> — <short label>
```

Recommended:

```markdown
## Coordination Notes

<current cross-child decisions, constraints, or sequencing notes>
```

Optional sections:

- `## Acceptance Criteria` — integration outcome not naturally owned by a single child.
- `## Related Work` — use cases, specs, research, reviews, architecture, domain, or NFR pages.
- `## Resume` — current-state snapshot while open. See `./body-conventions.md`.
- `## Why Discarded` — reason when discarded. See `./body-conventions.md`.

Unknown Title Case H2 headings are tolerated.

## Acceptance criteria

Epic acceptance criteria are optional.

Use them only for integration outcomes that are not already covered by child issues.

Examples:

- End-to-end flow works across several tasks.
- Migration is complete across all components.
- Stabilization campaign reduces a class of failures below a target threshold.

Do not duplicate every child acceptance criterion in the epic.

## Relationship to knowledge artifacts

Epics coordinate work. They do not define the product, architecture, or implementation contract.

Use knowledge artifacts for durable content:

- User-facing behavior → use case curated page.
- Implementation contract → spec.
- Component shape → architecture.
- Vocabulary → domain.
- Non-functional target → nfr.

If an epic discussion creates durable knowledge, update the relevant knowledge page and add a `## Change Log` entry there.

## Done rule

An epic should not be marked `done` until:

- The coordinated outcome has been reached or explicitly descoped.
- Children are done, discarded, or moved elsewhere.
- Integration-level acceptance criteria are satisfied or explicitly waived.
- Relevant knowledge pages are updated.
- Remaining feedback is captured as review items or follow-up issues.

## Comments and discussion

Use comments for:

- Coordination discussion.
- Cross-child progress updates.
- Blocker resolution.
- Scope negotiation.

Keep the epic body as the current compact coordination surface.

## Common mistakes

- Using an epic as a spec or architecture document.
- Duplicating all child details in the epic body.
- Missing `## Children`.
- Marking `done` while active children still depend on the epic.
- Nesting epics without explicit backend support and configuration.
- Using local projection paths or local integer ids as canonical identity.

## Do not

- Do not put implementation details or unit test strategy in the epic.
- Do not use `implements`, `spec`, `depends_on`, or implementation cycle fields on an epic.
- Do not discard children automatically when discarding an epic.
- Do not store durable design decisions only in the epic; update the relevant knowledge artifact.
- Do not auto-trigger a skill just because an epic is being written; follow the authoring resolver policy.
