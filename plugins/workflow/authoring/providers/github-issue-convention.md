# GitHub Issue Provider Convention

Provider-wide convention rules for workflow artifacts stored as GitHub Issues.

## Scope

Use these rules for workflow issue artifacts stored in GitHub Issues.

This file defines GitHub-wide issue writing rules only. Provider metadata mapping and cache projection rules belong in `./github-issue-metadata.md`. Provider relationship projection and pending-write rules belong in `./github-issue-relationships.md`. Artifact-specific body structure and relationship body sections belong in the matching GitHub issue type authoring file.

## Identity and references

Use GitHub-native references in visible text.

- Same repository: `#123`.
- Cross repository on the same host: `owner/repo#123`.
- Outside GitHub-native contexts or when ambiguous: full issue URL.

Resolve `#123` using `.workflow/config.yml` first, then the configured git remote, then `origin`.

GitHub Enterprise host, owner, and repo should be inferred from the configured remote when explicit config is absent.

## Relationships

Read `./github-issue-relationships.md` for provider relationship storage, cache projection, and pending-write rules.

Do not duplicate GitHub-native parent/child or dependency relationships in body sections when GitHub stores them natively.

Relationship body sections that are not parent or dependency relationships are artifact-specific and belong in the matching GitHub issue type authoring file.

## Comments and logs

Use GitHub comments for discussion, feedback, and work logs.

Do not create a body `## Log` section. Use GitHub comments for human-readable notes and GitHub timeline/events as provider audit history. Do not duplicate routine status changes in the issue body.

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

Provider wrapper commands perform the requested write and verification. The caller is responsible for following the authoring resolver/read policy before invoking a write.
