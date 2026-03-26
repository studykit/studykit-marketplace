# Claude Plugin Marketplace

This is the plugin marketplace directory - a collection of Claude Code plugins for various use cases.

## Version Management

Plugin versions are managed exclusively in `.claude-plugin/marketplace.json`. Individual `plugin.json` files must NOT contain a `version` field.

When a new plugin is added or new features are added to an existing plugin, update `.claude-plugin/marketplace.json` accordingly — add the new plugin entry or bump the version of the updated plugin.

## Global Directory

The `global/` directory manages rules, subagents, skills, hooks, and MCP configurations intended for installation to `~/.claude/`. These are user-level components that apply globally across all projects, not specific to any single plugin.

## Language Requirements

**All documentation must be written in English.** When creating or editing markdown files, README files, CLAUDE.md files, or any other documentation, always use English.

