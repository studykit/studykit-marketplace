# Workflow Review Authoring

A workflow review item is an **issue-backed feedback workflow artifact**. It captures a single finding, gap, or question that must be triaged, tracked, and resolved.

Review items are not page comments and not long-form documents. They are the workflow mailbox for feedback that needs status, priority, assignment, discussion, and closure.

Companion contracts:

- `./metadata-contract.md`
- `./issue-body.md`
- Provider binding: `./providers/github-issue-authoring.md` or `./providers/jira-issue-authoring.md`

## Storage role

`review` is always stored in the issue backend.

Supported issue providers:

- GitHub Issues
- Jira

Do not store workflow review items as Confluence comments, GitHub Wiki notes, or knowledge-page sections. Page comments may point to a review item, but they do not replace it.

## Review kinds

`kind` is required metadata.

| Kind | Meaning |
| --- | --- |
| `finding` | Something is wrong, inconsistent, risky, or below the expected contract. |
| `gap` | Something expected is missing or incomplete. |
| `question` | A decision or clarification is needed before the target can be considered settled. |

Each review item should contain one concern only. Do not pack multiple findings, gaps, or questions into one review item.

## Required metadata

Represent this metadata using provider-native fields when available. If a provider cannot store a field structurally, include the value in the issue body.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | Always `review`. Use issue type, label, or field depending on provider. |
| `kind` | yes | `finding`, `gap`, or `question`. |
| `status` | yes | Provider-backed lifecycle status. |
| `target` | yes for target-specific reviews | Artifact or artifacts being reviewed. Use metadata when possible and always include `## Target` in the body. |
| `source` | recommended | `self`, agent name, reviewer name, or process that emitted the review. |
| `priority` | recommended | `high`, `medium`, or `low`, or provider priority equivalent. |
| `labels` | optional | Provider labels/tags. |

Provider identity replaces local integer ids. Use GitHub issue numbers or Jira keys.

## Target rules

A review item must identify what it reviewed unless the concern is truly cross-cutting.

Targets may point to:

- Issue artifacts: task, bug, spike, epic, usecase workflow issue, research workflow issue, another review.
- Knowledge artifacts: spec, architecture, domain, context, actors, nfr, ci, curated usecase page, curated research page.

Use provider-native short refs in body text:

```markdown
## Target

- #123
- PROJ-456
- [Architecture](https://example.atlassian.net/wiki/spaces/ENG/pages/123456789/Architecture)
```

If target metadata is unavailable or unreliable, `## Target` is the fallback source for target resolution.

Do not invent placeholder targets. If the review is cross-cutting, say so explicitly in `## Description`.

## Lifecycle

Recommended semantic lifecycle:

```text
open        → discarded | in-progress
in-progress → discarded | resolved
resolved    → terminal
discarded   → terminal
```

Provider mappings may vary:

- GitHub: use Issue Field status when available; labels or project fields are fallback/planning views.
- Jira: map to configured Jira workflow statuses.

Status meaning:

- `open` — Feedback is in the inbox and not yet selected for resolution.
- `in-progress` — Someone is actively resolving it.
- `resolved` — The target artifact reflects the resolution.
- `discarded` — The feedback is no longer applicable or intentionally rejected.

`open` is the default initial status.

## Resolution rule

A review should not be marked `resolved` until every target artifact reflects the resolution.

For knowledge targets, the target page should include a `## Change Log` entry that links back to the review item or to the causing workflow artifact that resolved the review.

For issue targets, the target issue should include the relevant body/metadata change or an explicit provider comment explaining why no content change was needed.

If the fix is deferred, keep the review open or in-progress. Do not mark it resolved merely because a follow-up task was created unless the team explicitly treats that handoff as resolution.

## Body shape

Review bodies are deliberately compact.

Required:

```markdown
## Target

- <provider-native ref or URL>

## Description

<one concern, why it matters, and what would resolve it>
```

`## Target` may be omitted only for truly cross-cutting reviews. In that case, `## Description` must explain why there is no specific target.

Optional sections:

- `## Resume` — current-state snapshot while the review is being resolved. See `./issue-body.md`.
- `## Log` — use only when provider comments are unavailable or when a short in-body narrative is necessary. Prefer provider comments for discussion.
- `## Suggested Fix` — concise proposed action when useful.
- `## Evidence` — short links, snippets, or reproduction notes.

Unknown Title Case H2 headings are tolerated, but keep reviews short.

## Description guidance

For each kind:

- `finding`: explain what is wrong, where it appears, and why it matters.
- `gap`: explain what is missing, why it should exist, and what artifact should receive it.
- `question`: state the unresolved question and what answer would allow progress.

## Comments and discussion

Use provider comments for:

- Back-and-forth discussion.
- Reviewer clarification.
- Resolution notes.
- Evidence discovered after creation.

Keep the issue body as the current compact summary.

## Common mistakes

- Missing `## Target` for a target-specific review.
- Packing several findings into one review item.
- Using a page comment instead of a review item for feedback that needs workflow tracking.
- Marking `resolved` before the target artifact was updated.
- Duplicating long discussion in the issue body instead of comments.
- Using local projection paths or local integer ids as provider-backed identity.

## Do not

- Do not store review as a knowledge page.
- Do not rely only on metadata for `target`; include `## Target` in the body.
- Do not create placeholder targets.
- Do not use closing keywords or Smart Commit commands unless the workflow intentionally wants provider side effects.
- Do not auto-trigger a skill just because a review item is being written; follow the authoring resolver policy.
