# Jira Issue Provider Convention

Provider-wide convention rules for workflow artifacts stored as Jira issues.

## Scope

Use these rules for workflow issue artifacts stored in Jira.

This file defines Jira-wide issue writing rules only. Artifact-specific body structure, issue type mapping, fields, and relationship body fallback sections belong in the matching Jira issue type authoring file.

## Identity and references

Use Jira issue keys in visible text.

Examples:

- `PROJ-123`.
- `[PROJ-123]` in GitHub comments when GitHub for Atlassian should create a Jira link.
- Full Jira URL when outside Jira/Atlassian-aware contexts or when a portable link is needed.

Resolve keys using `.workflow/config.yml`, especially the Jira site.

## Metadata mapping

Prefer native Jira issue types, fields, priorities, and workflow statuses.

Jira issue types and workflows vary by site. Setup must discover or ask for the project-specific mappings instead of assuming a global enum.

Use labels only as fallback or routing metadata when native fields are unavailable or insufficient.

## Relationships

Use Jira issue links when configured link types match workflow semantics.

Common relationship link types include:

- `blocks` / `is blocked by` for dependencies.
- `implements` / `is implemented by` for implementation relationships when available.
- `relates to` for soft related relationships.

Use Jira hierarchy or parent fields for epic and parent relationships when available.

Use remote links for cross-provider references, such as GitHub issues or Confluence pages. If the API requires a stable remote link key, derive it from the resolved workflow reference object.

Relationship writes must use explicit `.workflow/config.yml` mappings. Do not infer Jira link type names, directions, remote-link surfaces, or parent fields from issue body prose.

Body fallback sections for Jira relationships are artifact-specific and belong in the matching Jira issue type authoring file.

## Comments and logs

Use Jira comments, history, and worklog for discussion and work logs.

Do not create a body `## Log` section. Keep the issue body structured and current.

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

- REST wrapper for Jira Data Center APIs.

MCP is fallback transport.

Provider wrapper commands perform the requested write and verification. The caller is responsible for following the authoring resolver/read policy before invoking a write.
