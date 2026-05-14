# GitHub Issue Provider Authoring

Provider binding rules for workflow artifacts stored as GitHub Issues.

Read with the semantic authoring file for the artifact type, plus:

- `../metadata-contract.md`
- `../issue-body.md`

## Scope

Use this binding for issue-backed workflow artifacts stored in GitHub Issues:

- `task`
- `bug`
- `spike`
- `epic`
- `review`
- workflow side of `usecase`
- workflow side of `research`

## Identity and references

Use GitHub-native references in visible text.

- Same repository: `#123`.
- Cross repository on the same host: `owner/repo#123`.
- Outside GitHub-native contexts or when ambiguous: full issue URL.

Resolve `#123` using `.workflow/config.yml` first, then the configured git remote, then `origin`.

GitHub Enterprise host, owner, and repo should be inferred from the configured remote when explicit config is absent.

## Type mapping

Use labels as the v1 type mapping for GitHub Issues.

GitHub Issue Types are not consistently available across repositories and organizations. The GitHub provider should therefore treat labels as the portable default.

Recommended labels:

- `task`
- `bug`
- `spike`
- `epic`
- `review`
- `usecase`
- `research`

Do not require a scope label by default. Repository-specific scope labels may be configured later when a project needs extra filtering.

Fallback order:

1. artifact-type label.
2. Repository-specific configured label mapping.
3. GitHub Issue Type only when setup explicitly enables it.
4. Structured body section or hidden marker only when metadata is unavailable.

## Status mapping

Canonical workflow status should use GitHub Issue Fields when available.

Use GitHub Projects fields for board, roadmap, and planning views, not as the primary artifact identity.

Fallback order:

1. GitHub Issue Field.
2. GitHub Project field when the project is the configured planning surface.
3. Label such as `workflow/status:open`.
4. Body section only when metadata is unavailable.

## Relationships

Use native GitHub relationships when they match workflow semantics.

- Parent/child: GitHub sub-issues when available.
- Dependencies: GitHub issue dependencies when available.
- Labels and fields: use for type, status, priority, and routing metadata.

Do not duplicate provider-native parent/child or dependency relationships in body sections when GitHub stores them natively.

Never write dedicated blocked/dependency sections for GitHub native dependency data. This includes `## Dependencies`, `## Blocked`, `## Blocked By`, `## Blocking`, and blocked-on resume slots. Use GitHub dependency metadata through the provider wrapper and put discussion or rationale in comments when needed.

Required body sections by relationship:

- `target` → `## Target`
- `implements` → `## Implements`
- `related` → `## Related`
- `depends_on` → GitHub dependency metadata only. Do not add a blocked/dependency body section.

## Review items

A workflow `review` is always a GitHub Issue.

It must include:

```markdown
## Target

- #123
```

Use metadata for `target` when suitable fields or links exist, but do not omit the body section.

## Comments and logs

Use GitHub comments for discussion, feedback, and work logs.

Use GitHub timeline/events as provider audit history. Do not duplicate routine status changes in the issue body.

## Implementation summary comments

When updating an issue after implementation, keep the comment concise.

Recommended shape:

```markdown
Implemented <short outcome>.

Summary:
- <material change>
- <material change>

Validation: local workflow checks passed.

- <short-sha>
```

Rules:

- Do not paste unit test output, test file lists, or verbose validation logs into issue comments.
- Do not include full commit URLs when GitHub can autolink a short SHA.
- Prefer one short SHA bullet per relevant commit.
- Keep implementation details high-level; link or reference changed files only when the distinction matters.

## Closing keywords

Only generate GitHub closing keywords such as `Fixes #123` when the workflow intentionally wants GitHub to auto-close an issue.

Do not use closing keywords merely to express a relationship.

## Transport

Preferred native transport:

- `gh`
- `gh api`

MCP is fallback transport.

Provider wrapper commands must enforce the authoring resolver/read-ledger guard before writes, regardless of transport.
