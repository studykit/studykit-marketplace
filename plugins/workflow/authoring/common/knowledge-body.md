# Workflow Knowledge Body Conventions

Body-level rules for workflow artifacts stored in a knowledge backend.

Knowledge-backed artifacts include `spec`, `architecture`, `domain`, `context`, `actors`, `nfr`, `ci`, and the curated output side of `usecase` and `research`.

## Purpose

Knowledge pages contain curated, current, durable content.

They should not contain raw discussion, transient questions, or detailed work logs. Those belong in the issue backend.

## Section heading form

A knowledge body section is an H2 Markdown heading in Title Case with spaces, followed by free-form Markdown until the next H2 or end of body.

```markdown
## Context

The current implementation contract depends on the provider boundary.

## Specification

The provider writes the canonical field and the page body records the durable meaning.
```

Rules:

- Section boundary is `## Heading` at column 0, on its own line.
- Heading text is Title Case with single spaces.
- Do not put an H1 in the body when the page title is stored separately.
- Use H3 and deeper headings only inside an H2 section.
- Unknown H2 headings are tolerated when they are useful and well-formed.
- Avoid stray content above the first H2 unless the selected artifact template requires a short summary block.

Common knowledge H2 names:

- `## Context`
- `## Specification`
- `## Sources`
- `## Change Log`
- `## Decision Log`
- `## Open Questions`
- `## Rejected Alternatives`
- `## Supersedes`
- `## Related Work`

## Reference form

Use stable, readable references in knowledge body text.

| Target | Preferred body form |
| --- | --- |
| Issue-backed artifact | Issue reference from the selected issue backend |
| Knowledge-backed artifact | Page, document, or file reference from the selected knowledge backend |
| External source | Standard Markdown link |

Rules:

- Prefer the shortest reference that is unambiguous in the configured project.
- Use full URLs when a short reference would be ambiguous outside its source system.
- Do not require local Markdown paths for artifacts whose canonical identity is not a local file.
- Do not introduce workflow-local numeric IDs when canonical identity already exists.

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

Version history records who changed what and when. `## Change Log` records why the page changed and which workflow artifact caused it.

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

- 2026-05-13 — [PROJ-123](https://example.com/issues/PROJ-123) — Published initial OAuth integration evaluation.
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

- [Auth Session v1](https://example.com/pages/auth-session-v1)
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

## Identity and authoring surface

Use the canonical page, document, or file identity supplied by the selected knowledge backend. Do not treat local projection paths as canonical identity unless the artifact is truly file-backed.

Keep workflow meaning in the visible body sections defined by type-specific authoring files.

Provider and cache metadata are operational state, not authoring content. Use provider workflows or cache sidecars for that state. Duplicate provider state in the body only when readers need it.

The visible body remains the durable reading surface for humans and agents.

## Lists and bullets

Use ordinary Markdown lists unless a type-specific contract gives a stricter shape.

Relationship lists should keep one referenced artifact per bullet.

Change-log entries should use this shape:

```markdown
- YYYY-MM-DD — <artifact-ref-or-link> — <concise reason>
```

## Filesystem projections

If workflow tooling creates local Markdown files as projections of external knowledge artifacts, do not treat projection paths as canonical identity.

- Do not use projection paths in commits, branches, or comments unless the local path itself is the topic.
- Do not edit projection metadata as authoring state. Use provider workflows or cache sidecars for provider state, and keep canonical artifact references in visible body text.
