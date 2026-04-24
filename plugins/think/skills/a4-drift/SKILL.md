---
name: a4-drift
description: "This skill should be used when the user explicitly invokes /a4-drift inside a project that uses the think plugin's a4/ workflow. Runs the shared drift detector against the project's a4/ workspace and reports the result. Useful mid-session after a large batch of issue or wiki edits, or before handoff to surface unresolved wiki↔issue inconsistencies."
argument-hint: "[--dry-run]"
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Drift Detection (think plugin)

Runs the shared drift detector against `<project-root>/a4/` and reports any wiki↔issue inconsistencies as new review items in `a4/review/`. Findings carry `source: drift-detector`.

Invocation: `/think:a4-drift [--dry-run]`. With `--dry-run`, drift is detected but no review items are written — useful for inspecting findings before letting the detector commit them.

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || echo NOT_A_GIT_REPO`

If the project root resolved to `NOT_A_GIT_REPO`, abort with a clear message. The detector is workspace-scoped and keyed off the git worktree root.

## Task

### 1. Verify the workspace exists

Check that `<project-root>/a4/` exists and is a directory. If not, tell the user that no `a4/` workspace was found and stop — there is nothing to detect drift against.

### 2. Run the detector

Pass `$ARGUMENTS` straight through to the script so callers can use `--dry-run` or `--json` without the skill needing to know each flag:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/drift_detector.py" \
    "<project-root>/a4" $ARGUMENTS
```

The script exits 0 when it succeeds (regardless of how many findings it emits) and writes one review item per new finding into `a4/review/<id>-<slug>.md`, allocating ids monotonically across the workspace. Findings already represented by an open / in-progress / dismissed `source: drift-detector` review item are deduplicated and not re-emitted.

### 3. Surface the result

Relay the detector's stdout to the user verbatim. When new review items were written, list them so the user can decide which to walk through next:

- For each newly written `review/<id>-<slug>.md`, optionally read it to summarize the kind, target wiki, and suggested resolution. Keep this short — the underlying file already contains the full body.
- If `--dry-run` was passed, no files were written; the script's stdout already enumerates the candidate findings.

### 4. Suggest a follow-up

Pick the suggestion that matches the result:

- **No new drift, none pre-existing** — "Wiki and issues are in sync. Nothing to do."
- **No new drift, some pre-existing open items** — "Drift detector found nothing new. There are still N open `source: drift-detector` review items from earlier runs; resolve them via the next applicable iteration skill (e.g., `/think:think-usecase iterate`, `/think:think-arch iterate`, `/think:think-plan iterate`)."
- **New drift written** — "Drift detector emitted N new review items in `a4/review/`. They will be picked up by the next iteration of the relevant `/think:think-*` skill, or you can walk them now."

Do not edit wiki pages or issue files yourself; the iteration skills are responsible for resolution.

## Detection Rules (reference)

The detector emits one review item per drift, with `target: <wiki>` and `wiki_impact: [<wiki>]` set. Drift kinds and the labels they carry:

| Kind | Review kind | Priority | Trigger |
|------|-------------|----------|---------|
| `close-guard` | gap | high | Resolved review item declares `wiki_impact: [<wiki>]` but `<wiki>.md` has no footnote citing the causing issue. |
| `missing-wiki-page` | gap | high | A `wiki_impact` entry names a wiki page that does not exist at `a4/` root. |
| `stale-footnote` | finding | medium | Footnote definition's wikilink resolves to a non-existent issue or wiki page. |
| `orphan-marker` | finding | low | Inline `[^N]` marker without a `## Changes` definition. |
| `orphan-definition` | finding | low | `## Changes` defines `[^N]:` but no inline `[^N]` marker exists. |

Each emitted review item carries `labels: [drift, drift:<kind>, drift-cause:<cause-slug>?]` for downstream filtering and dedup.

## Non-Goals

- Do not fix the drift here. The skill only detects and emits; resolution is the relevant `/think:think-*` iteration skill's responsibility.
- Do not invoke this skill autonomously. It is a user-triggered manual check; bulk-generation skills (`auto-bootstrap`) and compass already invoke `drift_detector.py` directly at the right moments.
