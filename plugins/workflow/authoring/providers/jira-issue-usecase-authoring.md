# Jira Issue Use Case Issue Authoring

Provider-specific binding for workflow `usecase` artifacts stored as Jira issues.

Read after:

- `../common/usecase-authoring.md`
- `./jira-issue-convention.md`
- `./jira-issue-relationships.md`
- `./jira-issue-anti-patterns.md`

## Scope

Use this binding for Jira `usecase` issues. The final body structure is listed below.

## Final body structure

Use this final Jira body structure for `usecase` artifacts.

Common required sections are defined by `../common/usecase-authoring.md`:

- `## Description`
- `## Actors`
- `## Current Draft`
- `## Open Questions`

Common optional sections are defined by `../common/usecase-authoring.md` and `../common/issue-body.md`:

- `## Resume`

Jira-specific H2 sections for this type: None.

Jira-specific rules:

- Use Jira issue links or remote links for related work.
- Do not add `## Related` only to duplicate native Jira links.

## Metadata mapping

Recommended Jira issue type: configured Story or Task type for the workflow issue side.

Use Jira workflow status for the use case workflow lifecycle state.

## Jira-specific section guidance

Use Jira issue links or remote links for related work whenever possible.

## Body duplication rule

Do not add `## Related` only to duplicate Jira issue links or remote links.
