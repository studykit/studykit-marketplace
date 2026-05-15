# Workflow Metadata Contract

Semantic metadata rules shared by workflow artifacts.

This file defines provider-neutral fields, identity expectations, and relationship meanings. It does not define storage, field mapping, cache projections, or provider-owned metadata boundaries.

## Artifact identity

Use the canonical identity supplied by the artifact's storage backend.

| Artifact role | Canonical identity |
| --- | --- |
| Issue-backed artifact | Backend issue reference |
| Knowledge-backed artifact | Backend page, document, or file reference |
| Local projection | Projection of canonical identity, not identity itself |

Do not require a local monotonic integer id. Do not treat local projection paths as canonical identity unless the artifact is truly file-backed.

## Normalized metadata view

Workflow tooling may expose a provider-neutral view like this:

```yaml
type: review
role: issue
identity:
  ref: <backend-issued-reference>
  display: <human-readable-reference>
title: Clarify retry boundary
status: open
target:
  - ref: <review-target-reference>
    kind: issue
created_at: 2026-05-13T00:00:00Z
updated_at: 2026-05-13T00:30:00Z
```

This view is a translation layer for assistants, validators, and reports. It is not necessarily stored as YAML in the backing system.

## Common fields

Common workflow metadata fields include, but are not limited to:

| Field | Meaning |
| --- | --- |
| `type` | Workflow artifact type, such as `task`, `bug`, `review`, or `spec`. |
| `role` | Storage role, usually `issue` or `knowledge`. |
| `identity` | Backend-issued reference and display form. |
| `title` | Short human-readable artifact title. |
| `status` | Semantic workflow lifecycle state. |
| `priority` | Relative urgency or ordering hint. |
| `tags` | Classification tags for filtering and routing. |
| `created_at` | Creation timestamp when available. |
| `updated_at` | Last meaningful update timestamp when available. |

Type-specific authoring files define required and optional fields for each artifact type.

## Relationship fields

Workflow relationships include:

| Field | Meaning |
| --- | --- |
| `target` | Artifact reviewed or affected by a review item. |
| `implements` | Work item implements a use case, requirement, spec, or knowledge artifact. |
| `parent` | Work item belongs under an epic or parent work item. |
| `children` | Work items coordinated by a parent work item. |
| `depends_on` | Work item waits for another work item. |
| `blocks` | Work item prevents another work item from progressing. |
| `related` | Soft relationship worth surfacing. |
| `supersedes` | New knowledge artifact replaces an older one. |
| `source_issue` | Knowledge artifact was created or changed because of an issue-backed workflow item. |
| `knowledge_page` | Issue-backed workflow item has a curated knowledge artifact. |

Type-specific authoring files define which relationships are allowed or required. Storage and projection shape are outside this file.

## Status

Status is semantic in common authoring files.

- Issue-backed artifacts use workflow lifecycle states defined by their type-specific authoring file.
- Knowledge-backed artifacts use stable content states when those states are useful.
- Concrete backend mappings are outside this file.

Do not assume every backend has the same status enum or stores status in the same place.

## Logs and history

Do not duplicate audit trails in metadata.

- Issue discussion and work notes belong in comments, notes, or history.
- Knowledge page history belongs in the backing system's version history.
- Knowledge page `## Change Log` records semantic cause, not full discussion.

## Required authoring behavior

Before creating or editing any workflow artifact:

1. Run the authoring resolver.
2. Read every authoring file returned by the resolver.
3. Draft the change from those contracts, then run the requested provider or cache operation.

Authoring contracts are plugin-bundled Markdown files. Resolver output must use absolute paths.
