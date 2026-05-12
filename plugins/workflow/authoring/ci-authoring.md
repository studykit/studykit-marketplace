# Workflow CI Authoring

Authoring contract for the `ci` knowledge artifact.

The CI artifact is the workspace reference for how agents and humans verify behavior changes: commands, test layers, fixture assumptions, and provider CI expectations.

The canonical CI artifact is knowledge-backed:

- GitHub repository `wiki/` page when the knowledge provider is GitHub repository `wiki/`.
- Confluence page when the knowledge provider is Confluence.
- Optional filesystem projection only when configured.

Common body rules: `./body-conventions.md`.
Knowledge body rules: `./knowledge-body.md`.
Shared metadata rules: `./metadata-contract.md`.
Provider-specific page rules: `./providers/github-knowledge-authoring.md` or `./providers/confluence-page-authoring.md`.

## Purpose

The CI artifact records the executable verification contract for the project.

Architecture explains the testing strategy. CI records the actual commands and environment assumptions that authors should use before marking implementation work done.

## Identity

Use provider-native page identity.

Suggested title: `CI` or `Test And CI`.

Do not require a legacy local CI file path or workflow-local numeric ID.

## Required body sections

### `## How To Run Tests`

Required.

Record the literal commands that are expected to work in the current project.

Include:

- Unit-test command.
- Integration-test command, if applicable.
- End-to-end or browser-test command, if applicable.
- Multi-tier verification command, if available.
- Required environment variables or setup steps that are safe to document.

Example:

```markdown
## How To Run Tests

| Layer | Command | Notes |
| --- | --- | --- |
| Unit | `npm test -- --runInBand` | No external services. |
| Integration | `npm run test:integration` | Requires local PostgreSQL. |
| All | `npm test` | Smoke check before implementation handoff. |
```

Do not record speculative commands as verified commands. If a command is unverified, label it clearly or move the investigation to a research item.

### `## Test Layout`

Required.

Describe where tests live and how they are named.

Include:

- Test directories by layer.
- Naming conventions.
- Runner configuration files.
- Shared fixtures or test utilities.

### `## CI Pipeline`

Required when the project has provider CI.

Describe the provider pipeline that validates branches and pull requests.

Include:

- Provider and pipeline name.
- Trigger events.
- Required checks.
- Relevant workflow file or pipeline URL.

Provider examples:

- GitHub Actions workflow URL or workflow filename.
- Jira/Bitbucket pipeline URL when Jira is paired with another SCM.
- External CI dashboard URL.

## Optional body sections

### `## Smoke Scenario`

Use for one minimal user-observable interaction that proves the system starts and performs the core behavior.

### `## Fixtures And Environment`

Use for test databases, service emulators, seed data, secrets handling, or container setup.

Do not store secrets.

### `## Troubleshooting`

Use for known local failure modes and fixes.

### `## Related Work`

Use for workflow items that changed the CI contract.

### `## Change Log`

Required for material updates. See `./knowledge-body.md`.

## Update rules

Update the CI artifact when a workflow item changes the verification contract.

Examples:

- A task adds a new test layer.
- A bug fix introduces a regression-test convention.
- A spec changes performance or compatibility verification.
- An architecture decision changes test isolation.
- A review item identifies missing verification guidance.

Every material update should add a `## Change Log` entry linking to the causing workflow artifact.

Example:

```markdown
## Change Log

- 2026-05-13 — #456 — Added browser smoke check for the checkout flow.
```

## Relationship to other artifacts

- Architecture `## Test Strategy` explains why the test layers exist.
- CI `## How To Run Tests` records how to run them.
- Task `## Unit Test Strategy` records task-specific verification.
- Bug `## Unit Test Strategy` records regression coverage for that bug.

Do not duplicate the full CI command table into task or architecture bodies. Link to the CI artifact instead.

## Done criteria

A CI artifact update is done when:

- Required sections are present.
- Commands are verified or explicitly marked as unverified.
- Provider CI links are current when applicable.
- The update has a `## Change Log` entry for the causing workflow item.

## Common mistakes

- Recording commands that have not been run and presenting them as verified.
- Duplicating architecture rationale instead of linking to architecture.
- Adding task-specific verification details that belong in a task or bug.
- Relying on a legacy local CI file as canonical identity in provider-backed mode.
- Omitting the workflow item that caused a CI contract change.
