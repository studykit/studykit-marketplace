# Workflow Metadata Contract

Metadata rules shared by workflow artifacts across issue and knowledge providers.

This plugin does not treat Markdown frontmatter as canonical storage in provider-backed mode. Provider-native metadata is the source of truth when available. The workflow adapter may render a normalized metadata view for the assistant, validators, and reports.

## Artifact identity

Use provider-native identity.

| Provider | Identity |
| --- | --- |
| GitHub Issues | `#123` in the configured repository, or `owner/repo#123` across repositories |
| Jira | `PROJ-123` |
| Confluence | Page ID scoped by site; display as page title or Smart Link |
| GitHub Wiki | Wiki path/title scoped by repository |
| Filesystem projection | Provider-resolved reference; local paths are projections, not identity |

Do not require a local monotonic integer id in provider-backed mode.

## Normalized metadata view

Adapters may expose a normalized view like this:

```yaml
type: review
role: issue
provider: github
key: "#456"
title: Clarify retry boundary
status: open
target:
  - input: "#123"
    provider: github
    kind: issue
    display: "#123"
created_at: 2026-05-13T00:00:00Z
updated_at: 2026-05-13T00:30:00Z
```

This view is a translation layer. It is not necessarily stored as YAML in the provider.

## Provider metadata and body fallback

Store workflow metadata in provider-native fields when possible.

Examples:

- GitHub issue type, issue fields, labels, sub-issues, dependencies, comments, and timeline.
- Jira issue type, status, custom fields, issue links, remote links, comments, and history.
- Confluence page properties, labels, page tree, links, comments, and version history.
- GitHub Wiki page body, wiki path, git history, and optional page metadata blocks.

Every relationship that matters to readers must also appear in the body. Provider metadata is useful for automation; body sections are the portable fallback.

## Relationship fields

Workflow relationships include:

| Field | Meaning | Body requirement |
| --- | --- | --- |
| `target` | Artifact reviewed or affected by a review item | Required as `## Target` for review items |
| `implements` | Work item implements a use case or requirement | Required as `## Implements` when present |
| `related` | Soft relationship worth surfacing | Required as `## Related` when present |
| `supersedes` | New knowledge artifact replaces an older one | Required as `## Supersedes` when present |
| `parent` | Work item belongs under an epic or parent work item | Body mention recommended when narrative depends on parent |
| `depends_on` | Work item is blocked by another work item | Required as `## Dependencies` when present |

Use provider-native short references in body text. Resolve them through `workflow.config.yml` and provider context.

Examples:

```markdown
## Target

- #123
- PROJ-456
- [Auth Session v2](https://example.atlassian.net/wiki/spaces/ENG/pages/123456789/Auth+Session+v2)
```

## Status

Status is provider-backed.

- GitHub: canonical workflow status should use Issue Fields when available. Project fields are for planning views.
- Jira: canonical workflow status should map to Jira workflow status.
- Knowledge providers: use provider metadata when available, and body sections for visible state when needed.

Do not assume every provider has the same status enum. Type authoring files define desired workflow semantics; provider authoring files define mapping constraints.

## Logs and history

Do not duplicate provider audit trails in metadata.

- Issue discussion and work logs belong in issue comments or provider-native history.
- Knowledge page history belongs in provider version history.
- Knowledge page `## Change Log` records semantic cause, not full discussion.

## Required authoring behavior

Before creating or editing any workflow artifact:

1. Run the authoring resolver.
2. Read every authoring file returned by the resolver.
3. Write only after the current session ledger records those reads.

Authoring contracts are plugin-bundled Markdown files. Resolver output must use absolute paths.
