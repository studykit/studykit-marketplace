# dom-analyzer

HTML/XML DOM structure analysis toolkit with hierarchy visualization.

## Features

- **DOM hierarchy visualization** - Tree-based view of HTML/XML document structure
- **CSS selector discovery** - Find reliable selectors for content extraction
- **Selector debugging** - Troubleshoot selectors that don't match
- **Cross-page comparison** - Validate selectors across page variants

## Components

| Type | Name | Purpose |
|------|------|---------|
| Agent | `dom-analyzer` | Autonomous DOM analysis agent |
| Skill | `html-dom-analysis` | Internal knowledge base for the agent |
| Script | `html-tree.ts` | CLI tool for DOM tree visualization |

## Prerequisites

- Node.js
- `jsdom` package: `npm install jsdom` (in plugin scripts directory)
- `ts-node` or `tsx` for TypeScript execution

## Usage

The agent triggers automatically when you ask about HTML/XML structure analysis:

```
"Analyze the DOM structure of this HTML file"
"Find the CSS selector for the article content"
"What's the hierarchy of elements in page.html?"
"Why isn't my selector matching anything?"
```

## Installation

```bash
claude --plugin-dir /path/to/dom-analyzer
```
