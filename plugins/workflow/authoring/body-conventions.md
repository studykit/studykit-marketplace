# Workflow Body Conventions

Cross-cutting body-level rules for workflow artifacts written to provider-backed issues, provider-backed knowledge pages, and optional filesystem projections.

Shared metadata rules: `./metadata-contract.md`.
Issue body rules: `./issue-body.md`.
Knowledge body rules: `./knowledge-body.md`.
Provider-specific rules live under `./providers/`.

## Scope

These rules apply to the visible body text of every workflow artifact.

The body is the portable human-readable fallback. Provider-native metadata may store the same relationships more precisely, but important relationships must still be visible in the body.

## Section heading form

A body section is an H2 Markdown heading in Title Case with spaces, followed by free-form Markdown until the next H2 or end of body.

```markdown
## Situation

A meeting just ended; absent teammates need the outcome.

## Flow

1. Open the meeting record.
2. Click "share summary".
3. Confirm the channel.
```

Rules:

- Section boundary is `## Heading` at column 0, on its own line.
- Heading text is Title Case with single spaces.
- Do not put an H1 in the body when the provider already owns the title.
- Use H3 and deeper headings only inside an H2 section.
- Unknown H2 headings are tolerated when they are useful and well-formed.
- Avoid stray content above the first H2 unless the provider template requires a short summary block.

Common H2 names:

- `## Description`
- `## Context`
- `## Specification`
- `## Acceptance Criteria`
- `## Unit Test Strategy`
- `## Target`
- `## Implements`
- `## Dependencies`
- `## Related`
- `## Sources`
- `## Change Log`
- `## Decision Log`
- `## Open Questions`
- `## Rejected Alternatives`
- `## Resume`

## Reference form

Use provider-native references in body text.

| Target | Preferred body form |
| --- | --- |
| GitHub issue or pull request in the configured repository | `#123` |
| GitHub issue or pull request in another repository on the same host | `owner/repo#123` |
| Jira issue | `PROJ-123` |
| Confluence page | Page title, Smart Link, or full URL |
| GitHub repository `wiki/` page | Repository-relative path or Markdown link |
| External source | Standard Markdown link |

Examples:

```markdown
## Target

- #123
- PROJ-456
- [Auth Session v2](https://example.atlassian.net/wiki/spaces/ENG/pages/123456789/Auth+Session+v2)
```

```markdown
## Sources

- [Vendor API documentation](https://example.com/docs)
```

Rules:

- Prefer the shortest native reference that is unambiguous in the configured provider context.
- Use full URLs when a short reference would be ambiguous outside its provider.
- Do not require local Markdown paths for provider-backed artifacts.
- Do not introduce workflow-local numeric IDs when provider identity already exists.
- The adapter resolves references through `workflow.config.yml`, provider context, and git remotes.

## Relationship sections

When a relationship matters, show it in a body section even if provider metadata also stores it.

Use these section names consistently:

- `## Target` — artifact reviewed or affected by a review item.
- `## Implements` — use case, requirement, spec, or knowledge artifact implemented by a work item.
- `## Dependencies` — blocking or ordering relationship.
- `## Related` — useful non-blocking relationship.
- `## Supersedes` — older knowledge artifact replaced by this one.
- `## Sources` — external evidence, vendor docs, papers, or decision inputs.
- `## Change Log` — semantic cause index on knowledge pages.

## Lists and bullets

Use ordinary Markdown lists unless a type-specific contract gives a stricter shape.

Relationship lists should keep one referenced artifact per bullet:

```markdown
## Dependencies

- PROJ-123
- #45
```

Change-log entries should use this shape:

```markdown
- YYYY-MM-DD — <provider-ref-or-link> — <concise reason>
```

Example:

```markdown
- 2026-05-13 — PROJ-123 — Updated the latency target after load-test validation.
```

## Comments versus body

Use the body for the current structured artifact.
Use provider comments for discussion, progress notes, review conversations, and raw investigation notes.

Do not copy long comment threads into the body. Summarize the resulting decision or current state in the relevant body section instead.

## Filesystem projections

If an adapter creates local Markdown files, treat them as projections of provider artifacts.

- Local paths are not canonical identity in provider-backed mode.
- Do not use projection paths in commits, branches, or provider comments unless the local path itself is the topic.
- Projection files may include normalized metadata for tooling, but authoring should still follow provider-native references.

## Cross-references

- `./metadata-contract.md` — shared metadata and identity rules.
- `./issue-body.md` — issue-backed body rules.
- `./knowledge-body.md` — knowledge-backed body rules.
