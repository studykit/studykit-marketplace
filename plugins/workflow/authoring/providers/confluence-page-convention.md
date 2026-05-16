# Confluence Page Convention

Common convention rules for workflow knowledge artifacts stored as Confluence pages.

## Scope

Use these rules for Confluence pages produced or updated by the workflow plugin.

This file defines Confluence-wide page writing rules only. Cache projections and provider write paths should use Confluence provider-native field names. Artifact-specific body structure belongs outside this file.

## Identity

Use Confluence page ID, site, and space as the stable page identity.

Use page title or Smart Link as the readable reference in visible text. Use a full page URL when the text must remain portable outside Confluence or when the target renderer may not support Smart Links.

Do not treat local projection paths as canonical page identity.

## Body format

Keep the visible page body structured and current.

Use H2 sections for durable page content. Avoid raw transcripts, long work logs, and unresolved discussion in the page body.

Use Confluence links, Smart Links, or full URLs for references. Prefer Smart Links when readers stay inside Atlassian-aware surfaces. Prefer full URLs when the page may be exported, copied, or read outside Confluence.

## Relationships

Represent relationships as visible page content when they are part of the artifact's durable meaning.

Use Confluence page links, Jira Smart Links, GitHub Smart Links, or full URLs for relationship entries.

Use Confluence page hierarchy for parent-child organization and navigation. Do not treat arbitrary workflow relationships as Confluence metadata unless a selected binding defines an explicit provider-backed Content Property contract.

## Change log

Every material page edit should include a concise `## Change Log` entry that links to the causing workflow artifact.

```markdown
## Change Log

- 2026-05-13 — PROJ-123 — Published initial OAuth integration evaluation.
```

The change log records why the page changed. Confluence version history records who changed what and when.

Do not duplicate issue discussion in the page.

## Page comments

Use Confluence comments for page-local clarification and review.

If feedback needs triage, assignment, priority, lifecycle status, or durable resolution tracking, create or update a workflow review issue instead of relying only on a page comment.

## Update discipline

Confluence updates must be version-aware.

Before updating an existing page, read the current page version. Detect version conflicts and avoid overwriting concurrent edits.

Keep each update focused on the requested artifact change. Do not rewrite unrelated sections just to normalize formatting.
