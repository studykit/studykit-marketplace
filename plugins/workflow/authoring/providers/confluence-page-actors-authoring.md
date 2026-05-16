# Confluence Page Actors Authoring

Provider-specific binding for workflow `actors` knowledge artifacts stored as Confluence pages.

Read after:

- `../common/actors-authoring.md`
- `./confluence-page-convention.md`

## Scope

Use this binding for Confluence `actors` pages. The final body structure is listed below.

## Final body structure

Use this final Confluence body structure for `actors` artifacts.

Common required sections are defined by `../common/actors-authoring.md`:

- `## Roster`

Common optional sections are defined by `../common/actors-authoring.md` and `../common/knowledge-body.md`:

- `## Authorization Notes`
- `## Related Work`
- `## Change Log`

Confluence does not add required provider-specific H2 sections for this type.

Confluence rules:

- Actor slugs should remain stable across use cases and pages.

Read `./confluence-page-convention.md` for Confluence storage, identity, reference, and transport rules.

## Confluence identity and classification

Use the Confluence page ID, site, and space as provider identity. Page titles are readable references but may not be stable enough for automation.

If the selected Confluence binding manages page classification, use a Confluence label or Content Property selected by the project for the `actors` type marker.

## Confluence section guidance

Keep actor slugs stable because use cases, issues, and pages may reference them.

Use Confluence page links or Smart Links when readers stay in Confluence. Use full URLs when content must remain portable outside Confluence.
