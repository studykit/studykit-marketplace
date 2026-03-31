# Review Report Persistence

After each `usecase-reviewer` invocation, save the full review report to a separate file.

## File Path

`A4/co-think/<topic-slug>.usecase.review-<label>.md`

Where `<label>` identifies the review context:
- **co-think-usecase:** use the revision number (e.g., `review-1`, `review-2`) or `review-final` for finalization
- **auto-usecase:** use the review round number (e.g., `review-1`, `review-2`)

## Frontmatter

```markdown
---
type: review-report
source: <topic-slug>.usecase.md
revision: <current revision number>
reviewed: <YYYY-MM-DD HH:mm>
---
```

## Content

Write the reviewer's full report as-is below the frontmatter — do not summarize or truncate.

## Purpose

- Preserves the review trail for auditing across iterations
- Enables resume after interruption: read existing reports to understand what was already flagged and fixed
- Allows comparison of review quality across iterations
