# Workflow Review Authoring

A workflow review item captures a single finding, gap, or question that needs
independent workflow tracking.

Use an existing issue comment when the feedback is local to that issue and can
be resolved as part of the issue's normal work. Create a review item when the
feedback needs separate ownership, prioritization, discussion, or completion
criteria.

Companion contracts:

- `./issue-body.md`
- Issue rules: `./issue-authoring.md`

Do not create a review item for every comment. Use comments for local
discussion. Use a review item when the feedback must be tracked independently.

## Review concern

State the concern type in the title or body.

| Concern | Meaning |
| --- | --- |
| `finding` | Something is wrong, inconsistent, risky, or below the expected contract. |
| `gap` | Something expected is missing or incomplete. |
| `question` | A decision or clarification is needed before the target can be considered settled. |

Each review item should contain one concern only. Do not pack multiple findings, gaps, or questions into one review item.

## Review target rules

A review item must identify the specific issue, knowledge page, or small set of
reviewed content that must change or answer the concern. If the concern is truly
cross-cutting, say so explicitly in `## Description`.

Choose the narrowest useful target:

- The issue whose body, acceptance criteria, plan, or discussion must change.
- The knowledge page whose content must change.
- A small set of reviewed items when the same concern applies to all of them.

Do not list every related item. Do not invent placeholder targets.

## Resolution criteria

Treat a review as complete only when every target item reflects the resolution.

For knowledge targets, the target page should include a `## Change Log` entry that links back to the review item or to the causing issue that resolved the review.

For issue targets, the target issue should include the relevant body change or an explicit comment explaining why no content change was needed.

If the fix is deferred, do not treat the review as complete merely because a follow-up task was created unless the team explicitly treats that handoff as resolution.

## Body shape

Review bodies are deliberately compact.

Required:

```markdown
## Description

<one concern, why it matters, and what would resolve it>
```

Target-specific reviews must identify the target according to the selected authoring files. For truly cross-cutting reviews, `## Description` must explain why there is no specific target.

Optional sections:

- `## Resume` — current-state snapshot while the review is being resolved. See `./issue-body.md`.
- `## Suggested Fix` — concise proposed action when useful.
- `## Evidence` — short links, snippets, or reproduction notes.

Unknown Title Case H2 headings are tolerated, but keep reviews short.

## Description guidance

For each concern:

- `finding`: explain what is wrong, where it appears, and why it matters.
- `gap`: explain what is missing, why it should exist, and what item should receive it.
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
- Treating a review as complete before the target item was updated.
- Duplicating long discussion in the issue body instead of comments.

## Do not

- Do not store review as a knowledge page.
- Do not create placeholder targets.
- Do not use one review item for multiple unrelated concerns.
