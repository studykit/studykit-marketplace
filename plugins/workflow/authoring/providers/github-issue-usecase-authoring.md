# GitHub Issue Use Case Issue Authoring

Provider-specific binding for workflow `usecase` artifacts stored as GitHub Issues.

Read after:

- `../common/usecase-authoring.md`
- `./github-issue-convention.md`
- `./github-issue-relationships.md`
- `./github-issue-anti-patterns.md`

## Scope

Use this binding for the GitHub issue side of `usecase`. The final body structure is listed below.

## Final body structure

Use this final GitHub body structure for `usecase` artifacts.

Common required sections are defined by `../common/usecase-authoring.md`:

- `## Description`
- `## Actors`
- `## Current Draft`
- `## Open Questions`

Common optional sections are defined by `../common/usecase-authoring.md` and `../common/issue-body.md`:

- `## Resume`

GitHub-specific H2 sections for this type: `## Related`.

GitHub-specific rules:

- Add `## Related` only for soft references not represented by GitHub metadata.

## GitHub labels

Apply the GitHub label `usecase` to identify this issue type.

## GitHub-specific section guidance

### `## Related`

Use only for soft references not represented by GitHub metadata.

Content:

- Start with one bullet per related artifact.
- Keep descriptions short.
- Do not include parent, dependency, or implementation relationships.
