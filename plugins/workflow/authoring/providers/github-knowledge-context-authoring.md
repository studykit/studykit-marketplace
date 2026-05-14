# GitHub Knowledge Context Authoring

Provider-specific binding for workflow `context` knowledge artifacts stored as repository Markdown files.

Read after:

- `../common/context-authoring.md`
- `./github-knowledge-convention.md`

## Scope

Use this binding for GitHub repository Markdown `context` pages. The final body structure is listed below.

## Final body structure

Use this final GitHub repository Markdown body structure for `context` artifacts.

Common required sections are defined by `../common/context-authoring.md`:

- `## Original Idea`
- `## Problem Framing`

Common optional sections are defined by `../common/context-authoring.md` and `../common/knowledge-body.md`:

- `## Scope`
- `## Screens`
- `## Success Criteria`
- `## Related Work`
- `## Change Log`

GitHub repository Markdown does not add required provider-specific H2 sections for this type.

GitHub repository Markdown rules:

- Link large mockups or generated previews instead of embedding them inline.

Read `./github-knowledge-convention.md` for storage, identity, reference, metadata, relationship, and transport rules.

## GitHub repository metadata and identity

Recommended metadata marker: `workflow:type/context`.

Use the repository path as canonical page identity. Optional Markdown metadata may help tooling, but the Git-tracked file and git history remain the source of truth.

## GitHub repository section guidance

Use links or attachments for related work, screens, and design artifacts.

Use repository-relative links when the target is in the same repository. Use full GitHub URLs when the page text must be portable outside the repository.
