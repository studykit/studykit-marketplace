# Research Report Persistence

After each similar systems research, the research agent writes the results directly to the file path provided by the invoking skill.

## File Path

`a4/<topic-slug>.usecase.research-<label>.md`

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

This file is a raw data archive. Record all collected materials in detail so the file is self-contained — reviewable without revisiting the original sources. Do not summarize or truncate.

### Required sections

- **Sources consulted** — list every URL, doc page, file path, and search query used. Include sources that yielded no useful results (to prevent re-searching).
- **Raw findings** — paste relevant excerpts, feature lists, user reviews, and comparison data verbatim. Quote directly rather than paraphrasing.

## Research Index

Maintain `a4/<topic-slug>.usecase.research-index.md` as a lookup table. Update the index each time a new research report is created. Use the index as the primary lookup — do not read research report files unless you need the full details.

## Purpose

- Preserves raw research data for auditing and traceability
- Enables resume after interruption: check the research index to avoid re-researching
- Allows the user to review full research context beyond the summary in the main document
