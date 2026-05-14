# GitHub Issue Review Authoring

Provider-specific binding for workflow `review` artifacts stored as GitHub Issues.

Read after:

- `../common/review-authoring.md`
- `./github-issue-convention.md`
- `./github-issue-anti-patterns.md`

## Scope

Use this binding for GitHub `review` issues. The final body structure is listed below.

## Final body structure

Use this final GitHub body structure for `review` artifacts.

Common required sections are defined by `../common/review-authoring.md`:

- `## Description`

Common optional sections are defined by `../common/review-authoring.md` and `../common/body-conventions.md`:

- `## Resume`
- `## Suggested Fix`
- `## Evidence`

GitHub-specific H2 sections for this type: `## Target`.

GitHub-specific rules:

- Add required `## Target` for target-specific reviews.
- `## Target` contains one bullet per target using GitHub references or Markdown links.

## Metadata mapping

Recommended GitHub type label: `review`.

Use GitHub Issue Fields for workflow status when available. If fields are unavailable, use a status label such as `workflow/status:<state>`.

## GitHub-specific section guidance

### `## Target`

Required for target-specific reviews.

Content:

- Start with one bullet per target.
- Use `#123` for same-repository issues.
- Use `owner/repo#123` for cross-repository GitHub issues.
- Use a Markdown link for repository knowledge pages or external targets.
- Add at most one short clarifying phrase after the reference when the target relationship is not obvious.

Example:

```markdown
## Target

- #123
- [Architecture](wiki/workflow/architecture.md)
```
