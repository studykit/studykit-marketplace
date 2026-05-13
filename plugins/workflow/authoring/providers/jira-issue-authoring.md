# Jira Issue Provider Authoring

Provider binding rules for workflow artifacts stored as Jira issues.

Read with the semantic authoring file for the artifact type, plus:

- `../metadata-contract.md`
- `../issue-body.md`

## Scope

Use this binding for issue-backed workflow artifacts stored in Jira:

- `task`
- `bug`
- `spike`
- `epic`
- `review`
- workflow side of `usecase`
- workflow side of `research`

## Identity and references

Use Jira issue keys in visible text.

Examples:

- `PROJ-123`
- `[PROJ-123]` in GitHub comments when GitHub for Atlassian should create a Jira link.
- Full Jira URL when outside Jira/Atlassian-aware contexts or when a portable link is needed.

Resolve keys using `.workflow/config.yml`, especially the Jira site.

## Type mapping

Prefer native Jira issue types.

Suggested mapping:

- `task` → Jira Task or configured equivalent.
- `bug` → Jira Bug.
- `spike` → Jira Spike if available, otherwise configured Task subtype or label.
- `epic` → Jira Epic or configured hierarchy type.
- `review` → configured Review/Task type plus workflow metadata.
- `usecase` workflow side → configured Story/Task type.
- `research` workflow side → configured Research/Task type.

Jira issue types vary by site. The setup flow must discover or ask for mappings.

## Status mapping

Canonical workflow status maps to Jira workflow status.

Do not assume a fixed status enum. Jira workflows vary by project.

The setup flow should map workflow semantic states to project-specific Jira statuses.

## Relationships

Use Jira issue links when configured link types match workflow semantics.

Examples:

- `blocks` / `is blocked by` for dependencies.
- `implements` / `is implemented by` when available.
- `relates to` for soft relationships.

Use Jira hierarchy or parent fields for epic/parent relationships when available.

Use remote links for cross-provider references, such as GitHub issues or Confluence pages. If the API requires a stable remote link key, derive it from the resolved workflow reference object.

Always include visible body sections for relationships, even when native links exist.

## Review items

A workflow `review` is always a Jira issue when Jira is the configured issue provider.

It must include:

```markdown
## Target

- PROJ-123
- [Architecture](https://example.atlassian.net/wiki/spaces/ENG/pages/123456789/Architecture)
```

Use Jira custom fields or remote links for `target` when possible, but do not omit the body section.

## Comments and logs

Use Jira comments, history, and worklog for discussion and work logs.

Keep the issue body structured and current.

## Branch, commit, and PR conventions

Default branch pattern:

```text
PROJ-123-some-name
```

Default commit pattern:

```text
PROJ-123 <summary>
```

Default PR title pattern:

```text
PROJ-123 <summary>
```

A slash branch pattern such as `PROJ-123/some-name` may work, but the default is hyphen for compatibility with Atlassian examples and common tooling.

## Smart Commits

Use Jira Smart Commit commands only when the workflow intentionally wants Jira command side effects.

Do not use Smart Commit commands merely to mention an issue.

## Transport

Preferred native transport:

- REST wrapper for Jira Cloud APIs.

MCP is fallback transport.

Provider wrapper commands must enforce the authoring resolver/read-ledger guard before writes, regardless of transport.
