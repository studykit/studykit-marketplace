# Issue Handling (ci-setup Step 4)

Verification failures from Step 3 are classified, optionally researched, and emitted as review items. ci-setup follows a **continue + review item** policy for upstream (architecture) findings — verified test infrastructure is independently meaningful even when the upstream test strategy turns out wrong; record what was checked, emit review items, and let the user run `/a4:arch iterate` separately.

## Diagnose the issue

- **Architecture issue** — the test strategy in `architecture.md` is incompatible or incorrect (e.g., chosen runner does not support the framework's test mode, declared isolation strategy conflicts with the host).
- **Environment issue** — local machine / tooling issue (e.g., missing display server for E2E on CI, missing system library for the runner).

## Do not guess environment fixes

Before attempting any environment fix:

1. Spawn `Agent(subagent_type: "a4:api-researcher")`. Pass the error message, the failing command, relevant config files, and the test runner being used.
2. The agent reads library source / docs as needed and writes findings to `a4/research/ci-<label>.md` (frontmatter `{ label: ci-<label>, scope: ci-troubleshoot, date: <today> }`).
3. Apply the fix based on findings.
4. Re-verify.

If the same fix fails twice, stop and emit a review item rather than retrying further.

## Emit review items

Allocate ids via `"${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"`.

Review body shape (per `${CLAUDE_PLUGIN_ROOT}/authoring/review-authoring.md`) requires `## Description`; `## Log` and `## Change Logs` are optional.

### Architecture issue

````markdown
---
type: review
id: <allocated via allocate_id.py>
title: "<short title>"
kind: finding
status: open
target: [architecture]
source: ci-setup
priority: high | medium
labels: [ci]
created: <today>
updated: <today>
---

## Description

**Summary.** What was attempted; what failed.

**Evidence.** Runner output, truncated.

**Suggestion.** Re-evaluate <test-tier / runner / isolation-strategy> choice in architecture.md. Concrete alternative: <proposed fix>. Run `/a4:arch iterate` to address.
````

### Environment issue (auto-fixed)

````markdown
---
type: review
id: <allocated>
title: "<short title>"
kind: finding
status: resolved
target: [ci]
source: ci-setup
priority: low
labels: [ci, environment]
created: <today>
updated: <today>
---

## Description

**Summary.** What went wrong.

**Fix applied.** What was done, citing [research/ci-<label>](../../research/ci-<label>.md) if a research report informed the fix.

## Log

- <today> — resolved at ci-setup time
````

### Environment issue (unresolved)

Same as auto-fixed but `status: open` and the `## Description` carries a `**Suggestion.**` paragraph with concrete next-step guidance for the user instead of `**Fix applied.**`.
