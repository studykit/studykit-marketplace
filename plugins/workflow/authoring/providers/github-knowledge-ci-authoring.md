# GitHub Knowledge CI Authoring

Provider-specific binding for workflow `ci` knowledge artifacts stored as repository Markdown files.

Read after:

- `../common/ci-authoring.md`
- `./github-knowledge-convention.md`

## Scope

Use this binding for GitHub repository Markdown `ci` pages. The final body structure is listed below.

## Final body structure

Use this final GitHub repository Markdown body structure for `ci` artifacts.

Common required sections are defined by `../common/ci-authoring.md`:

- `## How To Run Tests`
- `## Test Layout`
- `## CI Pipeline` when remote CI exists

Common optional sections are defined by `../common/ci-authoring.md` and `../common/knowledge-body.md`:

- `## Smoke Scenario`
- `## Fixtures And Environment`
- `## Troubleshooting`
- `## Related Work`
- `## Change Log`

GitHub repository Markdown does not add required provider-specific H2 sections for this type.

GitHub repository Markdown rules:

- Link workflow files, scripts, or dashboards with repository-relative paths when possible.

Read `./github-knowledge-convention.md` for GitHub repository storage, identity, reference, and transport rules.

## GitHub repository identity

Use the repository path as canonical page identity. Do not add Markdown frontmatter for workflow metadata.

## GitHub repository section guidance

Use links for workflow files, scripts, dashboards, and test configuration.

Use repository-relative links when the target is in the same repository. Use full GitHub URLs when the page text must be portable outside the repository.
