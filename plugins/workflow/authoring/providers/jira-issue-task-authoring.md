# Jira Issue Task Authoring

Provider-specific binding for `task` issues stored as Jira issues.

Read after:

- `../common/task-authoring.md`
- `./jira-issue-convention.md`
- `./jira-issue-relationships.md`
- `./jira-issue-anti-patterns.md`

## Scope

Use this binding for Jira `task` issues. The final body structure is listed below.

## Final body structure

Use this final Jira body structure for `task` issues.

Common required sections are defined by `../common/task-authoring.md`:

- `## Description`
- `## Unit Test Strategy`
- `## Acceptance Criteria`

Common optional sections are defined by `../common/task-authoring.md` and `../common/issue-body.md`:

- `## Change Plan`
- `## Interface Contracts`
- `## Resume`
- `## Why Discarded`

Issue type is automatically set to `Task`.
