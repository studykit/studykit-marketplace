# GitHub Issue Provider Convention

Provider-wide convention rules for issue-backed items stored as GitHub Issues.

## Scope

Use these rules for issue-backed items stored in GitHub Issues.

This file defines GitHub-wide issue writing conventions only.
Provider relationship boundaries belong in `./github-issue-relationships.md`.
GitHub body anti-patterns belong in `./github-issue-anti-patterns.md`.

## Identity and references

Use GitHub-native references in visible text.

- Same repository: `#123`.
- Cross repository on the same host: `owner/repo#123`.
- Outside GitHub-native contexts or when ambiguous: full issue URL.

Resolve `#123` using `.workflow/config.yml` first, then the configured git remote, then `origin`.

GitHub Enterprise host, owner, and repo should be inferred from the configured remote when explicit config is absent.

## Related body section

`## Related` is available to any GitHub issue type.

Use `## Related` for human-readable references that are not stored as
GitHub-native relationships. This includes implementation anchors, non-issue
review targets, follow-up work, external pages, or other soft references.

Do not use `## Related` for parent, child, blocking, or dependency
relationships that are stored as GitHub-native relationships.

When used:

- Start with one bullet per related reference.
- Keep descriptions short.

## Dependency body fallback

Use GitHub issue dependency relationships for blocking or ordering dependencies whenever possible.

Use `## Dependencies` only when dependency relationships cannot be stored natively and the issue body needs human-readable dependency context.

When used:

- Start with one bullet per dependency.
- Use GitHub issue references or full URLs whenever possible.
- Keep the section limited to blocking or ordering dependencies.

## Provider update intent

When asking `workflow-operator` to update provider-owned GitHub issue fields,
provide only the values needed for the requested update.

Generic supported update intents:

- Issue reference, plus desired title when changing the GitHub issue title.
- Issue reference, plus desired workflow type when explicitly changing the workflow type.

Do not ask for generic status, priority, tag, label, or GitHub Project field
writes from this contract. Those writes require a separate project-specific
workflow extension that documents and supports the selected field.

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
