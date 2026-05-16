# Jira Issue Review Authoring

Provider-specific binding for workflow `review` artifacts stored as Jira issues.

Read after:

- `../common/review-authoring.md`
- `./jira-issue-convention.md`
- `./jira-issue-metadata.md`
- `./jira-issue-relationships.md`

## Scope

Use this binding for Jira `review` issues. The final body structure is listed below.

## Final body structure

Use this final Jira body structure for `review` artifacts.

Common required sections are defined by `../common/review-authoring.md`:

- `## Description`

Common optional sections are defined by `../common/review-authoring.md` and `../common/body-conventions.md`:

- `## Resume`
- `## Suggested Fix`
- `## Evidence`

Jira-specific H2 sections for this type: `## Target`.

Jira-specific rules:

- Add required `## Target` for target-specific reviews.
- `## Target` contains one bullet per target using Jira keys or links.

## Metadata mapping

Recommended Jira issue type: configured Review or Task type plus workflow metadata.

Use Jira workflow status for the review lifecycle state.

## Jira-specific section guidance

### `## Target`

Required for target-specific reviews.

Content:

- Start with one bullet per target.
- Use Jira keys for Jira issue targets.
- Use Markdown links for Confluence pages, GitHub issues, repository files, or external targets.
- Add at most one short clarifying phrase after the reference when the target relationship is not obvious.

Example:

```markdown
## Target

- PROJ-123
- [Architecture](https://example.atlassian.net/wiki/spaces/ENG/pages/123456789/Architecture)
```
