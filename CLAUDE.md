# Claude Plugin Marketplace

This is the plugin marketplace directory - a collection of Claude Code plugins for various use cases.

## Version Management

Plugin versions are managed exclusively in `.claude-plugin/marketplace.json`. Individual `plugin.json` files must NOT contain a `version` field.

When a new plugin is added or new features are added to an existing plugin, update `.claude-plugin/marketplace.json` accordingly — add the new plugin entry or bump the version of the updated plugin.

## Global Directory

The `global/` directory manages rules, subagents, skills, hooks, and MCP configurations intended for installation to `~/.claude/`. These are user-level components that apply globally across all projects, not specific to any single plugin.

## Language Requirements

**All documentation must be written in English.** When creating or editing markdown files, README files, CLAUDE.md files, or any other documentation, always use English.

## a4 plugin frontmatter schema

When modifying anything under `plugins/a4/` or anything that reads/writes `<project-root>/a4/` workspace files, always read the relevant a4 frontmatter contracts first:

- [`plugins/a4/references/frontmatter-universals.md`](plugins/a4/references/frontmatter-universals.md) — universal rules (`type:` field, ids, path-reference format, dates, status writers, structural relationship fields).
- [`plugins/a4/references/<type>-authoring.md`](plugins/a4/references/) — per-type field table and lifecycle for the `type:` you are editing.
- [`plugins/a4/references/validator-rules.md`](plugins/a4/references/validator-rules.md) — schema enforcement and cross-file status consistency.

Together they are the single source of truth for the a4 frontmatter contract — required fields, enum values, path-reference format, status writers, auto-maintained reverse links, and validator behavior. Do not edit a4 frontmatter, write new a4 skills/scripts, or change validators without consulting them.

