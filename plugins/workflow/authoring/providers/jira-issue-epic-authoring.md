# Jira Issue Epic Authoring

Provider-specific binding for workflow `epic` artifacts stored as Jira issues.

Read after:

- `../common/epic-authoring.md`
- `./jira-issue-convention.md`

## Scope

Use this binding for Jira `epic` issues. The final body structure is listed below.

## Final body structure

Use this final Jira body structure for `epic` artifacts.

Common required sections are defined by `../common/epic-authoring.md`:

- `## Description`
- `## Children`

Common optional sections are defined by `../common/epic-authoring.md` and `../common/body-conventions.md`:

- `## Coordination Notes`
- `## Acceptance Criteria`
- `## Related Work`
- `## Resume`
- `## Why Discarded`

Jira-specific H2 sections for this type: None.

Jira-specific rules:

- Use Jira hierarchy or parent fields as canonical hierarchy.
- Keep `## Children` as the readable index.
- Do not add body sections that duplicate native Jira hierarchy.

## Metadata mapping

Recommended Jira issue type: Jira Epic or configured hierarchy type.

Use Jira workflow status for the workflow lifecycle state.

## Jira-specific section guidance

Use Jira hierarchy or parent fields as canonical hierarchy.

Keep `## Children` as the readable index. Each child entry should use a Jira key and a short label.

Do not add body sections that duplicate native Jira hierarchy.
