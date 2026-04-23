# Review Report Persistence

After each `usecase-reviewer` invocation, the reviewer agent writes the report directly to the file path provided by the invoking skill.

## File Path

`a4/<topic-slug>.usecase.review-<label>.md`

Where `<label>` identifies the review context:
- **think-usecase:** use the revision number (e.g., `review-1`, `review-2`) or `review-final` for finalization
- **auto-usecase:** use `g<iteration>-q<round>` format to distinguish growth iterations from quality rounds (e.g., `review-g1-q1`, `review-g1-q2`, `review-g2-q1`)

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
