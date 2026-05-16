# GitHub Knowledge Research Report Authoring

Provider-specific binding for workflow `research` knowledge artifacts stored as repository Markdown files.

Read after:

- `../common/research-authoring.md`
- `./github-knowledge-convention.md`

## Scope

Use this binding for GitHub repository Markdown `research` pages. The final body structure is listed below.

## Final body structure

Use this final GitHub repository Markdown body structure for `research` artifacts.

Common required sections are defined by `../common/research-authoring.md`:

- `## Context`
- `## Options` for comparative mode
- `## Findings` for single mode

Common optional sections are defined by `../common/research-authoring.md` and `../common/knowledge-body.md`:

- `## Summary`
- `## Criteria`
- `## Raw Evidence`
- `## Limitations`
- `## Related Work`
- `## Change Log`
- `## Sources`

GitHub repository Markdown does not add required provider-specific H2 sections for this type.

GitHub repository Markdown rules:

- Use Markdown links for citations and repository artifacts.

Read `./github-knowledge-convention.md` for GitHub repository storage, identity, reference, and transport rules.

## GitHub repository identity

Use the repository path as canonical page identity. Do not add Markdown frontmatter for workflow metadata.

## GitHub repository section guidance

Use links or full URLs for citations, sources, and related work.

Use repository-relative links when the target is in the same repository. Use full GitHub URLs when the page text must be portable outside the repository.
