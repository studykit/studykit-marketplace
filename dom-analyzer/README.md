# dom-analyzer

HTML DOM structure analysis plugin for hierarchy exploration, selector discovery, and selector debugging.

## Components

| Type | Name | Purpose |
|------|------|---------|
| Agent | `html-analyzer` | Analyze DOM structure level by level and recommend selectors |
| Skill | `html-tree` | Internal workflow and usage guidance for DOM analysis |
| Script | `skills/html-tree/scripts/html-tree.ts` | CLI for DOM hierarchy visualization |

## What The CLI Supports

- Full document tree visualization
- Depth-limited exploration with `--max-depth`
- Selector-focused subtree analysis with `--selector`
- Ancestor context with `--show-parents`
- Single-match inspection with `--match-index`
- Optional text node output with `--show-text`
- Compact or full attribute display with `--compact`, `--full`, `--no-attributes`
- File output with `--output`

## Prerequisites

- [Deno](https://deno.com/) runtime

No install step required — dependencies are declared inline via Deno's `npm:` specifiers.

## CLI Usage

```bash
deno run --allow-read dom-analyzer/skills/html-tree/scripts/html-tree.ts <html-file> [options]
```

Common examples:

```bash
deno run --allow-read html-tree.ts page.html --max-depth 3
deno run --allow-read html-tree.ts page.html --selector "article"
deno run --allow-read html-tree.ts page.html --selector ".story" --show-parents 2 --highlight-path
deno run --allow-read html-tree.ts page.html --selector "article" --match-index 1 --show-text
deno run --allow-read html-tree.ts page.html --full --output analysis.txt
```

## Options

| Option | Description |
|--------|-------------|
| `--show-text` | Include text nodes in output |
| `--no-attributes` | Hide all attributes |
| `--full` | Show all attributes except suppressed SVG/path attributes |
| `--compact` | Compact attribute mode; default behavior |
| `--max-depth <n>` | Limit traversal depth |
| `--output <file>` | Write output to file |
| `--selector <css>` | Visualize only nodes matching a CSS selector |
| `--show-parents <n>` | Show ancestor context above matched nodes |
| `--highlight-path` | Mark the selected node section in selector mode |
| `--match-index <n>` | Show only the nth selector match, 1-based |
| `--help` | Print help text |

## Agent Usage

Use the plugin when the task is about:

- Analyzing an HTML file's structure
- Exploring a page level by level instead of dumping the full DOM
- Finding stable CSS selectors for scraping or extraction
- Debugging why a selector does not match

Example prompts:

```text
Analyze the DOM structure of this HTML file
Find the CSS selector for the article content
Why isn't this selector matching anything?
Show me the hierarchy around the main content area
```

## Related Files

- [`dom-analyzer/agents/html-analyzer.md`](/Volumes/NVME/GitHub/studykit-plugins/dom-analyzer/agents/html-analyzer.md)
- [`dom-analyzer/skills/html-tree/SKILL.md`](/Volumes/NVME/GitHub/studykit-plugins/dom-analyzer/skills/html-tree/SKILL.md)
- [`dom-analyzer/skills/html-tree/references/cli-options.md`](/Volumes/NVME/GitHub/studykit-plugins/dom-analyzer/skills/html-tree/references/cli-options.md)
- [`dom-analyzer/skills/html-tree/references/workflows.md`](/Volumes/NVME/GitHub/studykit-plugins/dom-analyzer/skills/html-tree/references/workflows.md)
