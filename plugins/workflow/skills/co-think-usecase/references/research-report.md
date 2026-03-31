# Research Report Persistence

After each similar systems research, save the full research results to a separate file.

## File Path

`A4/co-think/<topic-slug>.usecase.research-<label>.md`

Where `<label>` identifies the research context:
- **auto-usecase:** `initial` for Step 3, `targeted-7b` for targeted research in Step 7b
- **co-think-usecase:** `1`, `2`, ... numbered sequentially per session

## Frontmatter

```markdown
---
type: research-report
source: <topic-slug>.usecase.md
research-query: <brief description of what was researched>
researched: <YYYY-MM-DD HH:mm>
---
```

## Content

Write the research worker's full output as-is below the frontmatter — do not summarize or truncate. This includes:
- Similar systems found and their key features
- High-value UC candidates (common across 3+ systems)
- Niche UC candidates (unique to 1 system)
- User-requested features (from reviews/forums)

## Purpose

- Preserves raw research data for auditing and traceability
- Enables resume after interruption: read existing reports to avoid re-researching
- Allows the user to review full research context beyond the summary in the main document
