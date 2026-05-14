# GitHub Knowledge Actors Authoring

Provider-specific binding for workflow `actors` knowledge artifacts stored as repository Markdown files.

Read after:

- `../common/actors-authoring.md`
- `./github-knowledge-convention.md`

## Scope

Use this binding for GitHub repository Markdown `actors` pages. The final body structure is listed below.

## Final body structure

Use this final GitHub repository Markdown body structure for `actors` artifacts.

Common required sections are defined by `../common/actors-authoring.md`:

- `## Roster`

Common optional sections are defined by `../common/actors-authoring.md` and `../common/knowledge-body.md`:

- `## Authorization Notes`
- `## Related Work`
- `## Change Log`

GitHub repository Markdown does not add required provider-specific H2 sections for this type.

GitHub repository Markdown rules:

- Actor slugs should be stable because repository links and issue bodies may reference them.

Read `./github-knowledge-convention.md` for storage, identity, reference, metadata, relationship, and transport rules.

## GitHub repository metadata and identity

Recommended metadata marker: `workflow:type/actors`.

Use the repository path as canonical page identity. Optional Markdown metadata may help tooling, but the Git-tracked file and git history remain the source of truth.

## GitHub repository section guidance

Keep actor slugs stable because use cases, issues, and pages may reference them.

Use repository-relative links when the target is in the same repository. Use full GitHub URLs when the page text must be portable outside the repository.
