# Jira Issue Cache Projection

Operator-facing cache projection contract for workflow Jira issue operations.

This file is for `workflow-operator` and plugin contributors. Do not return this file as an authoring path for main-agent artifact drafting.

## Cache files

The Jira Data Center cache projection uses these files under the issue cache directory:

- `issue.json`: native Jira REST issue payload. Cache write-back reads writable fields from this file.
- `remote-links.json`: native Jira remote links payload.
- `metadata.yml`: cache freshness and provider identity metadata.
- `snapshot.md`: generated read-only LLM-facing summary.
- `relationships-pending.yml`: pending relationship intent before provider write.

`metadata.yml` carries cache and provider fields such as `schema_version`, `provider`, `deployment`, `site`, `api_version`, `key`, `project`, `source_updated_at`, `created_at`, `fetched_at`, `url`, and projection filenames.

Do not treat `snapshot.md` as the write-back source. Change provider-owned metadata through workflow provider/cache operations.

## Relationship projection

Current Jira relationships are normalized from provider fields:

- Parent and children come from Jira parent/subtask surfaces when available.
- Dependencies and related issues come from configured Jira issue links.
- Cross-provider references use remote links.

The normalized provider payload exposes workflow relationships under `relationships.workflow` inside the cached issue payload:

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

`snapshot.md` may render a human-readable `## Workflow Relationships` summary from that payload. Do not treat the rendered summary as a write-back source.

## Pending relationship intent

Jira relationship write intent uses `relationships-pending.yml` under the issue cache directory:

```yaml
parent: <jira-key>
children:
  - <jira-key>
dependencies:
  blocked_by:
    - <jira-key>
  blocking:
    - <jira-key>
related:
  - <jira-key>
```

Apply pending relationships through workflow provider operations, then refresh the cached issue payload.
