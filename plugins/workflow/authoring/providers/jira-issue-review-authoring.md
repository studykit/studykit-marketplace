# Jira Issue Review Authoring

Provider-specific binding for `review` issues stored as Jira issues.

Read after:

- `../common/review-authoring.md`
- `./jira-issue-convention.md`
- `./jira-issue-relationships.md`
- `./jira-issue-anti-patterns.md`

## Scope

Use this binding when feedback needs a separate Jira issue for independent
tracking. If the feedback is local to an existing Jira issue and can be
resolved as part of that issue, use a Jira comment instead.

## Issue comment feedback

Use a Jira issue comment when the feedback is local to the issue and can be
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

Use this final Jira body structure for `review` issues.

Common required sections are defined by `../common/review-authoring.md`:

- `## Description`

Common optional sections are defined by `../common/review-authoring.md` and `../common/issue-body.md`:

- `## Resume`
- `## Suggested Fix`
- `## Evidence`

## Jira issue target relationship

When a separate review issue targets a Jira issue, represent the target with the
configured Jira blocking relationship. The target issue should be blocked by the
review issue until the concern is resolved.

Do not rely on body text alone for Jira issue-to-issue review targets.

Issue type is automatically set to `Task`.

Summary prefix is automatically set to `[Review] `.
