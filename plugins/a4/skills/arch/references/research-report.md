# Research Report Persistence

After each technical claim verification, the research subagent writes the results to a file.

## File Path

`a4/<topic-slug>.arch.research-<label>.md`

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

This file is a raw data archive. Record all collected materials in detail so the file is self-contained — reviewable without revisiting the original sources. Do not summarize or truncate.

### Required sections

- **Sources consulted** — list every URL, doc page, file path, and search query used. Include sources that yielded no useful results (to prevent re-searching).
- **Raw findings** — paste relevant excerpts, code samples, API signatures, configuration examples, and version-specific details verbatim. Quote directly rather than paraphrasing.

## Research Index

Maintain `a4/<topic-slug>.arch.research-index.md` as a lookup table. Update the index each time a new research report is created:

```markdown
| # | File | Tags | Summary | Date |
|---|------|------|---------|------|
| 1 | research-webdriverio-vscode.md | WebdriverIO, VS Code, wdio-vscode-service | Webview iframe access confirmed, version requirements | 2026-04-10 |
```

Before launching a new research subagent, check the index to avoid duplicate research.

## Inline Reference

Research reports are tracked via the research index and inline references in the arch, **not** via `reflected_files`. When a verification result influences a decision, add an inline reference:

`(ref: research-webdriverio-vscode.md)`
