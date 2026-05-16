# Jira Issue Provider Convention

Provider-wide convention rules for workflow artifacts stored as Jira issues.

## Scope

Use these rules for workflow issue artifacts stored in Jira.

This file defines Jira-wide issue writing rules only. Provider metadata authoring boundaries belong in `./jira-issue-metadata.md`. Provider relationship authoring boundaries belong in `./jira-issue-relationships.md`. Jira body anti-patterns belong in `./jira-issue-anti-patterns.md`. Artifact-specific body structure and relationship body fallback sections belong in the matching Jira issue type authoring file.

## Identity and references

Use Jira issue keys in visible text.

Examples:

- `PROJ-123`.
- `[PROJ-123]` in GitHub comments when GitHub for Atlassian should create a Jira link.
- Full Jira URL when outside Jira/Atlassian-aware contexts or when a portable link is needed.

Resolve keys using `.workflow/config.yml`, especially the Jira site.

## Relationships

Read `./jira-issue-relationships.md` for provider relationship storage and body-boundary rules.

Read `./jira-issue-anti-patterns.md` for forbidden relationship body sections.

Body fallback sections for Jira relationships are artifact-specific and belong in the matching Jira issue type authoring file.

## Comments and logs

Use Jira comments, history, and worklog for discussion and work logs.

Do not create a body `## Log` section. Keep the issue body structured and current.

## Implementation summary comments

When updating an issue after implementation, keep the comment concise.

Recommended shape:

```markdown
Implemented <short outcome>.

Why:
- <reason this change was needed>

Summary:
- <material change>
- <material change>

Validation: local workflow checks passed.

- <commit-ref>
```

Rules:

- Include `Why:` when the motivation is not obvious, the change removes
  behavior or documentation, or the work changes an agent, provider, or
  authoring boundary.
- Do not paste unit test output, test file lists, or verbose validation logs into issue comments.
- Prefer one short commit reference per relevant commit.
- Keep implementation details high-level; link or reference changed files only when the distinction matters.

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
