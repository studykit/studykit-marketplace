---
name: html-tree
allowed-tools: ["Bash(deno run*)"]
description: >
  This skill should be used when analyzing HTML DOM structure, visualizing element hierarchies,
  exploring page layout level by level, discovering CSS selectors for scraping, debugging
  why a selector does not match, showing the HTML tree of a file, parsing HTML to inspect
  elements, or examining page structure. Provides the html-tree CLI tool for tree visualization
  with depth control, selector filtering, and parent context display.
---

# HTML DOM Structure Analysis

## Tool Setup

The plugin bundles a self-contained TypeScript CLI tool at `${CLAUDE_PLUGIN_ROOT}/skills/html-tree/scripts/html-tree.ts`. Dependencies are declared inline via Deno's `npm:` specifiers — no install step required.

**Prerequisites:** Deno runtime.

**Base command** (all examples below abbreviate this as `...`):
```bash
deno run --allow-read ${CLAUDE_PLUGIN_ROOT}/skills/html-tree/scripts/html-tree.ts <html-file> [options]
```

## CLI Options Quick Reference

| Option | Description |
|--------|-------------|
| `--max-depth <n>` | Limit traversal depth |
| `--selector <css>` | Filter to elements matching CSS selector |
| `--show-parents <n>` | Show n ancestor levels above matched nodes |
| `--match-index <n>` | Show only the nth match (1-based) |
| `--show-text` | Include text node content |
| `--full` | Show all attributes (not just id, class, data-*) |
| `--no-attributes` | Hide all attributes, show only tag names |
| `--highlight-path` | Mark the path to selected nodes |
| `--output <file>` | Write output to file |

For complete option details with output samples, read **`${CLAUDE_PLUGIN_ROOT}/skills/html-tree/references/cli-options.md`**.

## Core Methodology: Level-by-Level Exploration

Analyze HTML structure by progressively increasing depth. Start shallow, identify landmarks, then drill into specific subtrees. This prevents information overload and builds understanding incrementally.

### Step 1: Top-Level Overview (depth 2)

Get the broadest view of the page structure.

```bash
... html-tree.ts page.html --max-depth 2
```

At this level you see major containers: `<html>`, `<head>`, `<body>`, and their direct children. Identify which top-level elements exist (header, nav, main, aside, footer, etc.).

### Step 2: Identify Structural Landmarks (depth 3-4)

Increase depth to reveal the layout within each major section.

```bash
... html-tree.ts page.html --max-depth 4
```

Look for:
- Semantic HTML5 elements: `<article>`, `<section>`, `<nav>`, `<header>`, `<footer>`, `<main>`, `<aside>`
- Wrapper divs with meaningful class names (`.container`, `.content`, `.wrapper`)
- Repeating patterns that indicate lists or grids

### Step 3: Drill Into a Specific Subtree

Use `--selector` to focus on a section of interest discovered in previous steps.

```bash
... html-tree.ts page.html --selector "main"
```

This shows the full subtree under the matched element. Combine with `--max-depth` to control how deep you go within that subtree:

```bash
... html-tree.ts page.html --selector "main" --max-depth 3
```

### Step 4: Examine Context Around Elements

When you find a target element, use `--show-parents` to understand its position in the hierarchy.

```bash
... html-tree.ts page.html --selector ".story-content" --show-parents 3
```

This reveals the ancestor chain, helping you build reliable CSS selectors that include structural context.

### Step 5: Inspect Content

Use `--show-text` to verify that matched elements contain the expected content.

```bash
... html-tree.ts page.html --selector "article" --show-text --max-depth 3
```

For multiple matches, examine individual ones with `--match-index`:

```bash
... html-tree.ts page.html --selector "article" --match-index 1 --show-text
```

### Step 6: Refine Selectors

Use `--full` to reveal all attributes (href, src, role, aria-*, data-*) when building precise selectors.

```bash
... html-tree.ts page.html --selector "article" --full --highlight-path
```

## Additional Workflows

For selector debugging, cross-page comparison, and other specialized workflows, see **`${CLAUDE_PLUGIN_ROOT}/skills/html-tree/references/workflows.md`**.
