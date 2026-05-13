# Confluence Page Provider Authoring

Provider binding rules for workflow artifacts stored as Confluence pages.

Read with the semantic authoring file for the artifact type, plus:

- `../metadata-contract.md`
- `../knowledge-body.md`

## Scope

Use this binding for knowledge-backed workflow artifacts stored in Confluence:

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

Use Confluence page title or Smart Link in visible text.

Use full page URLs when writing portable Markdown-like text or when the target context may not render Smart Links.

Provider metadata should use page ID scoped by Confluence site.

Resolve page references using `.workflow/config.yml`, including site and space.

## Type mapping

Prefer Confluence page properties or labels for workflow type metadata.

Suggested labels:

- `workflow:type/spec`
- `workflow:type/architecture`
- `workflow:type/domain`

Use page hierarchy for organization, not as the only source of type metadata.

## Status mapping

For knowledge artifacts that have lifecycle state, use page properties or labels when available.

Examples:

- `workflow:status/draft`
- `workflow:status/active`
- `workflow:status/deprecated`
- `workflow:status/superseded`

The visible page body should still communicate important state when readers need it.

## Relationships

Use Confluence links and Jira/Atlassian Smart Links for visible relationships.

Use page properties, labels, or link metadata for structured relationships when available.

Always include visible body sections for important relationships:

- `supersedes` → `## Supersedes`
- workflow causes → `## Change Log`
- non-blocking links → `## Related Work`
- external evidence → `## Sources`

## Change log

Every material page edit should include a concise `## Change Log` entry that links to the causing workflow artifact.

```markdown
## Change Log

- 2026-05-13 — PROJ-123 — Published initial OAuth provider evaluation.
```

Do not duplicate Jira/GitHub discussion in the page.

## Page comments

Use Confluence comments for page-local clarification.

If feedback must be triaged, assigned, prioritized, or resolved, create a workflow `review` issue in the issue backend.

## Versioning and conflicts

Confluence updates require version-aware writes. Provider wrapper commands must read the current page version before updating and must detect version conflicts.

## Transport

Preferred native transport:

- REST wrapper for Confluence Cloud APIs.

MCP is fallback transport.

Provider wrapper commands must enforce the authoring resolver/read-ledger guard before writes, regardless of transport.
