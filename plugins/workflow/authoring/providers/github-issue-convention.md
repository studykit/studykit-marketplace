# GitHub Issue Provider Convention

Provider-wide convention rules for workflow artifacts stored as GitHub Issues.

## Scope

Use these rules for workflow issue artifacts stored in GitHub Issues.

This file defines GitHub-wide issue writing conventions only.
Provider metadata boundaries belong in `./github-issue-metadata.md`.
Provider relationship boundaries belong in `./github-issue-relationships.md`.

## Identity and references

Use GitHub-native references in visible text.

- Same repository: `#123`.
- Cross repository on the same host: `owner/repo#123`.
- Outside GitHub-native contexts or when ambiguous: full issue URL.

Resolve `#123` using `.workflow/config.yml` first, then the configured git remote, then `origin`.

GitHub Enterprise host, owner, and repo should be inferred from the configured remote when explicit config is absent.

## Comments and logs

Use GitHub comments for discussion, feedback, and work logs.

Do not create a body `## Log` section. Use GitHub comments for human-readable notes and GitHub timeline/events as provider audit history. Do not duplicate routine status changes in the issue body.

## Implementation summary comments

When updating an issue after implementation, keep the comment concise.

Recommended shape:

```markdown
Implemented <short outcome>.

Why:
- <reason this change was needed>

Summary:
- <material change>
- <material change>

Validation: local workflow checks passed.

- <short-sha>
```

Rules:

- Include `Why:` when the motivation is not obvious, the change removes
  behavior or documentation, or the work changes an agent, provider, or
  authoring boundary.
- Do not paste unit test output, test file lists, or verbose validation logs into issue comments.
- Do not include full commit URLs when GitHub can autolink a short SHA.
- Prefer one short SHA bullet per relevant commit.
- Keep implementation details high-level; link or reference changed files only when the distinction matters.

## Closing keywords

Only generate GitHub closing keywords such as `Fixes #123` when the workflow intentionally wants GitHub to auto-close an issue.

Do not use closing keywords merely to express a relationship.
