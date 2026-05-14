# Plugin Authoring Guide Map

This directory contains repository-level guidance for creating and maintaining Studykit plugins.

Start here when a plugin change touches manifests, hooks, skills, agents, runtime scripts, or marketplace metadata. Use this file as the routing map; follow the smallest guide set that covers the change.

## Terminology

Use these terms consistently across guide documents:

- `host` means the application that invokes plugin behavior, such as Claude Code or Codex.
- `shared implementation` means durable behavior, instructions, scripts, templates, or tests that should not depend on one host.
- `adapter layer` means the host-specific boundary that translates host raw inputs, placeholders, paths, environment variables, tool names, and output formats into concrete values or plugin-owned normalized contracts.
- `script adapter` means the script entrypoint or wrapper that reads host-specific runtime values or plugin-owned normalized environment contracts and passes concrete arguments or host-neutral values into shared script logic.
- `hook adapter` means the adapter layer for hook payloads and hook output.
- `shared hook module` means a host-neutral hook logic module such as `plugins/<name>/scripts/<plugin>_hook.py`. It contains plain functions and receives concrete values from adapters; it does not parse stdin, argv, host environment variables, or raw host payloads.
- `utility module` means a host-neutral helper module such as `plugins/<name>/scripts/util.py`. It contains generic helpers that do not know plugin business rules, host payload schemas, or host environment variables.
- `shell tool context` means the assistant's command-execution environment, such as a shell command run during development or validation. It is not a plugin hook, skill, MCP, or LSP runtime.
- `command text input` means values available while constructing a command string, such as template substitutions. These are not automatically process environment variables.
- `process input` means values a launched script can read directly, such as environment variables, stdin, argv, cwd, and files.

When shared behavior supports both Claude Code and Codex, implement an adapter layer. The adapter layer should identify the invoking host, resolve host-specific variables, normalize inputs into plugin-owned values, map tool names, and emit output in the invoking host's expected shape.

## Document Ownership

| Document | Owns | Does not own |
| --- | --- | --- |
| `guide/cross-runtime-guide.md` | Cross-runtime architecture, repository layout, manifest alignment, shared-code boundaries, marketplace rules, and review flow. | Detailed adapter input surfaces, hook payload mechanics, skill metadata, or script invocation contracts. |
| `guide/adapter-guide.md` | Adapter input surfaces, command text vs process input, shell tool context, skill compatibility, hook compatibility, script invocation contracts, Claude/Codex runtime variables, normalization, state, and adapter tests. | Marketplace/version policy or high-level plugin availability decisions. |

## Task Routes

Use these routes before reading whole documents:

- Adding a dual-runtime plugin: read `guide/cross-runtime-guide.md`, then `guide/adapter-guide.md` for skills, hooks, scripts, or runtime inputs.
- Adding or changing a shared skill: read `guide/adapter-guide.md`.
- Adding or changing a shared hook: read `guide/adapter-guide.md`.
- Refactoring an existing hook for both Claude and Codex: read `guide/cross-runtime-guide.md` for the file split, then `guide/adapter-guide.md` for runtime entrypoints, payload parsing, JSON output, shared hook module boundaries, and utility-module boundaries.
- Adding or changing shared runtime scripts: read `guide/adapter-guide.md`; keep host-specific inputs at adapter boundaries.
- Updating Claude-only or Codex-only integration: read `guide/adapter-guide.md`, then keep limitations documented near the host-specific file.
- Updating marketplace registration or plugin versions: read `guide/cross-runtime-guide.md`.

## Reading Order

Use the smallest document set that matches the change:

1. For plugin availability, repository layout, manifests, marketplace files, or version policy, read `guide/cross-runtime-guide.md`.
2. For skills, hooks, scripts, agents, MCP/LSP commands, lifecycle commands, shell tool context, runtime variables, or adapter tests, read `guide/adapter-guide.md`.

If a change crosses both boundaries, read them in that order.

## Adapter Boundary Rule

Only the adapter layer should know host-specific details.

- Shared instructions and scripts should not branch on Claude or Codex unless no adapter boundary is available.
- Host-specific manifests, command wrappers, hook adapters, and runtime-specific examples may reference host variables and placeholders.
- All scripts should access host-provided values through an adapter layer. The script adapter may read command text substitutions, environment variables, stdin, argv, manifest values, or plugin-owned normalized environment contracts; shared script logic should receive concrete paths, arguments, host names, and host-neutral values.
- Hook-invoked scripts, skill-invoked scripts, and assistant shell tool commands do not have the same runtime context. Do not copy variable assumptions from one context into another.
- Cross-runtime hooks should normally use runtime-specific entrypoints (`hook_claude.py`, `hook_codex.py`) that call a shared hook module with concrete values.
- If shared code needs `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_SKILL_DIR}`, `${PLUGIN_ROOT}`, `CODEX_THREAD_ID`, `CLAUDE_CODE_SESSION_ID`, a raw hook payload, or a host-specific tool name, move that concern into an adapter first.
- Plugin-owned normalized environment contracts, such as workflow's `WORKFLOW_*` values, may be read by script entrypoints as defaults, but deeper shared logic should still receive concrete values.

## Layering Rule

Keep guidance layered:

- Cross-runtime policy belongs in `guide/cross-runtime-guide.md`.
- Adapter mechanics, skill portability, hook compatibility, and runtime input surfaces belong in `guide/adapter-guide.md`.

Do not duplicate detailed rules between documents. A higher-level document should point to the lower-level document instead of restating it.

## Change Checklist

Before completing a plugin change, confirm the relevant owner documents were followed:

- Shared behavior is host-neutral or has an explicit adapter boundary.
- Skill, hook, script, MCP/LSP, and lifecycle command changes follow `guide/adapter-guide.md`.
- Marketplace and version changes follow `guide/cross-runtime-guide.md`.
