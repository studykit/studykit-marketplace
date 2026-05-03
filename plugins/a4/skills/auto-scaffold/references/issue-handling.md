# Issue Handling (auto-scaffold Step 4)

Verification failures from Step 3 are classified, optionally researched, and emitted as review items. Scaffold follows a **continue + review item** policy for upstream (architecture) findings — verified scaffold state is independently meaningful even when an architecture choice turns out to be wrong; record what was checked, emit review items, and let the user run `/a4:arch iterate` separately.

## Diagnose the issue

- **Architecture issue** — the choice in `architecture.md` is incompatible or incorrect (e.g., stated tool version doesn't support the required runtime, two chosen components conflict).
- **Environment issue** — local machine / tooling issue (e.g., missing system library, no display server on CI).

## Do not guess environment fixes

Before attempting any environment fix:

1. Spawn `Agent(subagent_type: "a4:api-researcher")`. Pass the error message, the failing command, relevant config files, and the technology stack.
2. The agent reads library source / docs as needed and writes findings to `a4/research/scaffold-<label>.md` (frontmatter `{ label: scaffold-<label>, scope: scaffold-troubleshoot, date: <today> }`).
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
source: auto-scaffold
priority: high | medium
labels: [scaffold]
---

## Description

**Summary.** What was attempted; what failed.

**Evidence.** Build / run / dev-loop output, truncated.

**Suggestion.** Re-evaluate <component / dependency> choice in architecture.md. Concrete alternative: <proposed fix>. Run `/a4:arch iterate` to address.
````

### Environment issue (auto-fixed)

````markdown
---
type: review
id: <allocated>
title: "<short title>"
kind: finding
status: resolved
target: []
source: auto-scaffold
priority: low
labels: [scaffold, environment]
---

## Description

**Summary.** What went wrong.

**Fix applied.** What was done, citing `../../research/scaffold-<label>.md` if a research report informed the fix.

## Log

- <today> — resolved at scaffold time
````

### Environment issue (unresolved)

Same as auto-fixed but `status: open` and the `## Description` carries a `**Suggestion.**` paragraph with concrete next-step guidance for the user instead of `**Fix applied.**`.
