# Confluence Page Architecture Authoring

Provider-specific binding for workflow `architecture` knowledge artifacts stored as Confluence pages.

Read after:

- `../common/architecture-authoring.md`
- `./confluence-page-convention.md`

## Scope

Use this binding for Confluence `architecture` pages. The final body structure is listed below.

## Final body structure

Use this final Confluence body structure for `architecture` artifacts.

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

Confluence does not add required provider-specific H2 sections for this type.

Confluence rules:

- Diagrams may be native Confluence content, Mermaid-like rendered content, attachments, or linked diagrams.

Read `./confluence-page-convention.md` for Confluence storage, identity, reference, and transport rules.

## Confluence identity and classification

Use the Confluence page ID, site, and space as provider identity. Page titles are readable references but may not be stable enough for automation.

If the selected Confluence binding manages page classification, use a Confluence label or Content Property selected by the project for the `architecture` type marker.

## Confluence section guidance

Use links, attachments, or repository files for diagrams and related architecture inputs.

Use Confluence page links or Smart Links when readers stay in Confluence. Use full URLs when content must remain portable outside Confluence.
