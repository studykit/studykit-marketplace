# Confluence Page Domain Authoring

Provider-specific binding for `domain` knowledge pages stored as Confluence pages.

Read after:

- `../common/domain-authoring.md`
- `./confluence-page-convention.md`

## Scope

Use this binding for Confluence `domain` pages. The final body structure is listed below.

## Final body structure

Use this final Confluence body structure for `domain` pages.

Common required sections are defined by `../common/domain-authoring.md`:

- `## Concepts`

Common optional sections are defined by `../common/domain-authoring.md` and `../common/knowledge-body.md`:

- `## Relationships`
- `## State Transitions`
- `## Related Work`
- `## Change Log`

Confluence does not add required provider-specific H2 sections for this type.

Confluence rules:

- Keep concept headings stable because Confluence links may target headings.

Read `./confluence-page-convention.md` for Confluence storage, identity, reference, and transport rules.

## Confluence identity and classification

Use the Confluence page ID, site, and space as provider identity. Page titles are readable references but may not be stable enough for automation.

If the selected Confluence binding manages page classification, use a Confluence label or Content Property selected by the project for the `domain` type marker.

## Confluence section guidance

Keep headings stable because pages and issues may link to them.

Use Confluence page links or Smart Links when readers stay in Confluence. Use full URLs when content must remain portable outside Confluence.
