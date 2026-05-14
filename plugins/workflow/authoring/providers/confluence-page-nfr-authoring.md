# Confluence Page NFR Authoring

Provider-specific binding for workflow `nfr` knowledge artifacts stored as Confluence pages.

Read after:

- `../common/nfr-authoring.md`
- `./confluence-page-convention.md`

## Scope

Use this binding for Confluence `nfr` pages. The final body structure is listed below.

## Final body structure

Use this final Confluence body structure for `nfr` artifacts.

Common required sections are defined by `../common/nfr-authoring.md`:

- `## Requirements`

Common optional sections are defined by `../common/nfr-authoring.md` and `../common/knowledge-body.md`:

- `## Rationale`
- `## Related Work`
- `## Change Log`

Confluence does not add required provider-specific H2 sections for this type.

Confluence rules:

- Use stable NFR IDs for references.

Read `./confluence-page-convention.md` for storage, identity, reference, metadata, relationship, and transport rules.

## Confluence metadata and identity

Recommended label or page property: `workflow:type/nfr`.

Use the Confluence page ID, site, and space as structured identity. Page titles are readable references but may not be stable enough for automation.

## Confluence section guidance

Use stable NFR IDs for page and issue references.

Use Confluence page links or Smart Links when readers stay in Confluence. Use full URLs when content must remain portable outside Confluence.
