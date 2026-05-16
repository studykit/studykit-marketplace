# Confluence Page Spec Authoring

Provider-specific binding for workflow `spec` knowledge artifacts stored as Confluence pages.

Read after:

- `../common/spec-authoring.md`
- `./confluence-page-convention.md`

## Scope

Use this binding for Confluence `spec` pages. The final body structure is listed below.

## Final body structure

Use this final Confluence body structure for `spec` artifacts.

Common required sections are defined by `../common/spec-authoring.md`:

- `## Context`
- `## Specification`

Common optional sections are defined by `../common/spec-authoring.md` and `../common/knowledge-body.md`:

- `## Supersedes`
- `## Related Work`
- `## Open Questions`
- `## Consequences`
- `## Examples`
- `## Decision Log`
- `## Rejected Alternatives`
- `## Change Log`
- `## Sources`

Confluence does not add required provider-specific H2 sections for this type.

Read `./confluence-page-convention.md` for Confluence storage, identity, reference, and transport rules.

## Confluence section guidance

Use Confluence page links or Smart Links when readers stay in Confluence. Use full URLs when content must remain portable outside Confluence.
