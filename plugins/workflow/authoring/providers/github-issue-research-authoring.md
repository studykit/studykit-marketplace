# GitHub Issue Research Issue Authoring

Provider-specific binding for workflow `research` artifacts stored as GitHub Issues.

Read after:

- `../common/research-authoring.md`
- `./github-issue-convention.md`
- `./github-issue-relationships.md`
- `./github-issue-anti-patterns.md`

## Scope

Use this binding for the GitHub issue side of `research`. The final body structure is listed below.

## Final body structure

Use this final GitHub body structure for `research` artifacts.

Common required sections are defined by `../common/research-authoring.md`:

- `## Description`
- `## Research Question`
- `## Mode`
- `## Options`

Common optional sections are defined by `../common/research-authoring.md` and `../common/issue-body.md`:

- `## Scope`
- `## Sources To Check`
- `## Resume`

GitHub-specific H2 sections for this type: `## Related`.

GitHub-specific rules:

- Add `## Related` only for soft references not represented by GitHub metadata.

## GitHub labels

Apply the GitHub label `research` to identify this issue type.

## GitHub-specific section guidance

### `## Related`

Use only for soft references not represented by GitHub metadata.

Content:

- Start with one bullet per related artifact.
- Keep descriptions short.
- Do not include dependencies, parent work, or follow-up implementation work.
