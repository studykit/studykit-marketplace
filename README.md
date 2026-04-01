# Studykit Plugins

A curated plugin repository that is compatible with both **Claude Code** and **OpenAI Codex**.

## Repository layout

- `plugins/<plugin-name>/`: shared plugin content
- `plugins/<plugin-name>/.claude-plugin/plugin.json`: Claude plugin manifest
- `plugins/<plugin-name>/.codex-plugin/plugin.json`: Codex plugin manifest
- `.claude-plugin/marketplace.json`: Claude marketplace catalog
- `.agents/plugins/marketplace.json`: Codex marketplace catalog
- `global/`: Claude global rules, skills, hooks, and MCP configuration

## Codex compatibility

This repository now includes a repo-scoped Codex marketplace at:

- `.agents/plugins/marketplace.json`

Each Codex plugin follows the structure described in the OpenAI Codex plugin documentation:

- `.codex-plugin/plugin.json` for the plugin manifest
- optional `skills/`, `.mcp.json`, `.app.json`, and `assets/` at the plugin root

Official reference:

- https://developers.openai.com/codex/plugins/build

## Use this repository in Codex

1. Open this repository in Codex.
2. Restart Codex if the marketplace was added while Codex was already running.
3. Open the plugin directory.
4. Select the **Studykit Plugins** marketplace.
5. Install or enable the plugins you want.

Codex reads the repo marketplace from `.agents/plugins/marketplace.json`.

## Use this repository in Claude Code

Claude compatibility is preserved through the existing Claude marketplace files:

- `.claude-plugin/marketplace.json`
- `plugins/<plugin-name>/.claude-plugin/plugin.json`

## Compatibility policy

To avoid breaking Claude compatibility:

- Claude manifests and marketplace files are kept intact.
- Codex support is added in parallel through `.codex-plugin/` manifests and `.agents/plugins/marketplace.json`.
- Shared plugin logic stays under each plugin root whenever possible.

## Available plugins

- `lang`
- `doc`
- `jdk-source`
- `korea-gov-data`
- `dom-analyzer`
- `workflow`
- `obsidian`
- `plantuml`
