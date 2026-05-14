# Issue Provider Authoring

Common provider-binding rules for issue-backed workflow artifacts stored in GitHub Issues or Jira.

Read this with the semantic authoring file for the artifact type, plus:

- `../metadata-contract.md`
- `../issue-body.md`
- The active provider-specific binding: `./github-issue-authoring.md` or `./jira-issue-authoring.md`

## Scope

Use this binding for issue-backed workflow artifacts:

- `task`
- `bug`
- `spike`
- `epic`
- `review`
- workflow side of `usecase`
- workflow side of `research`

## Identity

Use provider-native identity.

- GitHub Issues: `#123` in the configured repository, or `owner/repo#123` across repositories.
- Jira: `PROJ-123`.

Do not use local projection paths or local numeric IDs as canonical identity for provider-backed issues.

## Type and Status

Represent workflow type and status with provider-native fields when available.

Provider-specific bindings define the concrete mapping:

- GitHub may use labels, issue fields, issue types, or project fields depending on repository setup.
- Jira should use configured issue types and workflow statuses.

If metadata cannot be stored structurally, use the fallback required by the active provider binding.

## Relationships

Use provider-native relationships when they match workflow semantics.

Common relationship meanings:

- `target` — artifact reviewed or affected by a review item.
- `implements` — use case, requirement, spec, or knowledge artifact implemented by a work item.
- `parent` — epic or parent work item that coordinates this item.
- `depends_on` — blocking or ordering dependency.
- `related` — useful non-blocking relationship.

Body fallback is provider-specific. Do not invent relationship body sections unless the active provider binding requires them.

## Comments and History

Use provider comments, work logs, timeline, or history for discussion, work notes, feedback, and audit facts.

Keep the issue body structured and current. Do not turn it into a transcript.

## Write Guard

Provider wrapper commands must enforce the authoring resolver/read-ledger guard before writes, regardless of transport.
