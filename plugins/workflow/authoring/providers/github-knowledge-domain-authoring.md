# GitHub Knowledge Domain Authoring

Provider-specific binding for workflow `domain` knowledge artifacts stored as repository Markdown files.

Read after:

- `../common/domain-authoring.md`
- `./github-knowledge-convention.md`

## Scope

Use this binding for GitHub repository Markdown `domain` pages. The final body structure is listed below.

## Final body structure

Use this final GitHub repository Markdown body structure for `domain` artifacts.

Common required sections are defined by `../common/domain-authoring.md`:

- `## Concepts`

Common optional sections are defined by `../common/domain-authoring.md` and `../common/knowledge-body.md`:

- `## Relationships`
- `## State Transitions`
- `## Related Work`
- `## Change Log`

GitHub repository Markdown does not add required provider-specific H2 sections for this type.

GitHub repository Markdown rules:

- Keep anchors stable because repository links may target headings.

Read `./github-knowledge-convention.md` for GitHub repository storage, identity, reference, and transport rules.

## GitHub repository identity

Use the repository path as canonical page identity. Do not add Markdown frontmatter for workflow metadata.

## GitHub repository section guidance

Keep headings stable because pages and issues may link to them.

Use repository-relative links when the target is in the same repository. Use full GitHub URLs when the page text must be portable outside the repository.
