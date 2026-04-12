# dom-analyzer

HTML/XML DOM structure analysis plugin for hierarchy exploration, selector discovery, and selector debugging.

## Components

| Type | Name | Purpose |
|------|------|---------|
| Agent | `html-analyzer` | Analyze DOM structure level by level and recommend selectors |
| Skill | `html-tree` | Internal workflow and usage guidance for DOM analysis |
| Script | `skills/html-tree/scripts/html-tree.py` | CLI for DOM hierarchy visualization |
| Script | `scripts/validate-read-size.sh` | Guardrail for oversized HTML inputs |
| Script | `scripts/restrict-huge-dom.sh` | Helper for limiting very large DOM reads |

## What the CLI Supports

- Full document tree visualization
- Depth-limited exploration with `--max-depth`
- Selector-focused subtree analysis with `--selector`
- Ancestor context with `--show-parents`
- Single-match inspection with `--match-index`
- Optional text node output with `--show-text`
- Compact or full attribute display with `--full` and `--no-attributes`
- Highlighting the selected path with `--highlight-path`
- File output with `--output`

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Python 3 compatible with `uv run`

No install step is required — the CLI declares its dependencies inline and `uv run` resolves them automatically.

## CLI Usage

```bash
uv run plugins/dom-analyzer/skills/html-tree/scripts/html-tree.py <html-file> [options]
```

Common examples:

```bash
uv run plugins/dom-analyzer/skills/html-tree/scripts/html-tree.py page.html --max-depth 3
uv run plugins/dom-analyzer/skills/html-tree/scripts/html-tree.py page.html --selector "article"
uv run plugins/dom-analyzer/skills/html-tree/scripts/html-tree.py page.html --selector ".story" --show-parents 2 --highlight-path
uv run plugins/dom-analyzer/skills/html-tree/scripts/html-tree.py page.html --selector "article" --match-index 1 --show-text
uv run plugins/dom-analyzer/skills/html-tree/scripts/html-tree.py page.html --full --output analysis.txt
```

## Options

| Option | Description |
|--------|-------------|
| `--show-text` | Include text nodes in output |
| `--no-attributes` | Hide all attributes |
| `--full` | Show all attributes |
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

- `plugins/dom-analyzer/agents/html-analyzer.md`
- `plugins/dom-analyzer/skills/html-tree/SKILL.md`
- `plugins/dom-analyzer/skills/html-tree/references/cli-options.md`
- `plugins/dom-analyzer/skills/html-tree/references/workflows.md`
