# Jira Issue Task Authoring

Provider-specific binding for workflow `task` artifacts stored as Jira issues.

Read after:

- `../common/task-authoring.md`
- `./jira-issue-convention.md`
- `./jira-issue-relationships.md`
- `./jira-issue-anti-patterns.md`

## Scope

Use this binding for Jira `task` issues. The final body structure is listed below.

## Final body structure

Use this final Jira body structure for `task` artifacts.

Common required sections are defined by `../common/task-authoring.md`:

- `## Description`
- `## Unit Test Strategy`
- `## Acceptance Criteria`

Common optional sections are defined by `../common/task-authoring.md` and `../common/issue-body.md`:

- `## Change Plan`
- `## Interface Contracts`
- `## Resume`
- `## Why Discarded`

Jira-specific H2 sections for this type: `## Dependencies`.

Jira-specific rules:

- Use Jira issue links or remote links for `implements`, `parent`, `depends_on`, and `related`.
- Add `## Dependencies` only when native dependency links are unavailable or unreliable.
- Do not add `## Implements` or `## Related` only to duplicate native Jira links.

## Metadata mapping

Recommended Jira issue type: Jira Task or configured equivalent.

Use Jira workflow status for the workflow lifecycle state. Use Jira priority for priority when configured.

## Jira-specific section guidance

Use Jira issue links or remote links for `implements`, `parent`, `depends_on`, and `related` relationships whenever possible.

### `## Dependencies`

Use only when dependency links cannot be stored natively.

Content:

- Start with one bullet per dependency.
- Use Jira keys whenever possible.
- Keep the section limited to blocking or ordering dependencies.
- Do not include soft related work, parent links, or implementation links.

## Body duplication rule

Do not add `## Implements` or `## Related` only to duplicate Jira issue links or remote links. Use those body sections only if the active project intentionally needs a human-readable fallback.
