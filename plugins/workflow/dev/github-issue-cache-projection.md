# GitHub Issue Cache Projection

Contributor-facing cache projection contract for workflow GitHub Issue operations.

This file is for workflow plugin contributors who maintain provider/cache scripts. Do not return this file as an authoring path for main-agent artifact drafting or operator script-runner guidance.

## Cache files

The GitHub issue cache projection uses these files under the issue cache directory:

- `issue.md`: Markdown issue body with projection-owned YAML frontmatter.
- `metadata.yml`: non-user-facing cache freshness metadata.
- `comments/index.yml` and `comments/*.md`: comment projection.
- `relationships.yml`: current provider relationship projection.
- `relationships-pending.yml`: pending relationship intent before provider write.

`issue.md` frontmatter is projection-owned and currently carries `schema_version`, `title`, `state`, `state_reason`, `labels`, and `source_updated_at`. `fetched_at` belongs in `metadata.yml`, not `issue.md`.

For cached body edits, the main assistant edits only the Markdown body below existing `issue.md` frontmatter. Provider-owned frontmatter changes must go through workflow provider/cache operations.

## Relationship projection

`relationships.yml` is a cache projection of provider state, not an author-editable metadata source. Refresh it through workflow cache/provider operations.

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

## Pending relationship intent

`relationships-pending.yml` is write intent. Apply it through workflow provider operations, then refresh the current projection.

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

Supported aliases exist for compatibility, but generated intent should prefer `parent`, `children`, `dependencies.blocked_by`, `dependencies.blocking`, and `related`.
