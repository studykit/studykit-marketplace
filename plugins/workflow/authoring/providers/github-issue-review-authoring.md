# GitHub Issue Review Authoring

Provider-specific binding for `review` issues stored as GitHub Issues.

Read after:

- `../common/review-authoring.md`
- `./github-issue-convention.md`
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

Keep the comment short. If the discussion needs independent tracking, create a
separate review issue instead.

## Separate review issue body structure

Use this final GitHub body structure for `review` issues.

Common required sections are defined by `../common/review-authoring.md`:

- `## Description`

Common optional sections are defined by `../common/review-authoring.md` and `../common/issue-body.md`:

- `## Resume`
- `## Suggested Fix`
- `## Evidence`

## GitHub issue target relationship

When a separate review issue targets a GitHub issue, represent the target with
the GitHub dependency relationship. The target issue should be blocked by the
review issue until the concern is resolved.

Do not rely on body text alone for GitHub issue-to-issue review targets.

GitHub label is automatically set to `review`.
