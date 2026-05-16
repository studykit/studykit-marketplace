# Jira Issue Bug Authoring

Provider-specific binding for `bug` issues stored as Jira issues.

Read after:

- `../common/bug-authoring.md`
- `./jira-issue-convention.md`
- `./jira-issue-relationships.md`
- `./jira-issue-anti-patterns.md`

## Scope

Use this binding for Jira `bug` issues. The final body structure is listed below.

## Final body structure

Use this final Jira body structure for `bug` issues.

Common required sections are defined by `../common/bug-authoring.md`:

- `## Description`
- `## Reproduction`
- `## Unit Test Strategy`
- `## Acceptance Criteria`

Common optional sections are defined by `../common/bug-authoring.md` and `../common/issue-body.md`:

- `## Environment`
- `## Change Plan`
- `## Interface Contracts`
- `## Resume`
- `## Why Discarded`

Issue type is automatically set to `Bug`.
