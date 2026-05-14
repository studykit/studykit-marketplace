# Workflow Issue Body Conventions

Body-level rules for workflow artifacts stored in an issue backend such as GitHub Issues or Jira.

Issue-backed artifacts include `task`, `bug`, `spike`, `epic`, `review`, and the workflow side of `usecase` and `research`.

Common body rules: `./body-conventions.md`.
Shared metadata rules: `./metadata-contract.md`.

## Purpose

Issue bodies should provide the durable, readable summary of the work item. Provider comments and history carry discussion, work logs, and audit events.

Do not turn the issue body into a transcript. Keep it current and structured.

## Required relationship sections

When a relationship exists, represent it in the body unless the provider-specific binding stores it natively and forbids duplication.

### `## Target`

Required for `review` items. Lists the artifact or artifacts being reviewed.

```markdown
## Target

- #123
- [Architecture](https://example.atlassian.net/wiki/spaces/ENG/pages/123456789/Architecture)
```

### `## Implements`

Required when a work item implements a use case, requirement, or curated knowledge artifact.

```markdown
## Implements

- [Login Usecase](https://example.atlassian.net/wiki/spaces/ENG/pages/234567890/Login+Usecase)
```

### `## Dependencies`

Default body fallback for providers that do not store blocking or ordering dependencies natively.

Do not add `## Dependencies`, `## Blocked`, `## Blocked By`, `## Blocking`, or equivalent blocked-related sections to GitHub issue bodies for native GitHub dependency relationships. Store those relationships through provider-native dependency metadata instead.

Non-GitHub fallback example:

```markdown
## Dependencies

- PROJ-123
- PROJ-456
```

### `## Related`

Use for non-blocking cross-references that are useful to readers.

```markdown
## Related

- [Auth Session v2](https://example.atlassian.net/wiki/spaces/ENG/pages/123456789/Auth+Session+v2)
```

## `## Description`

Most issue-backed artifacts should include `## Description` unless the type-specific contract requires a more specific section set.

Use it for:

- What needs to be done or resolved.
- Why it matters.
- Relevant scope boundaries.
- Links to curated knowledge artifacts.

Keep provider-native discussion in comments instead of repeatedly appending to `## Description`.

## `## Acceptance Criteria`

Use for implementation work when done-ness must be explicit.

```markdown
## Acceptance Criteria

- User can retry login after a transient provider error.
- Retry behavior is covered by unit tests.
```

## `## Resume`

Purpose: current-state snapshot for a future session.

Use when the item is mid-flight and the current state is not obvious from metadata, body, or comments.

Suggested slots:

- **Approach.** Current strategy.
- **Waiting for.** External input or sequencing note, only when the provider binding allows it. Do not use this slot to duplicate GitHub native dependency metadata.
- **Open questions.** Questions awaiting input.
- **Next.** Next concrete step.

Rewrite `## Resume` in place. Do not preserve history here.

## `## Log`

Prefer provider comments or history for routine logs. Use body `## Log` only when provider comments are unavailable or when the type-specific authoring contract requires an in-body narrative.

If used, entries are append-only dated bullets.

```markdown
## Log

- 2026-05-13 10:15 — Switched from Repository-layer caching to Service-layer caching because the key needs user context.
```

## `## Why Discarded`

Use when an item is intentionally abandoned and provider status alone does not explain why.

```markdown
## Why Discarded

- 2026-05-13 10:15 — Superseded by PROJ-456.
```

## Comments and provider history

Use provider-native comments for:

- Discussion.
- Review feedback.
- Work notes.
- Investigation notes that are not final curated output.

Use provider-native history for audit facts such as author, timestamp, state changes, labels, and field changes.

## Cross-references

Use provider-native short references where possible:

- GitHub same-repo issue: `#123`.
- Jira issue: `PROJ-123`.
- Confluence page: page title, Smart Link, or full URL.

The provider adapter resolves these through `.workflow/config.yml`.
