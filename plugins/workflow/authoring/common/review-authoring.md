# Workflow Review Authoring

A workflow review item is an **issue-backed feedback workflow artifact**. It captures a single finding, gap, or question that must be triaged, tracked, and resolved.

Review items are not page comments and not long-form documents. They are the workflow mailbox for feedback that needs status, priority, assignment, discussion, and closure.

Companion contracts:

- `./metadata-contract.md`
- `./body-conventions.md`
- Issue rules: `./issue-authoring.md`

## Storage role

`review` is always stored in the issue backend.

Do not store workflow review items as knowledge-page comments or knowledge-page sections. Page comments may point to a review item, but they do not replace it.

## Review kinds

`kind` is required metadata.

| Kind | Meaning |
| --- | --- |
| `finding` | Something is wrong, inconsistent, risky, or below the expected contract. |
| `gap` | Something expected is missing or incomplete. |
| `question` | A decision or clarification is needed before the target can be considered settled. |

Each review item should contain one concern only. Do not pack multiple findings, gaps, or questions into one review item.

## Required metadata

Represent this metadata structurally when possible. If a field cannot be stored structurally, include the value in the body when the selected authoring files require it.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | Always `review`. Use issue metadata when available. |
| `kind` | yes | `finding`, `gap`, or `question`. |
| `status` | yes | Workflow lifecycle status. |
| `target` | yes for target-specific reviews | Artifact or artifacts being reviewed. Represent according to the selected authoring files. |
| `source` | recommended | `self`, agent name, reviewer name, or process that emitted the review. |
| `priority` | recommended | `high`, `medium`, or `low`, or workflow priority equivalent. |
| `tags` | optional | Classification tags. |

Use canonical issue identity. Do not use local integer ids.

## Review target rules

A review item must identify what it reviewed unless the concern is truly cross-cutting.

Targets may point to:

- Issue artifacts: task, bug, spike, epic, usecase workflow issue, research workflow issue, another review.
- Knowledge artifacts: spec, architecture, domain, context, actors, nfr, ci, curated usecase page, curated research page.

Represent targets according to the selected authoring files.

Do not invent placeholder targets. If the review is cross-cutting, say so explicitly in `## Description`.

## Lifecycle

Recommended semantic lifecycle:

```text
open        → discarded | in-progress
in-progress → discarded | resolved
resolved    → terminal
discarded   → terminal
```

Status mapping depends on the configured issue backend.

Status meaning:

- `open` — Feedback is in the inbox and not yet selected for resolution.
- `in-progress` — Someone is actively resolving it.
- `resolved` — The target artifact reflects the resolution.
- `discarded` — The feedback is no longer applicable or intentionally rejected.

`open` is the default initial status.

## Resolution rule

A review should not be marked `resolved` until every target artifact reflects the resolution.

For knowledge targets, the target page should include a `## Change Log` entry that links back to the review item or to the causing workflow artifact that resolved the review.

For issue targets, the target issue should include the relevant body/metadata change or an explicit comment explaining why no content change was needed.

If the fix is deferred, keep the review open or in-progress. Do not mark it resolved merely because a follow-up task was created unless the team explicitly treats that handoff as resolution.

## Body shape

Review bodies are deliberately compact.

Required:

```markdown
## Description

<one concern, why it matters, and what would resolve it>
```

Target-specific reviews must identify the target according to the selected authoring files. For truly cross-cutting reviews, `## Description` must explain why there is no specific target.

Optional sections:

- `## Resume` — current-state snapshot while the review is being resolved. See `./body-conventions.md`.
- `## Suggested Fix` — concise proposed action when useful.
- `## Evidence` — short links, snippets, or reproduction notes.

Unknown Title Case H2 headings are tolerated, but keep reviews short.

## Description guidance

For each kind:

- `finding`: explain what is wrong, where it appears, and why it matters.
- `gap`: explain what is missing, why it should exist, and what artifact should receive it.
- `question`: state the unresolved question and what answer would allow progress.

## Comments and discussion

Use comments for:

- Back-and-forth discussion.
- Reviewer clarification.
- Resolution notes.
- Evidence discovered after creation.

Keep the issue body as the current compact summary.

## Common mistakes

- Missing target identity for a target-specific review.
- Packing several findings into one review item.
- Using a page comment instead of a review item for feedback that needs workflow tracking.
- Marking `resolved` before the target artifact was updated.
- Duplicating long discussion in the issue body instead of comments.
- Using local projection paths or local integer ids as canonical identity.

## Do not

- Do not store review as a knowledge page.
- Do not create placeholder targets.
- Do not use closing keywords or Smart Commit commands unless the workflow intentionally wants automated side effects.
- Do not auto-trigger a skill just because a review item is being written; follow the authoring resolver policy.
