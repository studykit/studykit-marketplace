# GitHub Issue Metadata

Provider-specific metadata and cache projection rules for workflow issue artifacts stored as GitHub Issues.

Read with `../common/metadata-contract.md` and `./github-issue-convention.md`.

## Semantic metadata mapping

- `type`: use a label matching the workflow type as the portable default. Use GitHub Issue Types only when repository setup explicitly enables them.
- `status`: use a GitHub Issue Field when available. Use a status label such as `workflow/status:<state>` when fields are unavailable.
- `priority` and `tags`: use configured fields or labels.
- `title`: use the GitHub issue title.
- `created_at` and `updated_at`: use GitHub timestamps when reading provider state.

GitHub native `state` is provider lifecycle state, not the workflow `status` field. Treat close reasons as provider metadata unless project configuration maps them into workflow status.

## Cache projection

The GitHub issue cache projection uses these files under the issue cache directory:

- `issue.md`: Markdown issue body with projection-owned YAML frontmatter.
- `metadata.yml`: non-user-facing cache freshness metadata.
- `comments/index.yml` and `comments/*.md`: comment projection.
- `relationships.yml`: provider relationship projection.
- `relationships-pending.yml`: pending relationship intent before provider write.

`issue.md` frontmatter is projection-owned and currently carries `schema_version`, `title`, `state`, `state_reason`, `labels`, and `source_updated_at`. `fetched_at` belongs in `metadata.yml`, not `issue.md`.

Edit only the Markdown body below existing `issue.md` frontmatter for body write-back. Change provider-owned metadata through workflow provider/cache operations.

## Relationship projection

Use GitHub-native relationships when available:

- Parent and child relationships use GitHub sub-issue metadata.
- Blocking relationships use GitHub issue dependency metadata.

`relationships.yml` uses a normalized provider projection:

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
