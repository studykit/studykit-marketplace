# Confluence Page Context Authoring

Provider-specific binding for workflow `context` knowledge artifacts stored as Confluence pages.

Read after:

- `../common/context-authoring.md`
- `./confluence-page-convention.md`

## Scope

Use this binding for Confluence `context` pages. The final body structure is listed below.

## Final body structure

Use this final Confluence body structure for `context` artifacts.

Common required sections are defined by `../common/context-authoring.md`:

- `## Original Idea`
- `## Problem Framing`

Common optional sections are defined by `../common/context-authoring.md` and `../common/knowledge-body.md`:

- `## Scope`
- `## Screens`
- `## Success Criteria`
- `## Related Work`
- `## Change Log`

Confluence does not add required provider-specific H2 sections for this type.

Confluence rules:

- Use links or attachments for large mockups.

Read `./confluence-page-convention.md` for storage, identity, reference, metadata, relationship, and transport rules.

## Confluence metadata and identity

Recommended label or page property: `workflow:type/context`.

Use the Confluence page ID, site, and space as structured identity. Page titles are readable references but may not be stable enough for automation.

## Confluence section guidance

Use links or attachments for related work, screens, and design artifacts.

Use Confluence page links or Smart Links when readers stay in Confluence. Use full URLs when content must remain portable outside Confluence.
