# Confluence Page Domain Authoring

Provider-specific binding for workflow `domain` knowledge artifacts stored as Confluence pages.

Read after:

- `../common/domain-authoring.md`
- `./confluence-page-convention.md`

## Scope

Use this binding for Confluence `domain` pages. The final body structure is listed below.

## Final body structure

Use this final Confluence body structure for `domain` artifacts.

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

Read `./confluence-page-convention.md` for storage, identity, reference, metadata, relationship, and transport rules.

## Confluence metadata and identity

Recommended label or page property: `workflow:type/domain`.

Use the Confluence page ID, site, and space as structured identity. Page titles are readable references but may not be stable enough for automation.

## Confluence section guidance

Keep headings stable because pages and issues may link to them.

Use Confluence page links or Smart Links when readers stay in Confluence. Use full URLs when content must remain portable outside Confluence.
