# Jira Issue Spike Authoring

Provider-specific binding for `spike` issues stored as Jira issues.

Read after:

- `../common/spike-authoring.md`
- `./jira-issue-convention.md`
- `./jira-issue-relationships.md`
- `./jira-issue-anti-patterns.md`

## Scope

Use this binding for Jira `spike` issues. The final body structure is listed below.

## Final body structure

Use this final Jira body structure for `spike` issues.

Common required sections are defined by `../common/spike-authoring.md`:

- `## Description`
- `## Hypothesis`
- `## Validation Method`
- `## Acceptance Criteria`

Common optional sections are defined by `../common/spike-authoring.md` and `../common/issue-body.md`:

- `## Artifact Links`
- `## Change Plan`
- `## Resume`
- `## Why Discarded`

Issue type is automatically set to `Task`.

Summary prefix is automatically set to `[Spike] `.
