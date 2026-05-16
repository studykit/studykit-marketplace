# Jira Issue Relationships

Provider-specific relationship rules for workflow issue artifacts stored as Jira issues.

Read with `../common/issue-authoring.md`, `./jira-issue-convention.md`, and `./jira-issue-metadata.md`.

## Boundary

Issue relationships are not issue metadata fields. Do not store parent, child, dependency, related issue, or remote-link state in provider metadata files.

Use Jira-native relationships when configured:

- Parent and children come from Jira parent/subtask or hierarchy surfaces.
- Dependencies and related issues come from configured Jira issue links.
- Cross-provider references use remote links.

Relationship writes must use explicit `.workflow/config.yml` mappings. Do not infer Jira link type names, directions, remote-link surfaces, or parent fields from issue body prose.

## Cache projection

Jira Data Center cache stores current native issue payloads in `issue.json` and remote links in `remote-links.json`.

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

## Pending intent schema

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

## Body boundary

Use body fallback sections only when configured native relationship storage is unavailable or intentionally insufficient for readers. Do not duplicate native Jira links or remote links in the body.
