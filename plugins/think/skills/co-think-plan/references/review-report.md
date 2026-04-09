# Review Report Persistence

After each `plan-reviewer` invocation, the reviewer agent writes the report directly to the file path provided by the invoking skill.

## File Path

`A4/co-think/<topic-slug>.impl-plan.review-<label>.md`

Where `<label>` identifies the review context:
- **Phase review:** use the scope (e.g., `review-coverage-1`, `review-feasibility-1`)
- **Full review (End Iteration):** use the revision number (e.g., `review-full-1`, `review-full-2`)
- **Final review (Finalize):** use `review-final`

## Frontmatter

```markdown
---
type: review-report
source: <topic-slug>.impl-plan.md
scope: <Coverage | Feasibility | Full>
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
- Provides context to fresh subagent invocations via file path passing
