# Research Report Persistence

After each similar systems research, the research agent writes the results directly to the file path provided by the invoking skill.

## File Path

`A4/<topic-slug>.usecase.research-<label>.md`

Where `<label>` identifies the research context:
- **auto-usecase:** `initial` for Step 3
- **think-usecase:** `1`, `2`, ... numbered sequentially per session

## Consumed Naming Convention

When research results have been reflected into the UC document (e.g., used in UC extraction), rename the file to mark it as consumed:

`<topic-slug>.usecase.research-<label>.md` → `<topic-slug>.usecase.research-<label>.consumed.md`

This allows resume detection via filename alone (Glob) without reading file contents:
- `*.research-initial.consumed.md` → research already reflected, skip research step
- `*.research-initial.md` (without consumed) → research done but not yet reflected, use existing results
- Neither exists → run research

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
