# GitHub Issue Metadata

Provider-specific metadata and cache projection rules for workflow issue artifacts stored as GitHub Issues.

Read with `../common/issue-authoring.md` and `./github-issue-convention.md`.

## Semantic metadata mapping

- `type`: use a label matching the workflow type as the portable default. Use GitHub Issue Types only when repository setup explicitly enables them.
- `status`: use a GitHub Issue Field when available. Use a status label such as `workflow/status:<state>` when fields are unavailable.
- `priority` and `tags`: use configured fields or labels.
- `title`: use the GitHub issue title.
- `created_at` and `updated_at`: use GitHub timestamps when reading provider state.

GitHub native `state` is provider lifecycle state, not the workflow `status` field. Treat close reasons as provider metadata unless project configuration maps them into workflow status.

## Cache projection

The GitHub issue metadata cache projection uses these files under the issue cache directory:

- `issue.md`: Markdown issue body with projection-owned YAML frontmatter.
- `metadata.yml`: non-user-facing cache freshness metadata.
- `comments/index.yml` and `comments/*.md`: comment projection.

`issue.md` frontmatter is projection-owned and currently carries `schema_version`, `title`, `state`, `state_reason`, `labels`, and `source_updated_at`. `fetched_at` belongs in `metadata.yml`, not `issue.md`.

Edit only the Markdown body below existing `issue.md` frontmatter for body write-back. Change provider-owned metadata through workflow provider/cache operations.

Issue relationships are outside this metadata document. Read `./github-issue-relationships.md` for relationship projection and pending-write files.
