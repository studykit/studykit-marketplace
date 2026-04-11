# Research Report Persistence

After each technical claim verification, the research subagent writes the results to a file.

## File Path

`A4/<topic-slug>.arch.research-<label>.md`

Where `<label>` is a short descriptive slug of the claim being verified (e.g., `webdriverio-vscode`, `agent-sdk-session-events`).

## Frontmatter

```markdown
---
type: research-report
source: <topic-slug>.arch.md
claim: <the technical claim being verified>
result: verified | unverified | inconclusive
researched: <YYYY-MM-DD HH:mm>
---
```

## Content

Write the research subagent's full output as-is below the frontmatter — do not summarize or truncate. This includes:
- Official documentation excerpts or links
- Version-specific details
- Caveats or limitations found
- Sources consulted

## Research Index

Maintain `A4/<topic-slug>.arch.research-index.md` as a lookup table. Update the index each time a new research report is created:

```markdown
| # | File | Tags | Summary | Date |
|---|------|------|---------|------|
| 1 | research-webdriverio-vscode.md | WebdriverIO, VS Code, wdio-vscode-service | Webview iframe access confirmed, version requirements | 2026-04-10 |
```

Before launching a new research subagent, check the index to avoid duplicate research.

## Inline Reference

Research reports are tracked via the research index and inline references in the arch, **not** via `reflected_files`. When a verification result influences a decision, add an inline reference:

`(ref: research-webdriverio-vscode.md)`
