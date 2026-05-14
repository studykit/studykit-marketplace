# Confluence Page Use Case Page Authoring

Provider-specific binding for workflow `usecase` knowledge artifacts stored as Confluence pages.

Read after:

- `../common/usecase-authoring.md`
- `./confluence-page-convention.md`

## Scope

Use this binding for Confluence `usecase` pages. The final body structure is listed below.

## Final body structure

Use this final Confluence body structure for `usecase` artifacts.

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

Read `./confluence-page-convention.md` for storage, identity, reference, metadata, relationship, and transport rules.

## Confluence metadata and identity

Recommended label or page property: `workflow:type/usecase`.

Use the Confluence page ID, site, and space as structured identity. Page titles are readable references but may not be stable enough for automation.

## Confluence section guidance

Link the source issue and implementation work with native links or full URLs.

Use Confluence page links or Smart Links when readers stay in Confluence. Use full URLs when content must remain portable outside Confluence.
