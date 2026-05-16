# GitHub Issue Review Authoring

Provider-specific binding for workflow `review` issues stored as GitHub Issues.

Read after:

- `../common/review-authoring.md`
- `./github-issue-convention.md`
- `./github-issue-metadata.md`
- `./github-issue-relationships.md`
- `./github-issue-anti-patterns.md`

## Scope

Use this binding when feedback needs a separate GitHub issue for independent
tracking. If the feedback is local to an existing GitHub issue and can be
resolved as part of that issue, use an issue comment instead.

## Issue comment feedback

Use a GitHub issue comment when the feedback is local to the issue and can be
resolved as part of that issue.

Recommended comment shape:

```markdown
Review feedback: <finding, gap, or question>

Why it matters:
- <short reason>

Suggested fix:
- <short action>
```

Do not add `## Target`; the containing issue is the target. Keep the comment
short. If the discussion needs independent tracking, create a separate review
issue instead.

## Separate review issue body structure

Use this final GitHub body structure for `review` issues.

Common required sections are defined by `../common/review-authoring.md`:

- `## Description`

Common optional sections are defined by `../common/review-authoring.md` and `../common/issue-body.md`:

- `## Resume`
- `## Suggested Fix`
- `## Evidence`

GitHub-specific H2 sections for this type: `## Target`.

GitHub-specific rules:

- Use a GitHub dependency relationship when the target is a GitHub issue.
- Add `## Target` only when the target is not represented by a provider-native
  relationship.
- Use body links in `## Target` for non-issue targets.
- Do not create a separate review issue only to record local discussion on an existing issue.

## GitHub labels

Apply the GitHub label `review` to identify this issue type.

## GitHub issue target relationship

When a separate review issue targets a GitHub issue, represent the target with
the GitHub dependency relationship. The target issue should be blocked by the
review issue until the concern is resolved.

Do not rely on body text alone for GitHub issue-to-issue review targets.

### `## Target`

Use only when the review target is not already represented by a provider-native
relationship.

Content:

- Start with one bullet per target.
- Use `#123` for same-repository issues.
- Use `owner/repo#123` for cross-repository GitHub issues.
- Use Markdown links for repository knowledge pages, Confluence pages, or external targets.
- Add at most one short clarifying phrase after the reference when the target relationship is not obvious.
- Do not add `## Target` only to duplicate a GitHub dependency relationship.
- Do not copy the target issue body into the review.

Example:

```markdown
## Target

- [Architecture](wiki/workflow/architecture.md)
```
