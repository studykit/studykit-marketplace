# GitHub Wiki Provider Authoring

Provider binding rules for workflow artifacts stored as GitHub Wiki pages.

Read with the semantic authoring file for the artifact type, plus:

- `../metadata-contract.md`
- `../knowledge-body.md`

## Scope

Use this binding for knowledge-backed workflow artifacts stored in GitHub Wiki:

- `spec`
- `architecture`
- `domain`
- `context`
- `actors`
- `nfr`
- `ci`
- curated side of `usecase`
- curated side of `research`

## Identity and references

GitHub Wiki identity is path/title based within the wiki repository.

Use page title, wiki page URL, or provider-native wiki link syntax in visible text.

Store or compute:

- host
- owner
- repo
- wiki path
- title
- last seen commit or version marker when needed for conflict detection

GitHub Wiki does not provide an obvious page-level stable opaque ID like GitHub Issue `node_id`.

## Type mapping

GitHub Wiki metadata is weaker than issue metadata.

Use one of these patterns:

1. Page frontmatter or metadata block.
2. A generated index page.
3. Both, if search and human browsing both need metadata.

This remains an open design area. Prefer the simplest approach that the provider wrapper can read and update reliably.

## Status mapping

For knowledge artifacts that have lifecycle state, store status in page metadata when available.

If metadata is unavailable, include visible state in the body.

## Relationships

Use visible body sections for important relationships:

- `supersedes` → `## Supersedes`
- workflow causes → `## Change Log`
- non-blocking links → `## Related Work`
- external evidence → `## Sources`

Use Markdown links to full URLs when the target is outside the wiki or when provider-native wiki links would be ambiguous.

## Change log

Every material page edit should include a concise `## Change Log` entry that links to the causing workflow artifact.

```markdown
## Change Log

- 2026-05-13 — #456 — Clarified async retry boundary.
```

Do not duplicate GitHub Issue discussion in the wiki page.

## Git-backed editing

GitHub Wiki is a separate git repository.

Provider wrapper commands should treat wiki writes as git operations against the wiki repository and should avoid ad-hoc edits that bypass conflict detection.

## Transport

Preferred native transport:

- `git` against the wiki repository.

MCP is fallback transport.

Provider wrapper commands must enforce the authoring resolver/read-ledger guard before writes, regardless of transport.
