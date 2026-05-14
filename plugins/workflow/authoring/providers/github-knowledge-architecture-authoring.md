# GitHub Knowledge Architecture Authoring

Provider-specific binding for workflow `architecture` knowledge artifacts stored as repository Markdown files.

Read after:

- `../common/architecture-authoring.md`
- `./github-knowledge-convention.md`

## Scope

Use this binding for GitHub repository Markdown `architecture` pages. The final body structure is listed below.

## Final body structure

Use this final GitHub repository Markdown body structure for `architecture` artifacts.

Common required sections are defined by `../common/architecture-authoring.md`:

- `## Overview`
- `## Components`
- `## Technology Stack`
- `## Test Strategy`

Common optional sections are defined by `../common/architecture-authoring.md` and `../common/knowledge-body.md`:

- `## Component Diagram`
- `## External Dependencies`
- `## Related Work`
- `## Change Log`

GitHub repository Markdown does not add required provider-specific H2 sections for this type.

GitHub repository Markdown rules:

- Diagrams may be Mermaid, ASCII, or linked files in the repository.

Read `./github-knowledge-convention.md` for storage, identity, reference, metadata, relationship, and transport rules.

## GitHub repository metadata and identity

Recommended metadata marker: `workflow:type/architecture`.

Use the repository path as canonical page identity. Optional Markdown metadata may help tooling, but the Git-tracked file and git history remain the source of truth.

## GitHub repository section guidance

Use links, attachments, or repository files for diagrams and related architecture inputs.

Use repository-relative links when the target is in the same repository. Use full GitHub URLs when the page text must be portable outside the repository.
