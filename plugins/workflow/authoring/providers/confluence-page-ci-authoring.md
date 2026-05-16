# Confluence Page CI Authoring

Provider-specific binding for `ci` knowledge pages stored as Confluence pages.

Read after:

- `../common/ci-authoring.md`
- `./confluence-page-convention.md`

## Scope

Use this binding for Confluence `ci` pages. The final body structure is listed below.

## Final body structure

Use this final Confluence body structure for `ci` pages.

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

Confluence does not add required provider-specific H2 sections for this type.

Confluence rules:

- Link pipelines, dashboards, and workflow files with Smart Links or full URLs.

Read `./confluence-page-convention.md` for Confluence storage, identity, reference, and transport rules.

## Confluence identity and classification

Use the Confluence page ID, site, and space as provider identity. Page titles are readable references but may not be stable enough for automation.

If the selected Confluence binding manages page classification, use a Confluence label or Content Property selected by the project for the `ci` type marker.

## Confluence section guidance

Use links for workflow files, scripts, dashboards, and test configuration.

Use Confluence page links or Smart Links when readers stay in Confluence. Use full URLs when content must remain portable outside Confluence.
