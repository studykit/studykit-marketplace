---
name: structurizr:compose
description: >
  Compose Structurizr DSL output or syntax guidance from natural language requests. This
  skill should be used when the user says "draw a C4 diagram", "create a system context
  diagram", "generate Structurizr DSL", "make a container diagram", "create a deployment
  view", "add a C4 diagram to markdown", "show the syntax for Structurizr DSL", "validate
  my Structurizr DSL", "check this workspace file", or explicitly invokes
  /structurizr:compose. Also trigger when the user mentions "C4 model", "software
  architecture diagram", or wants to visualize system architecture.
argument-hint: [create|reference|check] <diagram request or file>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch
---

# Compose Structurizr DSL

Compose Structurizr DSL output based on `$ARGUMENTS`.

## Mode Selection

Interpret `$0` as the optional mode when it matches one of:
`create`, `reference`, `check`.

If `$0` is not a mode, treat the full request as the diagram request and infer the mode from intent:

- `create` — write Structurizr DSL (standalone `.dsl` file or fenced block into Markdown, based on context)
- `reference` — explain or show Structurizr DSL syntax/patterns without writing files
- `check` — validate DSL syntax from a file or snippet, and explain failures without changing it

## Reference Loading

Always start with `references/skill-map.md`.

Then load the matching reference document(s) from `references/`:

- one **primary** reference for the view type or feature
- optional **supplemental** references when the request involves multiple concerns (e.g., deployment view + styles)

If the request needs features not covered by local references, fetch from the [official Structurizr docs](#official-documentation).

## Workflows

### 1. `create` mode

1. Load references, draft valid Structurizr DSL workspace
2. Apply theme — if the user specified a color preference, map it to a theme. Otherwise use "C4 Blue" as default
3. Write output: standalone `.dsl` file, or fenced block into an existing Markdown file if the context indicates it
4. Preview the diagram so the user can see it immediately

### 2. `reference` mode

1. Load references for the view type or feature
2. Answer with concise syntax guidance and a minimal example
3. Do **not** write files unless the user explicitly asks

### 3. `check` mode

1. Read the target file or snippet
2. If embedded in Markdown, extract only the `structurizr` fenced block body into a temp `.dsl` file
3. Validate syntax: `bash ${CLAUDE_SKILL_DIR}/scripts/validate.sh <file.dsl>`
4. Report pass/fail; on failure, explain the cause and show a corrected snippet
5. Do **not** modify files unless the user explicitly asks

## Preview

After writing or editing a `.dsl` file in `create` mode, always render it:

- **Preview**: `bash ${CLAUDE_SKILL_DIR}/scripts/preview.sh <output.dsl>`
- **Export**: `bash ${CLAUDE_SKILL_DIR}/scripts/export.sh <output.dsl> [png|svg|plantuml|mermaid]`

Prerequisites: `brew install structurizr plantuml`

## Official Documentation

When local `references/` files don't cover what you need, fetch from the official Structurizr docs:

| Topic | URL |
|-------|-----|
| DSL Language Reference | https://docs.structurizr.com/dsl/language |
| Cookbook (patterns & recipes) | https://docs.structurizr.com/dsl/cookbook/ |
| Cookbook: specific recipe | https://docs.structurizr.com/dsl/cookbook/{recipe-name}/ |
| Themes | https://docs.structurizr.com/dsl/cookbook/themes/ |
| AWS icons | https://docs.structurizr.com/dsl/cookbook/amazon-web-services/ |
| CLI export | https://docs.structurizr.com/cli/export |

Use `WebFetch` to retrieve the page content when you need syntax details, new cookbook recipes, or features not covered in local references.
