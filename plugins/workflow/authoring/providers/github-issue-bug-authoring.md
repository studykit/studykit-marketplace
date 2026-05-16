# GitHub Issue Bug Authoring

Provider-specific binding for workflow `bug` artifacts stored as GitHub Issues.

Read after:

- `../common/bug-authoring.md`
- `./github-issue-convention.md`
- `./github-issue-metadata.md`
- `./github-issue-relationships.md`
- `./github-issue-anti-patterns.md`

## Scope

Use this binding for GitHub `bug` issues. The final body structure is listed below.

## Final body structure

Use this final GitHub body structure for `bug` artifacts.

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

GitHub-specific H2 sections for this type: `## Related`.

GitHub-specific rules:

- Add `## Related` only for soft diagnostic context.

## GitHub labels

Apply the GitHub label `bug` to identify this issue type.

## GitHub-specific section guidance

### `## Related`

Use only for soft diagnostic references that help explain or investigate the defect.

Content:

- Start with one bullet per related artifact.
- Keep descriptions short.
- Do not include blockers, parent issues, or dependency relationships.
