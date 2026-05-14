# GitHub Knowledge Use Case Page Authoring

Provider-specific binding for workflow `usecase` knowledge artifacts stored as repository Markdown files.

Read after:

- `../common/usecase-authoring.md`
- `./github-knowledge-convention.md`

## Scope

Use this binding for GitHub repository Markdown `usecase` pages. The final body structure is listed below.

## Final body structure

Use this final GitHub repository Markdown body structure for `usecase` artifacts.

Common required sections are defined by `../common/usecase-authoring.md`:

- `## Goal`
- `## Situation`
- `## Flow`
- `## Expected Outcome`

Common optional sections are defined by `../common/usecase-authoring.md` and `../common/knowledge-body.md`:

- `## Actors`
- `## Validation`
- `## Error Handling`
- `## Related Work`
- `## Supersedes`
- `## Change Log`

GitHub repository Markdown does not add required provider-specific H2 sections for this type.

GitHub repository Markdown rules:

- Link the source issue and implementation work with Markdown links or full GitHub issue URLs.

Read `./github-knowledge-convention.md` for storage, identity, reference, metadata, relationship, and transport rules.

## GitHub repository metadata and identity

Recommended metadata marker: `workflow:type/usecase`.

Use the repository path as canonical page identity. Optional Markdown metadata may help tooling, but the Git-tracked file and git history remain the source of truth.

## GitHub repository section guidance

Link the source issue and implementation work with native links or full URLs.

Use repository-relative links when the target is in the same repository. Use full GitHub URLs when the page text must be portable outside the repository.
