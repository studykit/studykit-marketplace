# Jira Issue Research Issue Authoring

Provider-specific binding for workflow `research` artifacts stored as Jira issues.

Read after:

- `../common/research-authoring.md`
- `./jira-issue-convention.md`
- `./jira-issue-metadata.md`
- `./jira-issue-relationships.md`

## Scope

Use this binding for Jira `research` issues. The final body structure is listed below.

## Final body structure

Use this final Jira body structure for `research` artifacts.

Common required sections are defined by `../common/research-authoring.md`:

- `## Description`
- `## Research Question`
- `## Mode`
- `## Options`

Common optional sections are defined by `../common/research-authoring.md` and `../common/body-conventions.md`:

- `## Scope`
- `## Sources To Check`
- `## Resume`

Jira-specific H2 sections for this type: `## Dependencies`.

Jira-specific rules:

- Use Jira issue links or remote links for related work.
- Add `## Dependencies` only as dependency body fallback.

## Metadata mapping

Recommended Jira issue type: configured Research or Task type for the workflow issue side.

Use Jira workflow status for the research workflow lifecycle state.

## Jira-specific section guidance

Use Jira issue links or remote links for related work whenever possible.

### `## Dependencies`

Use only as dependency body fallback.

Content:

- Start with one bullet per dependency.
- Use Jira keys whenever possible.
- Keep the section limited to blocking or ordering dependencies.
