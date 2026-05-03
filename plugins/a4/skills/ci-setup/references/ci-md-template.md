# a4/ci.md Template (ci-setup Step 5)

Use the `Write` tool with this scaffold for fresh runs. On re-run, use `Edit` to touch only the sections that changed and append a `## Change Logs` bullet citing what drove the update.

The binding shape (required H2, optional H2, canonical H3 names) lives in `${CLAUDE_PLUGIN_ROOT}/authoring/ci-authoring.md`. This scaffold is **stack-neutral** — fill placeholders from the project's actual stack.

````markdown
---
type: ci
updated: <today>
---

## How to run tests

Records the verified per-tier commands. This is the LLM's reference for "how do I verify a feature change?" — `/a4:auto-coding`, `coder`, and `test-runner` read this directly.

| Tier | Command | Purpose | Status |
|------|---------|---------|--------|
| Unit | <unit-test-command> | Unit tests | PASS |
| Integration | <integration-test-command> | Integration tests | PASS |
| E2E | <e2e-test-command> | E2E tests | PASS |

(Include only the tiers in scope per `./tier-assessment.md`.)

### Multi-tier run

<Single command (or short script) that exercises all in-scope tiers in order — typically the CI pipeline's invocation. Used as the smoke check.>

### Test isolation flags

| Tier | Flags |
|------|-------|
| <tier> | <flags / env vars / temp dirs needed for determinism> |

## Test layout

Records where tests live and how they are organized.

| Tier | Location | Naming convention | Runner config |
|------|----------|-------------------|---------------|
| Unit | <path> | <pattern> | <config-file> |
| Integration | <path> | <pattern> | <config-file> |
| E2E | <path> | <pattern> | <config-file> |

## Smoke scenario

<Optional. A single minimal user-observable interaction the running app produces, used by `/a4:auto-coding` as the smoke check after each implementation cycle.>

## Issues

<Optional. Only when review items were emitted during this run. Link to the items emitted in Step 4.>

- Architecture issues (`status: open`): review/<id>-<slug>.md × N
- Environment issues (`status: resolved`): review/<id>-<slug>.md × M
- Environment issues (`status: open`): review/<id>-<slug>.md × K

## Change Logs

- <today> — <one-line why this run touched ci.md>
````
