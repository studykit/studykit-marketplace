# Review Report Persistence

After each `plan-reviewer` invocation, the reviewer agent writes the report directly to the file path provided by the invoking skill.

## File Path

`A4/<topic-slug>.plan.review-r<N>.md`

Where `<N>` is the review round number (1, 2, 3).

## Frontmatter

```markdown
---
type: review-report
source: <topic-slug>.plan.md
round: <N>
revision: <plan revision at time of review>
reviewed: <YYYY-MM-DD HH:mm>
---
```

## Content

Write the reviewer's full report as-is below the frontmatter — do not summarize or truncate.

## Purpose

- Preserves the review trail for auditing across iterations
- Enables resume after interruption: read existing reports to understand what was already flagged and fixed
- Tracks which reports have been reflected via the plan's `reflected_files` frontmatter
