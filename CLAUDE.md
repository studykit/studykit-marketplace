# Claude Plugin Marketplace

This is the plugin marketplace directory - a collection of Claude Code plugins for various use cases.

## Version Management

Plugin versions are managed exclusively in `.claude-plugin/marketplace.json`. Individual `plugin.json` files must NOT contain a `version` field.

When a new plugin is added or new features are added to an existing plugin, update `.claude-plugin/marketplace.json` accordingly — add the new plugin entry or bump the version of the updated plugin.

## Global Directory

The `global/` directory manages rules, subagents, skills, hooks, and MCP configurations intended for installation to `~/.claude/`. These are user-level components that apply globally across all projects, not specific to any single plugin.

## Language Requirements

**All documentation must be written in English.** When creating or editing markdown files, README files, CLAUDE.md files, or any other documentation, always use English.

## Path References in Documentation

Inside markdown documentation (CLAUDE.md, README.md, `plugins/a4/authoring/*.md`, `plugins/a4/dev/*.md`, etc.), reference plugin-internal files using **backticked relative paths** (`` `./file.md` ``, `` `../dir/file.md` ``, `` `plugins/a4/authoring/foo.md` ``) rather than markdown links (`[text](path)`). Reserve markdown link form for examples that demonstrate cross-reference syntax used inside `<project-root>/a4/` workspace files.

## a4 plugin — audience routing

The a4 plugin separates docs by audience. Pick by your task:

- **Editing files inside `<project-root>/a4/**/*.md` (workspace authoring), or authoring / running an a4 skill at runtime** — read `plugins/a4/authoring/*.md`. These are the binding contracts for workspace files (frontmatter, body conventions, per-type lifecycles). a4 skills are independent — each skill describes its own preconditions, inputs, outputs, and behavior in its own `SKILL.md` + `references/`; there is no shared orchestration layer to consult. In particular, when touching frontmatter, consult:
  - `plugins/a4/authoring/frontmatter-common.md` — cross-cutting rules (`type:` field, path-reference format, empty collections, unknown fields, `created` / `updated`).
  - `plugins/a4/authoring/frontmatter-wiki.md` — wiki minimal contract.
  - `plugins/a4/authoring/frontmatter-issue.md` — issue-side rules (`id`, title placeholders, relationships, status changes and cascades, structural relationship fields).
  - `plugins/a4/authoring/<type>-authoring.md` — per-type field table and lifecycle for the `type:` you are editing.
- **Modifying anything inside `plugins/a4/` itself (plugin contributor work)** — additionally read `plugins/a4/dev/*.md` (hook conventions, cascade implementation, shared procedure design memos like `iterate-mechanics.md`) and `plugins/a4/CLAUDE.md` (contributor notes).

Two sources of truth, two audiences: `authoring/` is the single source of truth for the a4 workspace contract (frontmatter, body conventions, per-type lifecycles); `dev/` is the single source of truth for plugin internals. Skills cite `authoring/` but never `dev/` at runtime. Do not edit a4 frontmatter, write new a4 skills/scripts, or change validators without consulting `authoring/`. Do not change hook flow or cascade behavior without consulting `dev/`. Validator output (Stop hook, `/a4:validate`) is self-explanatory — each violation message names the file, field, rule, and recovery path; cross-reference `frontmatter-common.md` / `frontmatter-wiki.md` / `frontmatter-issue.md` and the relevant `<type>-authoring.md` for the binding shape.

