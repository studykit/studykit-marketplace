# Confluence Page Research Report Authoring

Provider-specific binding for workflow `research` knowledge artifacts stored as Confluence pages.

Read after:

- `../common/research-authoring.md`
- `./confluence-page-convention.md`

## Scope

Use this binding for Confluence `research` pages. The final body structure is listed below.

## Final body structure

Use this final Confluence body structure for `research` artifacts.

Common required sections are defined by `../common/research-authoring.md`:

- `## Context`
- `## Options` for comparative mode
- `## Findings` for single mode

Common optional sections are defined by `../common/research-authoring.md` and `../common/knowledge-body.md`:

- `## Summary`
- `## Criteria`
- `## Raw Evidence`
- `## Limitations`
- `## Related Work`
- `## Change Log`
- `## Sources`

Confluence does not add required provider-specific H2 sections for this type.

Confluence rules:

- Use page links, Smart Links, or full URLs for citations.

Read `./confluence-page-convention.md` for storage, identity, reference, metadata, relationship, and transport rules.

## Confluence metadata and identity

Recommended label or page property: `workflow:type/research`.

Use the Confluence page ID, site, and space as structured identity. Page titles are readable references but may not be stable enough for automation.

## Confluence section guidance

Use links or full URLs for citations, sources, and related work.

Use Confluence page links or Smart Links when readers stay in Confluence. Use full URLs when content must remain portable outside Confluence.
