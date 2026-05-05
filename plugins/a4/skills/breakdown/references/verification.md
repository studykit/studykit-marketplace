# Step 4: Verification + Drift Review

Spawn `Agent(subagent_type: "a4:breakdown-reviewer")`. Pass:

- `a4/` absolute path
- The list of newly written task ids (so the reviewer scopes coverage / references / consistency checks to this round)
- Prior open task-targeted review item ids (for deduplication)

The reviewer emits per-finding review items to `a4/review/<id>-<slug>.md` and returns a summary.

## Walk findings

Apply **stop on strong upstream dependency** — task derivation depends directly on usecases / specs (AC source), cited supporting references, and the codebase that ci-setup verified, so upstream findings halt this skill rather than continuing with stale assumptions.

- **Task-level fix** — edit the affected task file, including `related:` / `## References` when the issue is missing context; edit the review item's `status:` to `resolved` directly. No wiki `## Change Logs` bullet — this skill does not own a wiki page.
- **Upstream finding (`target: architecture`, `target: usecase/...`, `target: <spec/...>`, `target: ci`, or a cited supporting doc)** — **stop**. Leave the review item `status: open`. Tell the user which iterate skill to run next:
  - `target: architecture` → `/a4:arch iterate`
  - `target: usecase/...` → `/a4:usecase iterate`
  - `target: ci` → re-run `/a4:ci-setup`
  - Spec-targeted findings → spec authoring (no dedicated iterate skill yet)
  - Supporting-doc findings → route to the owner of that document, or update it manually before resuming
  After the upstream issue resolves, resume `/a4:breakdown iterate`.
- **Defer** — leave `status: open`. Capture the deferral reason in conversation notes / handoff.

## Loop bound

Loop up to 3 review rounds if task-level revisions are substantial. Once the reviewer returns `ACTIONABLE` (or the user explicitly approves moving on with deferred findings), the batch is ready.

## Optional arch-drift review

When `a4/architecture.md` was present at Step 2 entry **and** the codebase exploration surfaced concrete divergences (file paths the arch names that don't exist in code, component names that don't match, module boundaries that contradict imports, etc.), emit **one** review item summarizing all divergences before handing off:

```yaml
---
type: review
title: "arch drift detected during /a4:breakdown"
kind: finding
status: open
target: [architecture]
source: breakdown
priority: medium
labels: [drift]
---
```

Body: enumerate each divergence with the arch line number and the contradicting code observation. Recommendation line: re-run `/a4:arch` to refresh, or update `architecture.md` manually then close the review.

If no divergences were observed, do not emit the item. If a still-open arch-drift item from a prior `/a4:breakdown` run already exists, skip emission and surface the existing id in the summary.

## Hand-off

Once the loop closes and any `target: architecture` / `target: usecase/...` items are either resolved or deferred:

> Tasks ready. Promote tasks `open → queued` (edit `status:` directly) when they are ready for implementation.
