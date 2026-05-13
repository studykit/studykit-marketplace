# Cross-Runtime Plugin Guide

This guide owns cross-host plugin architecture for this repository. It explains how to structure plugins so they can run in both Claude Code and Codex whenever practical, with host-specific behavior isolated behind adapter boundaries.

For guide routing and terminology, read `guide/AGENTS.md`.

## Scope

This document covers:

- Cross-host design goals.
- Adapter-boundary policy.
- Repository layout expectations.
- Manifest and marketplace alignment.
- Shared implementation boundaries.
- General documentation and review expectations.

This document does not define detailed adapter mechanics, hook payload handling, skill metadata, or runtime input surfaces. Use `guide/adapter-guide.md` for hook adapters, skill portability, script invocation contracts, and Claude/Codex runtime variables.

## When to Read This

Read this document when you are:

- Creating a plugin that should support both Claude Code and Codex.
- Porting a Claude-only or Codex-only plugin to the other host.
- Deciding whether a feature belongs in shared code or an adapter.
- Updating plugin manifests, marketplace registration, or version policy.
- Reviewing a plugin change for host-neutral behavior.

## Compatibility Goal

Prefer one shared implementation with thin host-specific adapters.

A plugin may be Claude-only or Codex-only when:

- The other host does not support the required capability.
- The plugin depends on a host-specific API or tool.
- Porting would add more complexity than value.
- The feature is intentionally host-specific.

When a feature cannot be portable, document the limitation in the plugin README or next to the host-specific file.

## Adapter Boundary Rule

Only the adapter layer should know host-specific differences.

The adapter layer may:

- Resolve host placeholders and environment variables.
- Read host-specific manifest fields.
- Parse raw host hook payloads.
- Map host tool names into shared categories.
- Convert shared decisions into host-specific output formats.
- Pass concrete paths, arguments, and normalized payloads to shared scripts.

The shared implementation should consume explicit values, not host runtime details. If a shared script, shared skill body, or shared business rule needs a raw Claude or Codex variable, move that logic to an adapter first.

## Script Adapter Rule

All scripts should read host-provided values through an adapter layer.

The adapter can be a thin command wrapper, the top of a script entrypoint, or a host-specific module. Its job is to:

- Read host-specific environment variables, placeholders, command arguments, stdin, or manifest values.
- Validate required values for the current host and context.
- Convert those values into concrete arguments or a normalized data structure.
- Call shared script logic with that normalized contract.

Shared script logic should not directly read Claude or Codex variables. This rule applies to scripts launched from hooks, skills, agents, MCP commands, LSP commands, and plugin lifecycle commands.

Hook-invoked scripts, skill-invoked scripts, and assistant shell tool commands have different runtime contexts. For example, a hook script may receive hook stdin and hook-specific environment variables, a skill-launched script may only receive values that the skill command passed explicitly, and a shell tool command may expose assistant-session variables that plugin runtimes do not receive. Document the expected context at each script entrypoint.

## Architecture Pattern

Use this layering pattern:

1. Shared behavior in `plugins/<name>/scripts/`, `plugins/<name>/skills/`, shared templates, or shared documentation.
2. Host adapter code that translates host-specific inputs into shared inputs.
3. Claude integration in `plugins/<name>/.claude-plugin/`, Claude hook manifests, or Claude-specific wrappers.
4. Codex integration in `plugins/<name>/.codex-plugin/`, Codex hook manifests, or Codex-specific wrappers.
5. Marketplace registration in the host-specific marketplace file.

Host-specific files should translate host inputs into shared inputs. They should not contain durable business logic.

## Repository Layout

Use these paths consistently:

- `plugins/<name>/` contains the plugin implementation.
- `plugins/<name>/.claude-plugin/plugin.json` contains Claude plugin metadata.
- `plugins/<name>/.codex-plugin/plugin.json` contains Codex plugin metadata when the plugin supports Codex.
- `plugins/<name>/hooks/hooks.json` contains Claude hook declarations when hooks are needed.
- `plugins/<name>/hooks/hooks.codex.json` contains Codex hook declarations when Codex hook syntax differs.
- `plugins/<name>/skills/` contains reusable skills.
- `plugins/<name>/agents/` contains reusable agent definitions when supported.
- `plugins/<name>/scripts/` contains shared runtime code.
- `.claude-plugin/marketplace.json` registers Claude marketplace entries.
- `.agents/plugins/marketplace.json` registers Codex marketplace entries.

## Manifest and Marketplace Rules

Keep host manifests aligned where both hosts are supported:

- Use the same plugin `name` in Claude and Codex manifests.
- Keep descriptions semantically equivalent, even when schemas differ.
- Keep author, repository, license, category, and keywords consistent where the schemas support them.
- Claude plugin versions live in `plugins/<name>/.claude-plugin/plugin.json` as a top-level `version` field using SemVer.
- Do not set `version` on the matching entry in `.claude-plugin/marketplace.json`; if both are set, `plugin.json` wins silently and a stale marketplace value would be masked.
- Codex plugin manifests at `plugins/<name>/.codex-plugin/plugin.json` carry their own top-level `version` field.
- When a plugin supports both hosts, bump the Claude and Codex `version` strings together and keep them identical.
- Update `.claude-plugin/marketplace.json` for Claude registration changes such as entries, source, and metadata, not for version.
- Update `.agents/plugins/marketplace.json` for Codex registration changes.

Before adding a plugin, decide whether it should be available to Claude, Codex, or both.

## Shared Code Rules

Shared scripts and libraries should not assume one host.

Use these practices:

- Accept host name, plugin root, project root, data path, and session identifiers through explicit inputs or a small adapter.
- Keep host-specific environment variables at the adapter boundary.
- Treat script entrypoints as adapters unless they are explicitly shared logic; adapter entrypoints may read environment variables, but shared logic should not.
- Resolve paths with platform-neutral APIs such as `pathlib`.
- Keep writes inside the active project, plugin data directory, or documented temporary directories.
- Keep dependencies minimal and documented.
- Prefer deterministic command-line entrypoints for scripts used by manifests or hooks.
- Avoid interactive terminal behavior unless the plugin explicitly requires it and every supported host can handle it.

When behavior differs by host, keep the conditional branch near the boundary. Do not scatter host checks through business logic.

## Skills, Agents, and Prompts

For detailed skill adapter rules, read `guide/adapter-guide.md`.

Author reusable instructions in host-neutral language when possible:

- Prefer "assistant", "agent", or "host" when an instruction applies to both hosts.
- Use "Claude Code" or "Codex" only for host-specific behavior.
- Keep file paths relative and backticked.
- Avoid mentioning tools that are unavailable in one supported host.
- Declare host-specific tool dependencies in the skill or agent description.
- Keep examples portable unless the example is intentionally host-specific.

Read `guide/adapter-guide.md` when writing runtime-specific command examples, skill-launched scripts, or adapter contracts.

## Hooks

Hooks are host-sensitive. This guide only sets the architectural boundary:

- Keep hook manifests thin.
- Put durable hook behavior in shared scripts.
- Use hook adapters to normalize host input and output.
- Keep Claude and Codex hook differences isolated.

For detailed hook adapter rules, read `guide/adapter-guide.md`. It owns hook command placeholders, environment variables, stdin normalization, output formatting, and state rules.

## Documentation Rules

All documentation in this repository must be written in English.

Use documentation to make compatibility obvious:

- Plugin READMEs should state supported hosts.
- Host-specific files should explain why they exist when the reason is not obvious.
- Shared scripts should include concise comments at adapter boundaries.
- Avoid copying long host documentation into plugin files.
- Use backticked relative paths for repository files, not markdown links, unless demonstrating cross-reference syntax.

## Expected Change Flow

For most plugin changes:

1. Decide which hosts the change affects.
2. Design or update the shared behavior first.
3. Define the normalized adapter contract needed by the shared behavior.
4. Update Claude-specific files only where Claude integration changes.
5. Update Codex-specific files only where Codex integration changes.
6. Update marketplace files when registration, availability, or versioning changes.
7. Run relevant validation or tests for each affected host.
8. Note any untested host in the final change summary.

## Review Checklist

Before finishing a cross-host plugin change, check:

- Supported hosts are clear.
- Claude and Codex manifests remain aligned where both are supported.
- Marketplace files reflect the intended availability and versioning.
- Shared behavior is not duplicated in host-specific files.
- Host-specific variables, payloads, and tool names are kept at adapter boundaries.
- Shared scripts receive explicit paths, arguments, and normalized payloads.
- Hook, skill, script, and runtime input changes follow `guide/adapter-guide.md`.
- Documentation uses host-neutral wording where possible.
- Host-specific limitations are documented.
- Tests or manual checks cover each affected host.
