# Jira Issue Provider Convention

Provider-wide convention rules for workflow artifacts stored as Jira issues.

## Scope

Use these rules for workflow issue artifacts stored in Jira.

This file defines Jira-wide issue writing rules only. Provider metadata authoring boundaries belong in `./jira-issue-metadata.md`. Provider relationship authoring boundaries belong in `./jira-issue-relationships.md`. Artifact-specific body structure and relationship body fallback sections belong in the matching Jira issue type authoring file.

## Identity and references

Use Jira issue keys in visible text.

Examples:

- `PROJ-123`.
- `[PROJ-123]` in GitHub comments when GitHub for Atlassian should create a Jira link.
- Full Jira URL when outside Jira/Atlassian-aware contexts or when a portable link is needed.

Resolve keys using `.workflow/config.yml`, especially the Jira site.

## Relationships

Read `./jira-issue-relationships.md` for provider relationship storage and body-boundary rules.

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
