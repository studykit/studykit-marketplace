---
name: plantuml:compose
description: >
  Compose PlantUML output or syntax guidance from natural language requests. This
  skill should be used when the user says "draw a diagram", "create a sequence
  diagram", "generate UML", "make a PlantUML", "add a diagram to markdown",
  "insert plantuml block", "show the syntax for a PlantUML diagram", "validate
  my PlantUML", "check this diagram file", or explicitly invokes /plantuml:compose.
argument-hint: [create|reference|check] <diagram request or file>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Compose PlantUML

Compose PlantUML output based on `$ARGUMENTS`.

## Mode Selection

Interpret `$0` as the optional mode when it matches one of:
`create`, `reference`, `check`.

If `$0` is not a mode, treat the full request as the diagram request and infer the mode from intent:

- `create` — write PlantUML (standalone `.puml` file or fenced block into Markdown, based on context)
- `reference` — explain or show PlantUML syntax/patterns without writing files
- `check` — validate PlantUML syntax from a file or snippet, and explain failures without changing it

## Reference Loading

Always start with `references/skill-map.md`.

Then load the matching reference document(s) from `references/`:

- one **primary** reference for the diagram type
- optional **supplemental** references when needed:
  - `references/creole-and-links.md` for formatting, links, tables, math, or rich notes
  - `references/sprites.md` for icons, logos, and stdlib sprites

If the request needs less-common follow-up material, load that file too.

## Workflows

### 1. `create` mode

1. Load references, draft valid PlantUML
2. Write output: standalone `.puml` file, or fenced block into an existing Markdown file if the context indicates it
3. Validate (for Markdown, extract the block body to a temp `.puml` file first)

### 2. `reference` mode

1. Load references for the diagram type or feature
2. Answer with concise syntax guidance and a minimal example
3. Do **not** write files unless the user explicitly asks

### 3. `check` mode

1. Read the target file or snippet
2. If embedded in Markdown, extract only the `plantuml` fenced block body into a temp `.puml` file
   - If multiple blocks exist, check the user-specified one or report which block was checked
3. Validate the `.puml` file
4. Report pass/fail; on failure, explain the cause and show a corrected snippet
5. Do **not** modify files unless the user explicitly asks

## Validation

Always validate after writing or editing PlantUML. If validation fails, fix and re-validate.

- **Local** (preferred): `bash ${CLAUDE_SKILL_DIR}/scripts/validate.sh <file.puml>`
- **Online** (fallback): `uv run ${CLAUDE_SKILL_DIR}/scripts/validate_online.py <file.puml>`
