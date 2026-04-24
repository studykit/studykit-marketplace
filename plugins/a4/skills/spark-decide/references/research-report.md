# Research Report Persistence

After each option research, the research agent writes detailed findings to a file.

## File Path

`a4/<topic-slug>.decide.research-<label>.md`

Where `<label>` is a short descriptive slug of the option being researched (e.g., `redis-caching`, `graphql-vs-rest`).

## Frontmatter

```markdown
---
type: research-report
source: <topic-slug>.decide.md
option: <the option being researched>
researched: <YYYY-MM-DD HH:mm>
---
```

## Content

This file is a raw data archive. Record all collected materials in detail so the file is self-contained — reviewable without revisiting the original sources. Do not summarize or truncate.

### Required sections

- **Sources consulted** — list every URL, doc page, file path, and search query used. Include sources that yielded no useful results (to prevent re-searching).
- **Raw findings** — paste relevant excerpts, code samples, API signatures, configuration examples, benchmark data, pricing pages, and adoption case studies verbatim. Quote directly rather than paraphrasing.

## Research Index

Maintain `a4/<topic-slug>.decide.research-index.md` as a lookup table. Update the index each time a new research report is created:

```markdown
| # | File | Option | Summary | Date |
|---|------|--------|---------|------|
| 1 | research-redis-caching.md | Redis caching | In-memory store, sub-ms latency, clustering support | 2026-04-13 |
```

Before launching a new research agent, check the index to avoid duplicate research.
