# Review Report Persistence

After each `arch-reviewer` invocation, the reviewer agent writes the report directly to the file path provided by the invoking skill.

## File Path

`A4/<topic-slug>.arch.review-<label>.md`

Where `<label>` identifies the review context:
- **Area review:** use the scope and revision number (e.g., `review-components-1`, `review-teststrategy-2`)
- **Full review (End Iteration):** use the revision number (e.g., `review-full-1`, `review-full-2`)
- **Final review (Finalize):** use `review-final`

## Frontmatter

```markdown
---
type: review-report
source: <topic-slug>.arch.md
scope: <Technology Stack | Components | Test Strategy | Full>
revision: <current revision number>
reviewed: <YYYY-MM-DD HH:mm>
---
```

## Content

Write the reviewer's full report as-is below the frontmatter — do not summarize or truncate.

## Purpose

- Preserves the review trail for auditing across iterations
- Enables resume after interruption: read existing reports to understand what was already flagged
- Provides context to fresh subagent invocations via file path passing
