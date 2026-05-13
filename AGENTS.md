# Studykit Plugin Marketplace

This is the plugin marketplace directory - a collection of Claude Code and Codex plugins for various use cases.

## Version Management

Claude plugin versions live in each plugin's `plugins/<name>/.claude-plugin/plugin.json` (top-level `version` field, SemVer). Plugin entries in `.claude-plugin/marketplace.json` MUST NOT set `version` — if `version` is set in both places, `plugin.json` wins silently and a stale marketplace value would be masked.

Codex plugin manifests at `plugins/<name>/.codex-plugin/plugin.json` carry their own top-level `version` field. When a plugin supports both runtimes, bump the Claude and Codex `version` strings together and keep them identical.

When a new plugin is added or new features are added to an existing plugin, update the relevant marketplace files accordingly — `.claude-plugin/marketplace.json` for Claude and `.agents/plugins/marketplace.json` for Codex (registration only, not version).

## Claude and Codex Compatibility

Plugins should be designed and maintained to run in both Claude Code and Codex whenever possible. Avoid hardcoding agent-specific assumptions unless the feature is explicitly agent-specific. Keep shared behavior, scripts, documentation, and metadata portable across both environments, and clearly isolate any Claude-only or Codex-only implementation details.

Start with `guide/AGENTS.md` when adding or changing plugin manifests, hooks, skills, agents, commands, runtime scripts, or marketplace metadata. Use `guide/cross-runtime-guide.md` for cross-runtime architecture and marketplace/version policy, and `guide/adapter-guide.md` for adapter, hook, skill, and script runtime compatibility.

When developing or changing skills, hooks, plugins, or agents, always check the current official Claude Code and Codex documentation before relying on runtime behavior, manifest schemas, metadata fields, placeholders, environment variables, hook payloads, tool names, or marketplace behavior. Do not rely on memory or repository examples alone when an official behavior may have changed.

## Global Directory

The `global/` directory manages rules, subagents, skills, hooks, and MCP configurations intended for installation to `~/.claude/`. These are user-level components that apply globally across all projects, not specific to any single plugin.

## Language Requirements

**All documentation must be written in English.** When creating or editing markdown files, README files, CLAUDE.md files, or any other documentation, always use English.

## Agent Instruction Files

When creating an `AGENTS.md` instruction file, always create a sibling `CLAUDE.md` file that imports it with exactly `@AGENTS.md`. Keep shared instructions in `AGENTS.md`; use `CLAUDE.md` only as the Claude Code import shim unless a location explicitly requires Claude-only instructions.

## Path References in Documentation

Inside markdown documentation (CLAUDE.md, README.md, `plugins/a4/authoring/*.md`, `plugins/a4/dev/*.md`, etc.), reference plugin-internal files using **backticked relative paths** (`` `./file.md` ``, `` `../dir/file.md` ``, `` `plugins/a4/authoring/foo.md` ``) rather than markdown links (`[text](path)`). Reserve markdown link form for examples that demonstrate cross-reference syntax used inside `<project-root>/a4/` workspace files.
