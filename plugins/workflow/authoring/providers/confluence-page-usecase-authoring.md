# Confluence Page Use Case Page Authoring

Provider-specific binding for `usecase` knowledge pages stored as Confluence pages.

Read after:

- `../common/usecase-authoring.md`
- `./confluence-page-convention.md`

## Scope

Use this binding for Confluence `usecase` pages. The final body structure is listed below.

## Final body structure

Use this final Confluence body structure for `usecase` pages.

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

Confluence does not add required provider-specific H2 sections for this type.

Confluence rules:

- Link the source issue and implementation work with Jira/GitHub Smart Links or full URLs.

Read `./confluence-page-convention.md` for Confluence storage, identity, reference, and transport rules.

## Confluence identity and classification

Use the Confluence page ID, site, and space as provider identity. Page titles are readable references but may not be stable enough for automation.

If the selected Confluence binding manages page classification, use a Confluence label or Content Property selected by the project for the `usecase` type marker.

## Confluence section guidance

Link the source issue and implementation work with native links or full URLs.

Use Confluence page links or Smart Links when readers stay in Confluence. Use full URLs when content must remain portable outside Confluence.
