# GitHub Issue Relationships

Provider-specific relationship rules for workflow issue artifacts stored as GitHub Issues.

Read with `../common/issue-authoring.md`, `./github-issue-convention.md`, and `./github-issue-metadata.md`.

## Boundary

Issue relationships are not issue metadata fields. Do not store parent, child, dependency, or related issue state in `issue.md` frontmatter or in provider metadata files.

Use GitHub-native relationships when available:

- Parent and child relationships use GitHub sub-issue metadata.
- Blocking relationships use GitHub issue dependency metadata.
- Soft related references use the artifact-specific body section only when no native relationship is available or when the relationship is intentionally human-readable context.

## Cache projection

The GitHub issue cache stores relationship state in sidecar files under the issue cache directory:

- `relationships.yml`: current provider relationship projection.
- `relationships-pending.yml`: pending relationship intent before provider write.

`relationships.yml` is a cache projection of provider state, not an author-editable metadata source. Refresh it through workflow cache/provider operations.

`relationships-pending.yml` is write intent. Apply it through workflow provider operations, then refresh the current projection.

## Current projection schema

`relationships.yml` uses this normalized provider projection:

```yaml
schema_version: 1
source_updated_at: <provider-updated-at>
fetched_at: <cache-fetch-time>
parent: <issue-ref-object>
children:
  - <issue-ref-object>
dependencies:
  blocked_by:
    - <issue-ref-object>
  blocking:
    - <issue-ref-object>
related:
  - <issue-ref-object>
```

Relationship summary text is rendered from this projection by workflow scripts. Do not expose raw projection YAML as the human relationship summary.

## Pending intent schema

`relationships-pending.yml` may use declarative fields for requested changes:

```yaml
parent: <issue-ref>
children:
  - <issue-ref>
dependencies:
  blocked_by:
    - <issue-ref>
  blocking:
    - <issue-ref>
related:
  - <issue-ref>
```

Supported aliases exist for compatibility, but authoring should prefer `parent`, `children`, `dependencies.blocked_by`, `dependencies.blocking`, and `related`.

## Body boundary

Do not duplicate GitHub-native parent, child, or dependency relationships in issue body sections. Read `./github-issue-anti-patterns.md` for forbidden body sections.
