# Research Report Persistence

After each technical claim verification, the research subagent writes the results to a file.

## File Path

`A4/<topic-slug>.spec.research-<label>.md`

Where `<label>` is a short descriptive slug of the claim being verified (e.g., `nextjs-server-actions`, `postgres-jsonb-index`).

## Frontmatter

```markdown
---
type: research-report
source: <topic-slug>.spec.md
claim: <the technical claim being verified>
result: verified | unverified | inconclusive
researched: <YYYY-MM-DD HH:mm>
---
```

## Content

Write the research subagent's full output as-is below the frontmatter — do not summarize or truncate. This includes:
- Official documentation excerpts or links
- Version-specific details (when the feature was introduced, deprecated, etc.)
- Caveats or limitations found
- Sources consulted

## Research Index

Maintain `A4/<topic-slug>.spec.research-index.md` as a lookup table. Update the index each time a new research report is created:

```markdown
| # | File | Tags | Summary | Date |
|---|------|------|---------|------|
| 1 | research-nextjs-server-actions.md | Next.js, Server Actions, v14 | Official docs, version-specific support scope, constraints summary | 2026-04-10 |
```

Before launching a new research subagent, check the index to avoid duplicate research.

## Inline Reference

Research reports are tracked via the research index and inline references in the spec, **not** via `reflected_files`. When a verification result influences a spec decision, add an inline reference where the claim is recorded:

`(ref: research-nextjs-server-actions.md)`

This allows the same report to be referenced from multiple locations across phases.

## Purpose

- Avoids redundant verification — the same claim referenced across phases can reuse the report
- Preserves raw research data for auditing and traceability
- Enables resume after interruption: read existing reports to skip re-researching
