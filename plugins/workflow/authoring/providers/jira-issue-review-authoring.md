# Jira Issue Review Authoring

Provider-specific binding for workflow `review` issues stored as Jira issues.

Read after:

- `../common/review-authoring.md`
- `./jira-issue-convention.md`
- `./jira-issue-metadata.md`
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

Do not add `## Target`; the containing Jira issue is the target. Keep the
comment short. If the discussion needs independent tracking, create a separate
review issue instead.

## Separate review issue body structure

Use this final Jira body structure for `review` issues.

Common required sections are defined by `../common/review-authoring.md`:

- `## Description`

Common optional sections are defined by `../common/review-authoring.md` and `../common/issue-body.md`:

- `## Resume`
- `## Suggested Fix`
- `## Evidence`

Jira-specific H2 sections for this type: `## Target`.

Jira-specific rules:

- Use a configured Jira blocking relationship when the target is a Jira issue.
- Add `## Target` only when the target is not represented by a provider-native
  relationship.
- Use body links in `## Target` when the target is not a Jira issue.
- Do not create a separate review issue only to record local discussion on an existing issue.

## Jira issue type

Use the Jira Task issue type for review items. Prefix the Jira summary with
`[Review] `.

## Jira issue target relationship

When a separate review issue targets a Jira issue, represent the target with the
configured Jira blocking relationship. The target issue should be blocked by the
review issue until the concern is resolved.

Do not rely on body text alone for Jira issue-to-issue review targets.

### `## Target`

Use only when the review target is not already represented by a provider-native
relationship.

Content:

- Use body links for non-Jira targets such as Confluence pages, GitHub issues,
  repository files, or external pages.
- Add at most one short clarifying phrase after the reference when the target relationship is not obvious.
- Do not add `## Target` only to duplicate a Jira blocking relationship.
- Do not copy the target issue body into the review.

Example:

```markdown
## Target

- [Architecture](https://confluence.example.com/display/ENG/Architecture)
```
