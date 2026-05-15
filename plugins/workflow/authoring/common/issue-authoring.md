# Workflow Issue Authoring

Common semantic rules for issue-backed workflow artifacts.

Read this with the semantic authoring file for the artifact type, plus:

- `./metadata-contract.md`
- `./body-conventions.md`

## Scope

Use these rules for issue-backed workflow artifacts:

- `task`
- `bug`
- `spike`
- `epic`
- `review`
- workflow side of `usecase`
- workflow side of `research`

## Identity

Use the issue identity supplied by the configured issue backend.

Do not introduce workflow-local issue IDs. Do not use local projection paths or local numeric IDs as canonical issue identity.

## Type and status

Every issue-backed artifact has a workflow type and lifecycle status.

Type-specific authoring files define semantic states. Backend-specific authoring files define how those states are stored and displayed.

## Relationships

Common relationship meanings:

- `target` — artifact reviewed or affected by a review item.
- `implements` — use case, requirement, spec, or knowledge artifact implemented by a work item.
- `parent` — epic or parent work item that coordinates this item.
- `depends_on` — blocking or ordering dependency.
- `related` — useful non-blocking relationship.

## Comments and history

Use comments, work notes, discussions, or history for:

- Back-and-forth discussion.
- Raw investigation notes.
- Progress notes.
- Review feedback.
- Audit facts.

Keep the issue body structured and current. Do not turn it into a transcript.

## Write workflow

Resolve and read the required authoring files before drafting issue-backed artifact changes. Provider/cache write commands perform the requested mutation and verification; they do not enforce hidden authoring read state.
