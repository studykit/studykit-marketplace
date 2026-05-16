# GitHub Knowledge NFR Authoring

Provider-specific binding for workflow `nfr` knowledge artifacts stored as repository Markdown files.

Read after:

- `../common/nfr-authoring.md`
- `./github-knowledge-convention.md`

## Scope

Use this binding for GitHub repository Markdown `nfr` pages. The final body structure is listed below.

## Final body structure

Use this final GitHub repository Markdown body structure for `nfr` artifacts.

Common required sections are defined by `../common/nfr-authoring.md`:

- `## Requirements`

Common optional sections are defined by `../common/nfr-authoring.md` and `../common/knowledge-body.md`:

- `## Rationale`
- `## Related Work`
- `## Change Log`

GitHub repository Markdown does not add required provider-specific H2 sections for this type.

GitHub repository Markdown rules:

- Use stable NFR IDs for references.

Read `./github-knowledge-convention.md` for GitHub repository storage, identity, reference, and transport rules.

## GitHub repository identity

Use the repository path as canonical page identity. Do not add Markdown frontmatter for workflow metadata.

## GitHub repository section guidance

Use stable NFR IDs for page and issue references.

Use repository-relative links when the target is in the same repository. Use full GitHub URLs when the page text must be portable outside the repository.
