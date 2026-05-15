# Jira Issue Metadata

Provider-specific metadata and cache projection rules for workflow issue artifacts stored as Jira issues.

Read with `../common/metadata-contract.md` and `./jira-issue-convention.md`.

## Semantic metadata mapping

- `type`: use the configured Jira issue type or project-specific equivalent. Use labels only as fallback or routing metadata.
- `status`: use Jira workflow status.
- `priority`: use Jira priority or a configured priority field.
- `tags`: use Jira labels or configured fields.
- `title`: use Jira summary.
- `created_at` and `updated_at`: use Jira timestamps when reading provider state.

Jira issue types, fields, priorities, and workflow statuses are site-specific. Setup must use `.workflow/config.yml` mappings instead of assuming a global enum.

## Cache projection

The Jira Data Center cache projection uses these files under the issue cache directory:

- `issue.json`: native Jira REST issue payload. Cache write-back reads writable fields from this file.
- `remote-links.json`: native Jira remote links payload.
- `metadata.yml`: cache freshness and provider identity metadata.
- `snapshot.md`: generated read-only LLM-facing summary.
- `relationships-pending.yml`: pending relationship intent before provider write.

`metadata.yml` carries cache and provider fields such as `schema_version`, `provider`, `deployment`, `site`, `api_version`, `key`, `project`, `source_updated_at`, `created_at`, `fetched_at`, `url`, and projection filenames.

Do not treat `snapshot.md` as the write-back source. Change provider-owned metadata through workflow provider/cache operations.

## Relationship projection

Jira relationships are normalized from provider fields:

- Parent and children come from Jira parent/subtask surfaces when available.
- Dependencies and related issues come from configured Jira issue links.
- Cross-provider references use remote links.

The normalized provider payload exposes workflow relationships under `relationships.workflow`:

```yaml
workflow:
  parent: <jira-issue-ref-object>
  children:
    - <jira-issue-ref-object>
  dependencies:
    blocked_by:
      - <jira-issue-ref-object>
    blocking:
      - <jira-issue-ref-object>
  related:
    - <jira-issue-ref-object>
  external_links:
    - <remote-link-object>
```

Relationship writes must use explicit `.workflow/config.yml` mappings. Do not infer Jira link type names, directions, remote-link surfaces, or parent fields from issue body prose.
