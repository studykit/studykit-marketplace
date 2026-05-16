# GitHub Issue Epic Authoring

Provider-specific binding for `epic` issues stored as GitHub Issues.

Read after:

- `../common/epic-authoring.md`
- `./github-issue-convention.md`
- `./github-issue-relationships.md`
- `./github-issue-anti-patterns.md`

## Scope

Use this binding for GitHub `epic` issues. The final body structure is listed below.

## Final body structure

Use this final GitHub body structure for `epic` issues.

Common required sections are defined by `../common/epic-authoring.md`:

- `## Description`

Common optional sections are defined by `../common/epic-authoring.md` and `../common/issue-body.md`:

- `## Coordination Notes`
- `## Acceptance Criteria`
- `## Related Work`
- `## Resume`
- `## Why Discarded`

GitHub-specific H2 sections for this type: None.

GitHub-specific rules:

- Use GitHub sub-issues for canonical hierarchy.

## GitHub hierarchy

GitHub sub-issues are the provider-native parent/child relationship for all
GitHub issue types, not only epics.

Use the epic body for coordination narrative.

GitHub label is automatically set to `epic`.
