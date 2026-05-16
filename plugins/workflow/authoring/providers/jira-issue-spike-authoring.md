# Jira Issue Spike Authoring

Provider-specific binding for workflow `spike` artifacts stored as Jira issues.

Read after:

- `../common/spike-authoring.md`
- `./jira-issue-convention.md`
- `./jira-issue-metadata.md`
- `./jira-issue-relationships.md`
- `./jira-issue-anti-patterns.md`

## Scope

Use this binding for Jira `spike` issues. The final body structure is listed below.

## Final body structure

Use this final Jira body structure for `spike` artifacts.

Common required sections are defined by `../common/spike-authoring.md`:

- `## Description`
- `## Hypothesis`
- `## Validation Method`
- `## Acceptance Criteria`

Common optional sections are defined by `../common/spike-authoring.md` and `../common/issue-body.md`:

- `## Artifact Links`
- `## Change Plan`
- `## Follow-Up`
- `## Resume`
- `## Why Discarded`

Jira-specific H2 sections for this type: `## Dependencies`.

Jira-specific rules:

- Use Jira issue links for follow-up work when possible.
- Add `## Dependencies` only as dependency body fallback.
- Do not add `## Related` only to duplicate native Jira links.

## Metadata mapping

Recommended Jira issue type: Jira Spike if available, otherwise configured Task subtype or label.

Use Jira workflow status for the workflow lifecycle state.

## Jira-specific section guidance

Use Jira issue links for follow-up work when possible.

### `## Dependencies`

Use only as dependency body fallback.

Content:

- Start with one bullet per dependency.
- Use Jira keys whenever possible.
- Keep the section limited to blocking or ordering dependencies.

## Body duplication rule

Do not add `## Related` only to duplicate Jira issue links or remote links.
