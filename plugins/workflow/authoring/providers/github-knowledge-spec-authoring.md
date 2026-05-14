# GitHub Knowledge Spec Authoring

Provider-specific binding for workflow `spec` knowledge artifacts stored as repository Markdown files.

Read after:

- `../common/spec-authoring.md`
- `./github-knowledge-convention.md`

## Scope

Use this binding for GitHub repository Markdown `spec` pages. The final body structure is listed below.

## Final body structure

Use this final GitHub repository Markdown body structure for `spec` artifacts.

Common required sections are defined by `../common/spec-authoring.md`:

- `## Context`
- `## Specification`

Common optional sections are defined by `../common/spec-authoring.md` and `../common/knowledge-body.md`:

- `## Supersedes`
- `## Related Work`
- `## Open Questions`
- `## Consequences`
- `## Examples`
- `## Decision Log`
- `## Rejected Alternatives`
- `## Change Log`
- `## Sources`

GitHub repository Markdown does not add required provider-specific H2 sections for this type.

GitHub repository Markdown rules:

- Use repository-relative Markdown links for pages in the same repository.
- Use full URLs when text must be portable.

Read `./github-knowledge-convention.md` for storage, identity, reference, metadata, relationship, and transport rules.

## GitHub repository metadata and identity

Recommended metadata marker: `workflow:type/spec`.

Use the repository path as canonical page identity. Optional Markdown metadata may help tooling, but the Git-tracked file and git history remain the source of truth.

## GitHub repository section guidance

Use links or full URLs for related work, superseded pages, and sources.

Use repository-relative links when the target is in the same repository. Use full GitHub URLs when the page text must be portable outside the repository.
