# Research Report Persistence

After each similar systems research, the research agent writes the results directly to the file path provided by the invoking skill.

## File Path

`A4/<topic-slug>.usecase.research-<label>.md`

Where `<label>` is a short descriptive slug of the research context (e.g., `competitor-task-management`, `collaboration-features`).

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

## Research Index

Maintain `A4/<topic-slug>.usecase.research-index.md` as a lookup table. Update the index each time a new research report is created. Use the index as the primary lookup — do not read research report files unless you need the full details.

## Purpose

- Preserves raw research data for auditing and traceability
- Enables resume after interruption: check the research index to avoid re-researching
- Allows the user to review full research context beyond the summary in the main document
