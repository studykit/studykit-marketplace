---
name: d2:compose
description: >
  Compose D2 diagram output or syntax guidance from natural language requests. This
  skill should be used when the user says "draw a diagram", "create an architecture diagram", "generate
  D2", "make a D2 diagram", "add a diagram to markdown", "insert d2 block",
  "show the syntax for a D2 diagram", or explicitly invokes /d2:compose.
argument-hint: [create|reference|check] <diagram request or file>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch
---

# Compose D2

Compose D2 output based on `$ARGUMENTS`.

## Mode Selection

Interpret `$0` as the optional mode when it matches one of:
`create`, `reference`, `check`.

If `$0` is not a mode, treat the full request as the diagram request and infer the mode from intent:

- `create` — write D2 (standalone `.d2` file or fenced block into Markdown, based on context)
- `reference` — explain or show D2 syntax/patterns without writing files
- `check` — validate D2 syntax from a file or snippet, and explain failures without changing it

## Reference Loading

Always start with `references/skill-map.md`.

Then load the matching reference document(s) from `references/`:

- one **primary** reference for the diagram type or feature
- optional **supplemental** references when the request involves multiple concerns (e.g., special diagram + themes)

If the request needs features not covered by local references, fetch from the [official D2 docs](#official-documentation).

## Workflows

### 1. `create` mode

1. Load references, draft valid D2
2. Pick theme — if the user specified a theme or color preference, map it to a theme ID. Otherwise use theme 3 (Flagship Terrastruct) as the default
3. Write output: standalone `.d2` file, or fenced block into an existing Markdown file if the context indicates it
4. Preview the diagram so the user can see it immediately

### 2. `reference` mode

1. Load references for the diagram type or feature
2. Answer with concise syntax guidance and a minimal example
3. Do **not** write files unless the user explicitly asks

### 3. `check` mode

1. Read the target file or snippet
2. If embedded in Markdown, extract only the `d2` fenced block body into a temp `.d2` file
   - If multiple blocks exist, check the user-specified one or report which block was checked
3. Validate by rendering: `bash ${CLAUDE_SKILL_DIR}/scripts/preview.sh <file.d2>`
4. Report pass/fail; on failure, explain the cause and show a corrected snippet
5. Do **not** modify files unless the user explicitly asks

## Preview

After writing or editing a `.d2` file in `create` mode, always render it:

- **Preview**: `bash ${CLAUDE_SKILL_DIR}/scripts/preview.sh <output.d2> [theme-id] [layout-engine]`
- **Export**: `bash ${CLAUDE_SKILL_DIR}/scripts/export.sh <output.d2> [format] [theme-id] [layout-engine]`

For sketch (hand-drawn) style: `d2 --sketch --theme 3 <output.d2> <output.png>`

Prerequisites: `brew install d2`

## Official Documentation

When local `references/` files don't cover what you need, fetch from the official D2 docs:

| Topic | URL |
|-------|-----|
| Language Tour | https://d2lang.com/tour/intro/ |
| Shapes | https://d2lang.com/tour/shapes |
| Connections | https://d2lang.com/tour/connections |
| Containers | https://d2lang.com/tour/containers |
| Style | https://d2lang.com/tour/style |
| Icons | https://d2lang.com/tour/icons |
| SQL Tables | https://d2lang.com/tour/sql-tables |
| Sequence Diagrams | https://d2lang.com/tour/sequence-diagrams |
| Grid Diagrams | https://d2lang.com/tour/grid-diagrams |
| Classes | https://d2lang.com/tour/classes |
| Globs | https://d2lang.com/tour/globs |
| Themes | https://d2lang.com/tour/themes |
| Layouts | https://d2lang.com/tour/layouts |
| Text & Markdown | https://d2lang.com/tour/text |
| Imports | https://d2lang.com/tour/imports |
| CLI Manual | https://d2lang.com/tour/man/ |
