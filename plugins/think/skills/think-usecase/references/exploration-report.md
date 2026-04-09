# Exploration Report Persistence

After each `usecase-explorer` invocation, the explorer agent writes the report directly to the file path provided by the invoking skill.

## File Path

`A4/<topic-slug>.usecase.exploration-<label>.md`

Where `<label>` identifies the exploration context:
- **auto-usecase:** use the growth iteration number — one report per growth iteration (e.g., `exploration-1`, `exploration-2`, `exploration-3`)
- **think-usecase:** use the revision number (e.g., `exploration-1`, `exploration-2`)

## Consumed Naming Convention

When exploration results have been reflected into the UC document (e.g., UC candidates composed into full UCs), rename the file to mark it as consumed:

`<topic-slug>.usecase.exploration-<label>.md` → `<topic-slug>.usecase.exploration-<label>.consumed.md`

This allows resume detection via filename alone (Glob) without reading file contents:
- `*.exploration-<label>.consumed.md` → exploration already reflected, skip
- `*.exploration-<label>.md` (without consumed) → exploration done but not yet reflected, use existing results
- Neither exists → run explorer

## Frontmatter

```markdown
---
type: exploration-report
source: <topic-slug>.usecase.md
explored: <YYYY-MM-DD HH:mm>
---
```

## Content

Write the explorer's full report as-is below the frontmatter — do not summarize or truncate. This includes:
- Perspectives explored and applicability assessment
- Gaps found per perspective
- UC candidates with title, actor, and goal

## Purpose

- Preserves exploration results for auditing and traceability
- Enables resume after interruption: read existing reports to avoid re-exploring
- Allows the user to review exploration context in think-usecase sessions
