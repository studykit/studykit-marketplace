# Workflow Knowledge Body Conventions

Body-level rules for workflow artifacts stored in a knowledge backend such as Confluence or GitHub repository `wiki/`.

Knowledge-backed artifacts include `spec`, `architecture`, `domain`, `context`, `actors`, `nfr`, `ci`, and the curated output side of `usecase` and `research`.

Common body rules: `./body-conventions.md`.
Shared metadata rules: `./metadata-contract.md`.

## Purpose

Knowledge pages contain curated, current, durable content.

They should not contain raw discussion, transient questions, or detailed work logs. Those belong in the issue backend.

## Curated content only

Write knowledge pages as reference material:

- Current decisions.
- Stable requirements.
- Specifications.
- Domain concepts.
- Architecture shape.
- Final research findings.
- Final use case descriptions.

Avoid:

- Long discussion transcripts.
- Untriaged feedback.
- Session notes.
- Raw scratch work.
- Routine progress logs.

## `## Change Log`

Every material knowledge-page change should include a concise semantic cause entry.

Provider version history records who changed what and when. `## Change Log` records why the page changed and which workflow artifact caused it.

```markdown
## Change Log

- 2026-05-13 — #456 — Clarified async retry boundary.
- 2026-05-14 — PROJ-123 — Updated latency target.
```

Rules:

- One bullet per material change.
- Keep entries concise.
- Link to the causing issue, review, task, use case workflow issue, or research workflow issue.
- Do not duplicate the discussion from the causing issue.
- Append new entries; do not rewrite history except for obvious formatting errors.

## Links back to workflow items

When a knowledge page is created or materially updated because of an issue-backed artifact, include a visible link back to that artifact.

Examples:

```markdown
## Change Log

- 2026-05-13 — [PROJ-123](https://example.atlassian.net/browse/PROJ-123) — Published initial OAuth provider evaluation.
```

```markdown
## Related Work

- #123
- PROJ-456
```

## Relationship sections

Use visible relationship sections when relevant.

### `## Supersedes`

For specs or curated documents that replace older documents.

```markdown
## Supersedes

- [Auth Session v1](https://example.atlassian.net/wiki/spaces/ENG/pages/111/Auth+Session+v1)
```

### `## Related Work`

For issue-backed artifacts that informed or currently depend on this page.

```markdown
## Related Work

- PROJ-123
- #456
```

### `## Sources`

For research reports or decisions that rely on external evidence.

```markdown
## Sources

- [Vendor API documentation](https://example.com/docs)
```

## Page comments

Use page comments for page-local review and clarification only.

If feedback must be triaged, prioritized, assigned, or resolved through workflow, create a `review` item in the issue backend instead of relying on a page comment.

## Provider metadata

Store metadata in provider-native fields when available:

- Confluence labels or page properties.
- GitHub repository `wiki/` page frontmatter or index page metadata when needed.

The visible body remains the fallback for humans and agents.
