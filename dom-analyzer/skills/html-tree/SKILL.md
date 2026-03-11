---
name: html-tree
description: DOM hierarchy visualization and CSS selector discovery using the html-tree CLI tool. Covers analysis workflows for structure exploration, selector debugging, and cross-page comparison.
disable-model-invocation: true
user-invocable: false
---

# HTML DOM Analysis

## DOM Hierarchy Visualizer Tool

The plugin bundles a TypeScript CLI tool at `${CLAUDE_PLUGIN_ROOT}/scripts/html-tree.ts` for parsing and visualizing HTML DOM trees.

### Prerequisites

- Node.js with `ts-node` or `tsx` available
- `jsdom` package installed

Install dependencies if needed:
```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts && npm install
```

### Core Commands

**Full structure overview:**
```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts && npx ts-node --esm html-tree.ts <html-file> --max-depth 5
```

**Filter by CSS selector:**
```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts && npx ts-node --esm html-tree.ts <html-file> --selector "article"
```

**Show parent context for selector matches:**
```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts && npx ts-node --esm html-tree.ts <html-file> --selector ".content" --show-parents 3
```

**Show specific match from multiple results:**
```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts && npx ts-node --esm html-tree.ts <html-file> --selector "div.story" --match-index 1
```

**Include text content in output:**
```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts && npx ts-node --esm html-tree.ts <html-file> --show-text --max-depth 4
```

**Save output to file:**
```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts && npx ts-node --esm html-tree.ts <html-file> --output analysis.md
```

### Key CLI Options

| Option | Description |
|--------|-------------|
| `--max-depth <n>` | Limit traversal depth |
| `--selector <css>` | Filter to elements matching CSS selector |
| `--show-parents <n>` | Show n ancestor levels above matched nodes |
| `--match-index <n>` | Show only the nth match (1-based) |
| `--show-text` | Include text node content |
| `--full` | Show all attributes (not just id, class, data-*) |
| `--highlight-path` | Mark the path to selected nodes |

For the complete option reference with output samples, consult **`references/cli-options.md`**.

## Analysis Workflows

### Workflow 1: Full Structure Discovery

Use when the overall page layout is unknown.

1. Run with `--max-depth 3` to get a high-level overview
2. Identify major structural containers (header, main, footer, article)
3. Increase depth on interesting sections using `--selector`
4. Note semantic elements and class naming patterns

### Workflow 2: Content Selector Discovery

Use when building a scraper/converter and need to find the right selectors.

1. Start with broad semantic selectors: `article`, `main`, `section`
2. If no match, try common class patterns: `.content`, `.story`, `.post`, `.entry`
3. Use `--show-parents 3` to understand context around matches
4. Use `--match-index` to examine individual matches when multiple found
5. Use `--show-text` to verify the matched elements contain expected content

### Workflow 3: Debugging Selectors

Use when a CSS selector is not matching expected elements.

1. Start from a broader selector that does match
2. Progressively narrow with child selectors
3. Use `--full` to see all attributes, not just id/class/data-*
4. Check for dynamic class names or attributes that vary across pages
5. Use `--highlight-path` to trace from root to the target element

### Workflow 4: Cross-Page Validation

Use when verifying selectors work across different page variants.

1. Collect multiple HTML samples of the same site/type
2. Run the same selector against each sample
3. Compare match counts and paths
4. Identify stable vs. variable structural patterns
5. Choose selectors based on the most stable elements

## DOM Analysis Without the Tool

When the visualizer tool is not available or for quick analysis, use the Read tool to examine HTML files directly:

1. Read the HTML file
2. Identify structural patterns from the raw markup
3. Look for semantic HTML5 elements (article, section, nav, header, footer, main, aside)
4. Note id and class attributes for selector candidates
5. Check for data-* attributes that indicate component boundaries

## Additional Resources

### Reference Files

- **`references/cli-options.md`** - Complete CLI option reference with output samples and advanced usage patterns
