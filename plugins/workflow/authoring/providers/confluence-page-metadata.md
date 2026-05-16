# Confluence Page Metadata

Provider-specific metadata rules for workflow knowledge artifacts stored as Confluence pages.

Read with `../common/knowledge-body.md` and `./confluence-page-convention.md`.

## Semantic metadata mapping

Prefer Confluence page properties or labels for workflow metadata when available.

- `type`: use a page property or label selected by the project.
- `status`: use a page property, label, or configured status surface when useful.
- `tags`: use labels.
- `title`: use the Confluence page title.
- `created_at` and `updated_at`: use Confluence page metadata when reading provider state.

Concrete type and status labels belong in the matching Confluence page type authoring file.

## Identity and hierarchy

Use Confluence page ID, site, and space as stable page identity. Page title and Smart Links are readable references, not stable identity by themselves.

Use page hierarchy for organization and navigation. Do not rely on hierarchy as the only source of workflow type or status metadata.

## Relationship metadata

Use page properties, labels, or link metadata for structured relationships when available. Keep visible relationship sections when the relationship is part of the page's durable meaning.
