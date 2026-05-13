# Adapter Guide

This guide owns adapter-layer rules for Studykit plugins. It explains what inputs are visible in each runtime context and how to convert host-specific inputs into a shared contract for scripts, skills, hooks, MCP commands, LSP commands, and lifecycle commands.

Use `guide/cross-runtime-guide.md` for cross-runtime architecture, manifests, marketplace rules, and shared-code boundaries.

## Scope

This document covers:

- Command text input versus process input.
- Assistant shell tool input surfaces.
- Skill-launched script input surfaces.
- Hook script input surfaces.
- Skill compatibility across Claude Code and Codex.
- Hook compatibility across Claude Code and Codex.
- Claude-specific placeholders and subprocess variables.
- Codex-specific hook command limitations and current skill-placeholder assumptions.
- Script adapter rules for passing normalized values to shared logic.

This document does not define shared business logic or plugin marketplace/version policy.

## When to Read This

Read this document when you are:

- Creating or updating a `SKILL.md` file.
- Adding `agents/openai.yaml` metadata for Codex-facing skills.
- Writing a script launched by a skill, hook, MCP command, LSP command, or lifecycle command.
- Writing or changing hook manifests.
- Deciding whether a value should be read from environment variables, stdin, argv, files, or template substitution.
- Moving behavior from a host-specific command into shared script logic.
- Debugging why a value is visible in one runtime context but missing in another.
- Writing tests or fixtures for hook or skill script adapters.

## Core Rule

Do not let shared script logic read host-specific inputs directly.

Every script that depends on host-provided values needs an adapter boundary. The adapter reads raw inputs once, validates them, and passes concrete values or a normalized structure into shared logic.

Shared logic should receive values such as:

- `host`
- `invocation`
- `plugin_root`
- `plugin_data`
- `project_root`
- `cwd`
- `session_id`
- `argv`
- `hook_payload`
- `tool_name`
- `tool_category`
- `user_config`

Shared logic should not directly read `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_SKILL_DIR}`, `${PLUGIN_ROOT}`, `$ARGUMENTS`, `CLAUDE_CODE_SESSION_ID`, `CODEX_THREAD_ID`, `CLAUDE_ENV_FILE`, raw hook stdin, or shell-tool-only variables.

## Command Text Input vs Process Input

Keep these two categories separate:

- `command text input` means values that a host can substitute while building a command string or instruction body.
- `process input` means values that the launched process can read directly through environment variables, stdin, argv, cwd, or files.

A template substitution is not automatically an environment variable. For example, a host may expand `${CLAUDE_SKILL_DIR}` while constructing a command, but the launched script should not assume that `CLAUDE_SKILL_DIR` exists in `os.environ`.

The safest pattern is:

1. Use command text substitution only to construct the command or explicit argv.
2. Pass every required value as argv, stdin, or a small normalized environment contract.
3. Let the adapter parse those values.
4. Call shared logic with concrete values.

## Runtime Input Surface Matrix

| Runtime context | Command text input | Process input visible to the launched command | Adapter rule |
| --- | --- | --- | --- |
| Assistant shell tool command | The command string authored by the assistant. Plugin placeholders are not expanded just because the assistant uses the shell tool. | The shell environment for the assistant session, cwd, argv, stdin if provided, and files. In Codex, `CODEX_THREAD_ID` is available in the shell tool environment in current observed runtimes, but it is not documented as a plugin or hook contract. | For Studykit scripts launched by the Codex shell tool, the adapter may read `CODEX_THREAD_ID` as the session id for session-scoped state. Keep that use at the adapter boundary and do not assume hooks, MCP servers, LSP servers, or non-shell-tool contexts can read it. |
| Claude skill content command | Claude skill substitutions such as `${CLAUDE_SKILL_DIR}`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, and named `$name` arguments. | The child process environment inherited by the command, argv passed by the command, cwd, stdin if provided, and files. Skill substitutions are not guaranteed to appear as environment variables. Claude Code v2.1.132+ sets `CLAUDE_CODE_SESSION_ID` in Bash tool subprocesses, matching the hook `session_id`. | Treat the skill command or Bash-launched script entrypoint as the adapter. Pass needed substitution values explicitly as argv or stdin for portability. Claude-only Bash-launched adapters may read `CLAUDE_CODE_SESSION_ID`, then pass a normalized `session_id` to shared logic. |
| Codex skill instruction | Current Codex skill docs do not define `$ARGUMENTS`, `CODEX_SKILL_DIR`, or `CODEX_PLUGIN_ROOT` skill-body placeholders. | The assistant resolves files and may run commands with explicit paths and argv. Do not assume a Codex skill placeholder exists unless documented. | Resolve paths relative to the active `SKILL.md` or known plugin files, then pass concrete values explicitly. |
| Claude hook command | Hook manifest command text can use `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, command env assignments, and supported hook placeholders. | Hook subprocess environment, hook stdin payload, argv, cwd, and files. Some values such as `CLAUDE_ENV_FILE` exist only in supported hook contexts. | Treat the hook entrypoint as the adapter. Parse stdin once, read env once, then call shared logic with normalized data. |
| Codex hook command | Codex hook manifests support command text, matcher fields, `statusMessage`, and plugin manifest paths to lifecycle config files. Current official Codex docs do not document a plugin-root or plugin-data placeholder inside individual hook commands. | Hook subprocess environment, hook stdin payload, argv, cwd, and files. | Do not rely on undocumented hook command placeholders. Use a Codex-specific wrapper or generated concrete path when a hook needs bundled files, then normalize to `plugin_root`, `plugin_data`, and host-neutral fields. |
| MCP, LSP, or lifecycle command | Host-specific manifest command text and supported plugin placeholders. | Subprocess environment, argv, cwd, stdin when the protocol provides it, and files. Claude may export `CLAUDE_PLUGIN_OPTION_<KEY>` for plugin user configuration in supported subprocess contexts. | Read host-specific configuration at the adapter boundary and pass validated values to shared logic. |
| Plugin manifest or templated content | Manifest schema fields, user configuration placeholders, and host-specific template substitution. | Nothing reaches a child process unless the manifest command passes or exports it. | Do not expect manifest substitutions to appear in scripts automatically. |

## Assistant Shell Tool Context

The assistant shell tool is for development, validation, and repository maintenance. It is not a plugin runtime.

The shell tool can see:

- Environment variables exported into the assistant command session.
- The current working directory selected for the command.
- Files available in the workspace and allowed sandbox roots.
- Stdin only when the command invocation provides it.
- Command-line arguments in the command string.

The shell tool cannot assume:

- Claude skill substitutions such as `${CLAUDE_SKILL_DIR}`.
- Codex skill placeholders unless they are explicitly documented and expanded by that runtime.
- Hook stdin payloads.
- Plugin hook environment variables.

For Studykit scripts launched through the Codex shell tool, use `CODEX_THREAD_ID` as the shell-tool session id when session-scoped state is needed. This is a repository convention based on the current Codex shell environment, not a documented Codex plugin or hook contract.

Keep this rule narrow:

- Shell-tool-launched Codex script adapters may read `CODEX_THREAD_ID`.
- Codex hooks should read `session_id` from their stdin JSON payload instead.
- Shared logic should receive a normalized `session_id`; it should not read `CODEX_THREAD_ID` directly.
- Do not assume MCP servers, LSP servers, lifecycle commands, or future non-shell-tool contexts can read `CODEX_THREAD_ID` unless their adapter passes it explicitly.

## Skill Adapter Rules

### Shared Skill Format

Both runtimes use a skill directory with a `SKILL.md` file.

Expected shared layout:

```text
plugins/<name>/skills/<skill-name>/
├── SKILL.md
├── references/
├── scripts/
├── assets/
└── agents/openai.yaml
```

Rules:

- `SKILL.md` is required.
- `references/`, `scripts/`, and `assets/` are optional and loaded only when needed.
- `agents/openai.yaml` is required by this repository for Codex-facing skills, even though OpenAI documents it as optional metadata.
- Use `plugins/<name>/scripts/` only for scripts shared by multiple skills, hooks, or agents.

### Shared `SKILL.md` Metadata

Every skill must have at least:

```md
---
name: skill-name
description: Explain exactly when this skill should and should not trigger.
---
```

Rules:

- `name` should match the skill directory name.
- `name` should be lowercase kebab-case.
- `description` must be concise and trigger-focused.
- Front-load important trigger words because Codex may shorten long descriptions in the initial skill list.
- Put runtime limitations in the body or `compatibility` metadata only when they matter.

### OpenAI Metadata

Every Codex-facing skill in this repository must include:

```text
plugins/<name>/skills/<skill-name>/agents/openai.yaml
```

Use it for OpenAI/Codex-specific skill metadata, especially:

```yaml
interface:
  display_name: "User-facing skill name"
  short_description: "Short install-surface description"
  icon_small: "./assets/icon-small.svg"
  icon_large: "./assets/icon-large.png"
  brand_color: "#10A37F"
  default_prompt: "Optional example prompt"

policy:
  allow_implicit_invocation: true

dependencies:
  tools:
    - type: "mcp"
      value: "serverName"
      description: "Why this tool is needed"
```

Rules:

- Keep `agents/openai.yaml` Codex-specific. Do not put essential workflow steps only there.
- Keep shared workflow instructions in `SKILL.md` and `references/`.
- Use `policy.allow_implicit_invocation: false` for skills that should run only when explicitly named.
- Declare MCP, app, or other Codex-visible tool dependencies here when the skill needs them.
- Use relative asset paths from the skill root, starting with `./`.

### Skill Runtime Difference Matrix

| Area | Claude Code | Codex |
| --- | --- | --- |
| Shared skill file | `SKILL.md` | `SKILL.md` |
| Skill metadata | `name`, `description` in frontmatter | `name`, `description` in frontmatter |
| OpenAI metadata | Not used by Claude-specific mechanics | Official optional `agents/openai.yaml` metadata for UI metadata, invocation policy, and dependencies; required by this repository for Codex-facing skills |
| Plugin skill registration | Claude plugin manifest mechanics | `.codex-plugin/plugin.json` should point `skills` to `./skills/` |
| Repo-local skill discovery | Claude-specific locations and plugin install behavior | Codex scans `.agents/skills` from cwd up to repo root; plugins can also bundle skills |
| Skill arguments | `$ARGUMENTS`, `$ARGUMENTS[N]` with `$N` shorthand such as `$0` and `$1`, and named `$name` arguments are Claude skill-content substitutions | No documented Codex equivalent in current OpenAI skill docs; treat the user prompt as input and pass explicit values to scripts |
| Skill directory placeholder | `${CLAUDE_SKILL_DIR}` in Claude skill content | No documented `CODEX_SKILL_DIR` placeholder; resolve paths relative to the loaded skill file when needed |
| Plugin root placeholder in skill content | No documented `${CLAUDE_PLUGIN_ROOT}` skill-content substitution; use `${CLAUDE_SKILL_DIR}` for skill-local files | No documented `CODEX_PLUGIN_ROOT` skill placeholder; Codex plugin manifests use `./`-prefixed paths relative to plugin root |
| Persistent plugin data | No documented `${CLAUDE_PLUGIN_DATA}` skill-content substitution; use documented plugin subprocess contexts or pass an explicit data path | Do not assume a skill-body placeholder; keep skill state project-local or pass a documented data path explicitly |
| Hook plugin root | `${CLAUDE_PLUGIN_ROOT}` in Claude hook command text and exported hook subprocess environment | No documented Codex hook-command plugin-root placeholder at this revision; use a Codex-specific wrapper or generated concrete path |
| Hook plugin data | `${CLAUDE_PLUGIN_DATA}` in Claude hook command text and exported hook subprocess environment | No documented Codex hook-command plugin-data placeholder at this revision; keep hook data handling behind a hook adapter |
| Tool names | Claude-specific tool names may appear in Claude-only instructions | Codex tool names may differ; avoid tool-name coupling in shared skills |

### Skill-Launched Scripts

A skill-launched script can see only process input available to that launched command.

Common process inputs are:

- `argv` passed by the skill command or by the assistant when running a command from skill instructions.
- Environment variables inherited by the command process.
- `cwd` selected for the command.
- Files available at the provided paths.
- Stdin only when explicitly provided.

In Claude Code v2.1.132 and later, scripts launched through the Bash tool also receive `CLAUDE_CODE_SESSION_ID` in the subprocess environment. That value matches the `session_id` passed to Claude hooks. Treat it as a Claude-specific process input for a script adapter, not as a SKILL.md string substitution and not as a Codex contract.

In Codex, Studykit scripts launched through the shell tool may read `CODEX_THREAD_ID` in the script adapter when session-scoped state is needed. Treat it as a Codex shell-tool convention only; Codex hooks should use stdin `session_id`.

A skill-launched script should not assume it can read:

- Skill command substitutions as environment variables.
- Hook payloads.
- Hook-only environment variables.
- Assistant shell diagnostic variables.

Use this pattern for Claude-specific command snippets:

```md
!`${CLAUDE_SKILL_DIR}/scripts/run.sh ${CLAUDE_SESSION_ID} "$ARGUMENTS"`
```

Then read `session_id` and `arguments` from positional arguments inside the script adapter.

For Claude-only scripts launched through the Bash tool on Claude Code v2.1.132 or later, the adapter may read `CLAUDE_CODE_SESSION_ID` when session correlation is needed. For Codex shell-tool scripts, the adapter may read `CODEX_THREAD_ID`. In both cases, pass a normalized `session_id` into shared logic so tests, hooks, and cross-runtime paths do not depend on shell-tool-only environment variables.

Use this pattern for Codex-compatible instructions:

```md
Resolve `scripts/run.py` relative to this `SKILL.md`, then run it with explicit arguments for every required path or value.
```

### Portable Skill Paths

Prefer runtime-neutral references in shared skill instructions:

```md
Read `references/options.md` when the user asks for advanced options.
Run `scripts/validate.py` with the target file path.
```

Avoid shared skill instructions like:

```md
Run `${CLAUDE_PLUGIN_ROOT}/skills/example/scripts/validate.py`.
```

That path is not a documented skill-content placeholder. Use `${CLAUDE_SKILL_DIR}` for Claude-only skill-local commands, or resolve and pass explicit paths through an adapter.

### Skill Tool Dependencies

Shared skills should avoid runtime-specific tool names unless a step is runtime-specific.

Use this pattern:

```md
Read the target file.
Run the validation script.
Search the repository for matching declarations.
```

Avoid this in shared instructions unless the tool name is runtime-specific on purpose:

```md
Use Read, Bash, WebFetch, or apply_patch.
```

For Codex, declare structured tool dependencies in `agents/openai.yaml` when applicable. For Claude, document required tools or plugin configuration in Claude-specific docs or manifest fields.

## Hook Adapter Rules

### Hook Compatibility Surfaces

Hook behavior differs along these axes. Treat each as a place where compatibility work may be needed.

| Surface | Claude | Codex |
| --- | --- | --- |
| Manifest file | `hooks/hooks.json` | Default bundled path is `hooks/hooks.json`; Studykit may use `hooks/hooks.codex.json` when Codex hook syntax differs |
| Plugin root in commands | `${CLAUDE_PLUGIN_ROOT}` | No documented hook-command placeholder at this revision; use a generated concrete path or wrapper |
| Plugin data in commands | `${CLAUDE_PLUGIN_DATA}` | No documented hook-command placeholder at this revision; pass an explicit data path through the adapter |
| File edit tool names | `Write`, `Edit` | Canonical hook tool name is `apply_patch`; matchers may also use `Edit` or `Write` aliases |
| Hook stdin shape | Claude payload schema | Codex payload schema |
| Output channels | Stdout, stderr, and JSON decisions per Claude rules | Stdout, stderr, and JSON decisions per Codex rules |

Do not rely on Claude-named aliases such as `${CLAUDE_PLUGIN_ROOT}` or generic names such as `${PLUGIN_ROOT}` in Codex hook commands unless Codex documentation explicitly supports them in the target runtime.

### Hook File Pattern

Use this structure unless a plugin has a documented reason to differ:

- `plugins/<name>/hooks/hooks.json` for Claude hook declarations.
- `plugins/<name>/hooks/hooks.codex.json` for Codex hook declarations when Codex hook syntax differs. This filename is a Studykit convention, not the Codex default. Reference it from `.codex-plugin/plugin.json` via `"hooks": "./hooks/hooks.codex.json"`.
- `plugins/<name>/hooks/README.md` for hook behavior notes when the hook system is non-trivial.
- `plugins/<name>/scripts/<plugin>_hook.py` or an equivalent shared entrypoint.
- `plugins/<name>/tests/` fixtures for host-specific hook payloads when hook logic is complex.

### When to Split Hook Manifests

Create separate hook manifests when any of these differ between hosts:

- Supported event names.
- Tool matcher names.
- Hook command environment variables.
- Hook stdin payload shape.
- Expected hook output format.
- Manifest-only fields.
- Timeout or UX requirements.

Do not create separate manifests only to copy the same command with cosmetic wording changes. Prefer one shared script with host-specific command wrappers.

### Hook Host Marker

Every shared hook script should know which host invoked it. Set an explicit host marker in the hook command.

Claude:

```json
{
  "type": "command",
  "command": "uv",
  "args": ["run", "${CLAUDE_PLUGIN_ROOT}/scripts/example_hook.py", "post-edit", "--host", "claude"],
  "timeout": 10
}
```

Codex:

```json
{
  "type": "command",
  "command": "uv run \"/absolute/path/to/plugin/scripts/example_hook.py\" post-edit --host codex",
  "timeout": 10,
  "statusMessage": "Processing plugin hook"
}
```

Use a clear host marker and document the accepted values. In the Codex example, replace the absolute plugin path through packaging, generation, or a wrapper; do not treat `/absolute/path/to/plugin` as a Codex placeholder.

### Hook Script Context

A hook script can see hook process input, not skill body input or assistant shell assumptions.

Common hook inputs are:

- Hook stdin payload.
- Environment variables set by the host.
- Environment variables assigned in the hook manifest command.
- Manifest command substitutions documented for that host, such as Claude plugin root or plugin data paths, or explicit values generated by repository packaging.
- `argv` passed by the hook manifest command.
- `cwd` and files available to the hook subprocess.

A hook script should not assume it can read:

- `${CLAUDE_SKILL_DIR}` or `$ARGUMENTS`.
- Shell-tool-only variables such as `CODEX_THREAD_ID`.
- Plugin manifest placeholders that were not passed into the hook command.
- Values from another host unless the hook command or adapter normalizes them.

### Hook Stdin Normalization

Parse host-specific hook stdin exactly once. The adapter should tolerate missing fields and produce a host-neutral structure.

This example is the post-normalization shape produced by the adapter, not raw host stdin:

```json
{
  "host": "codex",
  "invocation": "hook",
  "event": "post-edit",
  "cwd": "/path/to/project",
  "project_root": "/path/to/project",
  "plugin_root": "/path/to/plugin",
  "plugin_data": "/path/to/plugin-data",
  "session_id": "session-or-fallback",
  "tool_name": "apply_patch",
  "tool_category": "patch_apply",
  "tool_input": {},
  "tool_result": {},
  "prompt": null
}
```

Rules:

- Treat unknown fields as optional.
- Keep raw payloads available for diagnostics, but do not let business logic depend on raw host schemas.
- Prefer the hook payload `cwd` when available.
- Derive `project_root` from the git root when available, then fall back to `cwd`.
- Never fail only because an optional host field is absent.
- Fail clearly when a required field for a specific action is missing.

### Hook Events and Matchers

Model behavior by lifecycle intent instead of event name:

| Lifecycle intent | Typical use |
| --- | --- |
| Session start | Clean stale state, load lightweight context, initialize session records. |
| Before tool use | Snapshot state needed to compare pre-change and post-change behavior. |
| After tool use | Record changed files, run reconciliation, emit guidance. |
| Stop or finalization | Validate session changes; block or request continuation only when recovery is actionable. |
| User prompt submit | Resolve references and inject additional context when supported. |
| Session end | Clean session-scoped files when the host supports it. |

Declare only events the target host supports. If one host lacks an equivalent event, ensure the shared script handles missing state safely.

Keep matcher choices in the manifest. Convert host-specific tool names into shared categories such as:

- `file_write`
- `file_edit`
- `patch_apply`
- `prompt`
- `unknown`

Shared business logic should consume the category and normalized payload, not raw matcher strings.

### Hook Output

Different hosts interpret stdout, stderr, JSON decisions, status messages, and injected context differently. Keep output formatting at the adapter boundary:

- Use stdout for user-visible guidance only when the host expects it.
- Use stderr for diagnostics only when the host surfaces it appropriately.
- Emit block decisions only in the exact JSON shape expected by the target host.
- Keep status text in manifest fields when the host supports them.
- Keep injected context concise and deterministic.

Blocking responses must include enough context for the user or host to recover: what failed, which rule was triggered, and how to fix it.

### Hook State

Separate state by lifetime:

- Persistent plugin data belongs in the host's plugin data directory.
- Project-local validation state belongs under a documented project-local directory.
- Session-scoped state should include the session id and, when useful, the host name.

Use collision-resistant state file names so one host does not delete or reinterpret another host's active session state:

```text
<plugin>-<host>-<event>-<session-id>.json
```

Avoid using a Claude-named path for new host-neutral state. If a plugin already uses a path such as `.claude/tmp/` for historical reasons, keep path handling behind a helper.

## Claude-Specific Inputs

Claude template substitutions and subprocess variables are context-sensitive.

| Input | Context | Adapter use |
| --- | --- | --- |
| `${CLAUDE_SESSION_ID}` | Skill content substitution | Pass as argv when scripts need session correlation. |
| `${CLAUDE_SKILL_DIR}` | Skill content substitution | Use to construct a skill-local command path; pass derived paths explicitly. |
| `${CLAUDE_PLUGIN_ROOT}` | Claude hook command text and exported hook subprocess environment; other documented plugin subprocess/config contexts such as MCP, LSP, and monitors | Use in command text to locate bundled files; normalize to `plugin_root`. |
| `${CLAUDE_PLUGIN_DATA}` | Claude hook command text and exported hook subprocess environment; other documented plugin subprocess/config contexts such as MCP, LSP, and monitors | Use in command text for persistent plugin data; normalize to `plugin_data`. |
| `$ARGUMENTS` | Skill content substitution | Pass as argv or stdin when scripts need user-provided skill arguments. |
| `$ARGUMENTS[N]` or shorthand `$N` such as `$0`, `$1`, `$2` | Skill content substitution | Pass as argv when scripts need indexed arguments. |
| `${user_config.KEY}` | Plugin configuration and supported templated content | Use only where Claude performs substitution; pass to scripts explicitly if needed. |
| `CLAUDE_PLUGIN_OPTION_<KEY>` | Plugin subprocesses that receive user config, including hooks, MCP, LSP, and monitors | Read in a Claude subprocess adapter, validate, then pass normalized config to shared logic. |
| `CLAUDE_ENV_FILE` | Supported Claude hook contexts | Use only in hook contexts that support session-level shell exports. |
| `CLAUDE_CODE_SESSION_ID` | Bash tool subprocess environment in Claude Code v2.1.132 and later | Read only at a Claude Bash-launched script adapter boundary when session correlation is needed. |

Do not copy a Claude variable pattern from one context into another without checking that context.

Claude command hooks are a documented exception to the general safety rule that command text substitutions are not automatically process environment variables: Claude exports `CLAUDE_PROJECT_DIR`, `CLAUDE_PLUGIN_ROOT`, and `CLAUDE_PLUGIN_DATA` to command hook subprocesses. Keep shared logic portable by still normalizing those values at the adapter boundary.

## Codex-Specific Inputs

Codex plugin contexts have different documented surfaces.

Rules for this repository:

- Current Codex hook docs do not document `${PLUGIN_ROOT}`, `${PLUGIN_DATA}`, `${CLAUDE_PLUGIN_ROOT}`, or `${CLAUDE_PLUGIN_DATA}` as hook-command placeholders. Do not rely on those names in Codex hook commands.
- Codex hooks receive a JSON object on stdin with `session_id`; use that as the official hook session/thread identifier.
- Current Codex skill docs do not define `$ARGUMENTS`, `CODEX_SKILL_DIR`, or `CODEX_PLUGIN_ROOT` skill-body placeholders. Do not design shared skill scripts around those names.
- Studykit scripts launched through the Codex shell tool may read `CODEX_THREAD_ID` at the script adapter boundary for session-scoped state. This is an observed shell-tool convention, not a documented Codex plugin or hook contract.
- If a Codex hook or lifecycle command needs plugin root or data paths, pass a concrete value through a wrapper, generated hook config, argv, stdin, or a documented manifest mechanism.

## Passing Values to Scripts

Prefer explicit and testable input contracts:

1. Use argv for short scalar values such as host, event, mode, session id, or target file.
2. Use stdin for structured payloads such as hook payloads or larger JSON contracts.
3. Use environment variables only at the adapter boundary and only for values that are naturally environment-level, such as host markers or plugin command configuration.
4. Use files for large fixtures, caches, or persistent state paths.
5. Normalize host-specific names before calling shared logic.

Document each script entrypoint with:

- Invocation context: `shell`, `skill`, `hook`, `mcp`, `lsp`, or `lifecycle`.
- Required argv.
- Required environment variables.
- Expected stdin shape.
- Output contract.
- Whether the script is shared or host-specific.

## State and Data Paths

Rules:

- Do not write mutable state under the plugin installation directory.
- Claude persistent plugin data should use `${CLAUDE_PLUGIN_DATA}` only from a Claude adapter context that supports it, then pass the resulting path explicitly to script logic.
- Codex-compatible skills should use project-local state or an explicit data path passed to scripts.
- Session-scoped files should include a session id when the runtime provides one.
- If a Codex skill path is not launched through the shell tool, or `CODEX_THREAD_ID` is unavailable, use a project-local deterministic path and document cleanup behavior.

## Testing Adapters

Tests should not rely on the developer's current shell environment.

Use fixtures and explicit inputs:

- Provide hook stdin payload fixtures for each supported host.
- Set required environment variables in the test command or test harness.
- Pass argv explicitly.
- Assert the normalized contract passed to shared logic.
- Include tests for missing optional fields and missing required fields.

## Anti-Patterns

Avoid these mistakes:

- Reading host-specific environment variables from deep shared logic.
- Treating command text substitutions as process environment variables.
- Using shell-tool-only variables such as `CODEX_THREAD_ID` from shared logic, hooks, MCP servers, LSP servers, or lifecycle commands.
- Assuming hook payloads exist in skill-launched scripts.
- Assuming skill placeholders exist in hook scripts.
- Copying Claude variable names into Codex shared logic.
- Copying Codex hook variable names into shared skill prose.
- Business logic copied into both `hooks.json` and `hooks.codex.json`.
- Testing adapters with the ambient shell environment instead of explicit fixtures.

## Review Checklist

Before finishing an adapter-related change, verify:

- The invocation context is documented.
- Command text input and process input are separated.
- Required argv, environment variables, stdin, and output are documented.
- Host-specific values are read only at the adapter boundary.
- Shared logic receives concrete values or a normalized structure.
- `SKILL.md` has valid `name` and `description` frontmatter when a skill changes.
- Codex-facing skills have `agents/openai.yaml`.
- Shared skill instructions avoid Claude-only placeholders unless clearly marked Claude-specific.
- Hook manifests exist for every supported host that needs the hook.
- Hook scripts receive an explicit host marker when shared.
- Hook stdin is normalized in one adapter.
- Hook scripts do not assume skill-only placeholders.
- Skill-launched scripts do not assume hook-only payloads or variables.
- Shell-tool-only variables are read only by shell script adapters and are passed to shared logic as normalized values.
- Tests use explicit fixtures and environment variables instead of ambient shell state.
