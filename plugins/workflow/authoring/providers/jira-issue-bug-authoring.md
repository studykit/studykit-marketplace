# Jira Issue Bug Authoring

Provider-specific binding for workflow `bug` artifacts stored as Jira issues.

Read after:

- `../common/bug-authoring.md`
- `./jira-issue-convention.md`
- `./jira-issue-relationships.md`
- `./jira-issue-anti-patterns.md`

## Scope

Use this binding for Jira `bug` issues. The final body structure is listed below.

## Final body structure

Use this final Jira body structure for `bug` artifacts.

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

Jira-specific H2 sections for this type: `## Dependencies`.

Jira-specific rules:

- Use Jira issue links or remote links for dependency and related issue relationships.
- Add `## Dependencies` only as dependency body fallback.
- Do not add `## Related` only to duplicate native Jira links.

## Metadata mapping

Recommended Jira issue type: Jira Bug.

Use Jira workflow status for the workflow lifecycle state. Use Jira priority or severity fields when configured.

## Jira-specific section guidance

Use Jira issue links or remote links for dependency and related issue relationships whenever possible.

### `## Dependencies`

Use only as dependency body fallback.

Content:

- Start with one bullet per dependency.
- Use Jira keys whenever possible.
- Keep the section limited to blocking or ordering dependencies.

## Body duplication rule

Do not add `## Related` only to duplicate Jira issue links or remote links.
