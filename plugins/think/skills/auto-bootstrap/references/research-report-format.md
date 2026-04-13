# Research Report Format

Use this format when writing research reports for bootstrap issues.

## File Path

`A4/<topic-slug>.bootstrap.research-<label>.md`

Where `<label>` is a short slug describing the issue (e.g., `jest-esm-flags`, `esbuild-target-mismatch`).

## Frontmatter

```markdown
---
type: research-report
source: <topic-slug>.bootstrap.md
issue: <the error or issue being investigated>
result: resolved | unresolved | inconclusive
researched: <YYYY-MM-DD HH:mm>
---
```

## Content

This file is a raw data archive. Record all collected materials in detail so the file is self-contained — reviewable without revisiting the original sources. Do not summarize or truncate.

### Required sections

- **Sources consulted** — list every URL, doc page, file path, library source code location, and search query used. Include sources that yielded no useful results (to prevent re-searching).
- **Raw findings** — paste relevant excerpts, error messages, config examples, version-specific notes, known issues, and migration guide steps verbatim. Quote directly rather than paraphrasing.
