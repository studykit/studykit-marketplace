# Issue Handling (auto-bootstrap Step 5)

Verification failures from Step 4 are classified, optionally researched, and emitted as review items. The skill follows the **continue + review item** policy for upstream (architecture) findings — see [`wiki-authorship.md §Cross-stage feedback`](${CLAUDE_PLUGIN_ROOT}/docs/wiki-authorship.md). Verified bootstrap state is independently meaningful even when an architecture choice turns out to be wrong; record what was checked, emit review items, and let the user run `/a4:arch iterate` separately.

## Diagnose the issue

- **Architecture issue** — the choice in `architecture.md` is incompatible or incorrect (e.g., stated tool version doesn't support the required runtime, two chosen tiers conflict).
- **Environment issue** — local machine / tooling issue (e.g., missing Java for PlantUML, no display server for E2E on CI).

## Do not guess environment fixes

Before attempting any environment fix:

1. Spawn `Agent(subagent_type: "a4:api-researcher")`. Pass the error message, the failing command, relevant config files, and the technology stack.
2. The agent reads library source / docs as needed and writes findings to `a4/research/bootstrap-<label>.md` (frontmatter `{ label: bootstrap-<label>, scope: bootstrap-troubleshoot, date: <today> }`).
3. Apply the fix based on findings.
4. Re-verify.

If the same fix fails twice, stop and emit a review item rather than retrying further.

## Emit review items

Allocate ids via `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"`.

Review body shape (per `references/review-authoring.md`) requires `<description>`; `<log>` and `<change-logs>` are optional.

### Architecture issue

````markdown
---
type: review
id: <allocated via allocate_id.py>
title: "<short title>"
kind: finding
status: open
target: architecture
source: auto-bootstrap
wiki_impact: [architecture]
priority: high | medium
labels: [bootstrap]
created: <today>
updated: <today>
---

<description>

**Summary.** What was attempted; what failed.

**Evidence.** Build / run / test output, truncated.

**Suggestion.** Re-evaluate <component / test-tier / dependency> choice in architecture.md. Concrete alternative: <proposed fix>. Run `/a4:arch iterate` to address.

</description>
````

### Environment issue (auto-fixed)

````markdown
---
type: review
id: <allocated>
title: "<short title>"
kind: finding
status: resolved
target: bootstrap
source: auto-bootstrap
wiki_impact: []
priority: low
labels: [bootstrap, environment]
created: <today>
updated: <today>
---

<description>

**Summary.** What went wrong.

**Fix applied.** What was done, citing [research/bootstrap-<label>](../../research/bootstrap-<label>.md) if a research report informed the fix.

</description>

<log>

- <today> — resolved at bootstrap time

</log>
````

### Environment issue (unresolved)

Same as auto-fixed but `status: open` and the `<description>` carries a `**Suggestion.**` paragraph with concrete next-step guidance for the user instead of `**Fix applied.**`.
