# Workflow CI Authoring

Authoring contract for the `ci` knowledge page.

The CI page is the workspace reference for how agents and humans verify behavior changes: commands, test layers, fixture assumptions, and remote CI expectations.

The canonical CI page is knowledge-backed and stored in the configured knowledge backend. Optional filesystem projection is used only when configured.

Knowledge body rules: `./knowledge-body.md`.

## Purpose

The CI page records the executable verification contract for the project.

Architecture explains the testing strategy. CI records the actual commands and environment assumptions that authors should use before marking implementation work done.

## Identity

Use canonical page identity.

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

Required when the project has remote CI.

Describe the remote pipeline that validates branches and pull requests.

Include:

- Pipeline name and host.
- Trigger events.
- Required checks.
- Relevant workflow file or pipeline URL.

Pipeline examples:

- CI workflow URL or workflow filename.
- External pipeline URL when the project uses another CI system.
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

Use for work items that changed the CI contract.

### `## Change Log`

Required for material updates. See `./knowledge-body.md`.

## Update rules

Update the CI page when a work item changes the verification contract.

Examples:

- A task adds a new test layer.
- A bug fix introduces a regression-test convention.
- A spec changes performance or compatibility verification.
- An architecture decision changes test isolation.
- A review item identifies missing verification guidance.

Every material update should add a `## Change Log` entry linking to the causing work item.

Example:

```markdown
## Change Log

- 2026-05-13 — #456 — Added browser smoke check for the checkout flow.
```

## Content boundaries

- Architecture `## Test Strategy` explains why the test layers exist.
- CI `## How To Run Tests` records how to run them.
- Task `## Unit Test Strategy` records task-specific verification.
- Bug `## Unit Test Strategy` records regression coverage for that bug.

Do not duplicate the full CI command table into task or architecture bodies. Link to the CI page instead.

## Done criteria

A CI page update is done when:

- Required sections are present.
- Commands are verified or explicitly marked as unverified.
- Remote CI links are current when applicable.
- The update has a `## Change Log` entry for the causing work item.

## Common mistakes

- Recording commands that have not been run and presenting them as verified.
- Duplicating architecture rationale instead of linking to architecture.
- Adding task-specific verification details that belong in a task or bug.
- Relying on a legacy local CI file as canonical identity when the CI page is knowledge-backed.
- Omitting the work item that caused a CI contract change.
