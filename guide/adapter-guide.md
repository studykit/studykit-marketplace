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

Do not let shared implementation read host-specific raw inputs directly.

Every plugin entrypoint that depends on host-provided values needs an adapter
boundary. The adapter reads raw inputs for its invocation context, validates
them, and converts them into one of these plugin-owned forms:

- Concrete function arguments.
- A host-neutral data structure.
- A small normalized environment contract for repeated shell calls.
- A generated file that stores normalized values for a later adapter to read.

Host-specific raw inputs include:

- Command text substitutions such as `${CLAUDE_PLUGIN_ROOT}`,
  `${CLAUDE_SKILL_DIR}`, `$ARGUMENTS`, or host-specific placeholders.
- Host environment variables such as `CLAUDE_ENV_FILE`,
  `CLAUDE_CODE_SESSION_ID`, `CODEX_THREAD_ID`, or repository-local hook
  variables such as `PLUGIN_ROOT`.
- Raw hook stdin JSON.
- Runtime-specific payload fields, tool names, matcher names, transcript
  metadata, or agent markers.

Shared logic should receive concrete values or plugin-neutral structures such
as:

- `host`
- `invocation`
- `plugin_root`
- `plugin_data`
- `project_root`
- `cwd`
- `session_id`
- `event_name`
- `tool_name`
- `tool_category`
- `read_target`
- `edit_targets`
- `prompt_text`
- `scan_text`
- `user_config`

Do not pass raw hook payloads into shared logic. Parse raw payloads in the
runtime adapter, extract only the fields the operation needs, then pass those
fields as concrete values. Runtime payload dataclasses or parser-only
structures should stay inside the runtime adapter unless they are explicitly
host-neutral.

A normalized environment contract is allowed when a plugin needs many repeated
shell calls and explicit argv would make every command noisy or fragile. Keep
that contract plugin-owned and host-neutral:

- Use names controlled by the plugin, such as `WORKFLOW`,
  `WORKFLOW_PLUGIN_ROOT`, `WORKFLOW_PROJECT_DIR`, and `WORKFLOW_SESSION_ID`.
- Populate the contract only from an adapter, hook, launcher, or generated
  state file.
- Let command-line entrypoints read the contract as defaults for convenience.
- Pass concrete values from the entrypoint into deeper shared modules.
- Do not use host marker variables as the contract itself.

The workflow plugin is the reference pattern: Claude and Codex hooks read their
own runtime inputs, persist or generate normalized `WORKFLOW_*` values for
later shell use, and workflow scripts consume those normalized values as
defaults before calling shared workflow logic with concrete paths and session
ids. The `scripts/workflow` launcher may also run from a plain terminal; in
that mode it sets local defaults for non-session values but does not synthesize
`WORKFLOW_SESSION_ID`.

When creating another plugin, use this sequence:

1. List the raw inputs for each invocation context: hook, skill, shell, MCP,
   LSP, lifecycle, or manifest template.
2. Choose the adapter entrypoint that owns each raw input.
3. Parse raw payloads into adapter-local structures.
4. Decide whether repeated shell calls need a plugin-owned normalized
   environment contract or whether argv/stdin is enough.
5. Call shared functions with concrete values only.
6. Test adapters with explicit fixtures and environment variables; test shared
   functions without host-specific environment variables.

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
| Assistant shell tool command | The command string authored by the assistant. Plugin placeholders are not expanded just because the assistant uses the shell tool. | The shell environment for the assistant session, cwd, argv, stdin if provided, and files. In Codex, `CODEX_THREAD_ID` is available in the shell tool environment in current observed runtimes, but it is not documented as a plugin or hook contract. | For Studykit workflow scripts launched by the Codex shell tool, use a shell wrapper that reads `CODEX_THREAD_ID`, sources the generated workflow export file, and passes normalized `WORKFLOW_*` values to scripts. Keep that use at the wrapper boundary and do not assume hooks, MCP servers, LSP servers, or non-shell-tool contexts can read it. |
| Claude skill content command | Claude skill substitutions such as `${CLAUDE_SKILL_DIR}`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, and named `$name` arguments. | The child process environment inherited by the command, argv passed by the command, cwd, stdin if provided, and files. Skill substitutions are not guaranteed to appear as environment variables. Claude Code v2.1.132+ sets `CLAUDE_CODE_SESSION_ID` in Bash tool subprocesses, matching the hook `session_id`. | Treat the skill command or Bash-launched script entrypoint as the adapter. Pass needed substitution values explicitly as argv or stdin for portability. Claude-only Bash-launched adapters may read `CLAUDE_CODE_SESSION_ID`, then pass a normalized `session_id` to shared logic. |
| Codex skill instruction | Current Codex skill docs do not define `$ARGUMENTS`, `CODEX_SKILL_DIR`, or `CODEX_PLUGIN_ROOT` skill-body placeholders. | The assistant resolves files and may run commands with explicit paths and argv. Do not assume a Codex skill placeholder exists unless documented. | Resolve paths relative to the active `SKILL.md` or known plugin files, then pass concrete values explicitly. |
| Claude hook command | Hook manifest command text can use `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, command env assignments, and supported hook placeholders. | Hook subprocess environment, hook stdin payload, argv, cwd, and files. Some values such as `CLAUDE_ENV_FILE` exist only in supported hook contexts. | Treat the hook entrypoint as the adapter. Parse stdin once, read env once, then call shared logic with normalized data. |
| Codex hook command | Codex hook manifests support command text, matcher fields, `statusMessage`, and plugin manifest paths to lifecycle config files. Workflow hooks in this repository pass plugin root through the Codex hook process environment as `PLUGIN_ROOT`. | Hook subprocess environment, hook stdin payload, argv, cwd, and files. | Treat `PLUGIN_ROOT` as Codex-adapter input only. Do not let shared workflow logic read it directly. |
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

For Studykit workflow scripts launched through the Codex shell tool, use a
workflow shell wrapper that reads `CODEX_THREAD_ID` as the exact shell session
marker, sources the generated workflow export file, and then invokes scripts
with normalized `WORKFLOW_*` values. This is a repository convention based on
the current Codex shell environment, not a documented Codex plugin or hook
contract. In Codex subagent shells, `CODEX_THREAD_ID` is the subagent's own
thread id; a parent thread id is not exposed as a shell environment variable.
When a subagent needs parent-session workflow state, prepare a generated export
file at hook time from transcript metadata and let the wrapper source it.

Keep this rule narrow:

- Shell-tool-launched Codex wrappers may read `CODEX_THREAD_ID`.
- Codex hooks should read `session_id` from their stdin JSON payload instead.
- Shared logic should receive a normalized `session_id`; it should not read `CODEX_THREAD_ID` directly.
- Do not assume MCP servers, LSP servers, lifecycle commands, or future non-shell-tool contexts can read `CODEX_THREAD_ID` unless their adapter passes it explicitly.

When a plugin needs repeated shell-tool script calls, prefer a small normalized
environment contract over repeated argv. For the workflow plugin, the contract
is:

- `WORKFLOW`
- `WORKFLOW_PLUGIN_ROOT`
- `WORKFLOW_PROJECT_DIR`
- `WORKFLOW_SESSION_ID`

Runtime detection for shell wrappers must use exact session variables, not
prefix checks. Codex shell wrappers may use `CODEX_THREAD_ID`. Claude shell
wrappers may use `CLAUDE_CODE_SESSION_ID`. If both are possible in one wrapper,
define the precedence explicitly or fail closed instead of guessing. Workflow's
launcher and shell-runtime helper check `CLAUDE_CODE_SESSION_ID` first because
Claude sessions already receive the persisted `WORKFLOW_*` contract and should
not source Codex state. Do not infer Claude from unrelated `CLAUDE_CODE_*`
variables.

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
| Hook plugin root | `${CLAUDE_PLUGIN_ROOT}` in Claude hook command text and exported hook subprocess environment | `PLUGIN_ROOT` process environment for Studykit Codex hook adapters |
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

In Codex, Studykit workflow wrappers launched through the shell tool may read `CODEX_THREAD_ID` when session-scoped state is needed. Treat it as a Codex shell-tool convention only; Codex hooks should use stdin `session_id`. In subagents this value identifies the subagent thread; parent-thread workflow state must come from a hook-prepared normalized export file.

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

For Claude-only scripts launched through the Bash tool on Claude Code v2.1.132 or later, the adapter may read `CLAUDE_CODE_SESSION_ID` when session correlation is needed. For Codex workflow shell commands, the wrapper may read `CODEX_THREAD_ID` to source normalized workflow exports. In both cases, pass a normalized `session_id` into shared logic so tests, hooks, and cross-runtime paths do not depend on shell-tool-only environment variables.

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

Hook behavior differs by host. Treat each item below as adapter-owned.

| Surface | Claude | Codex |
| --- | --- | --- |
| Manifest file | `hooks/hooks.json` | Use `hooks/hooks.codex.json` when Codex hook syntax differs; reference it from `.codex-plugin/plugin.json`. |
| Entrypoint | `scripts/hook_claude.py` | `scripts/hook_codex.py` |
| Dispatch | Payload `hook_event_name` | Manifest argv subcommand |
| Plugin root | `CLAUDE_PLUGIN_ROOT` from the Claude hook environment | `PLUGIN_ROOT` from the Codex hook process environment used by this repository's Codex hook manifest or wrapper |
| Project root | `CLAUDE_PROJECT_DIR` from the Claude hook environment | Resolve from payload `cwd` using git root fallback, then `cwd` |
| Hook stdin shape | Claude hook payload schema | Codex hook payload schema |
| File edit tools | `Write`, `Edit`, `MultiEdit` | `Write`, `Edit`, `MultiEdit`, plus Codex `apply_patch` command parsing |
| Subagent start | Workflow does not use Claude `SubagentStart`; operator shells use the `WORKFLOW_*` contract persisted from `SessionStart` | No native `SubagentStart`; Codex prepares the operator export file from `SessionStart` transcript metadata and injects the launcher path when it identifies the operator agent |
| Output | JSON-only stdout for non-empty hook output | JSON-only stdout for non-empty hook output |

Do not copy environment names, matcher names, payload fields, or event behavior between hosts. Add the translation to the runtime adapter instead.

### Hook File Pattern

Use this structure unless a plugin has a documented reason to differ:

- `plugins/<name>/hooks/hooks.json` for Claude hook declarations.
- `plugins/<name>/hooks/hooks.codex.json` for Codex hook declarations when Codex hook syntax differs. This filename is a Studykit convention, not the Codex default. Reference it from `.codex-plugin/plugin.json` via `"hooks": "./hooks/hooks.codex.json"`.
- `plugins/<name>/hooks/README.md` for hook behavior notes when the hook system is non-trivial.
- `plugins/<name>/tests/` fixtures for host-specific hook payloads when hook logic is complex.

### Runtime-Specific Entrypoints

Do not use a shared hook driver that detects the host at runtime. Use one entrypoint per host:

- `scripts/hook_claude.py` owns Claude payload parsing, Claude environment variables, Claude event dispatch, Claude dataclass payload structures, and Claude hook output.
- `scripts/hook_codex.py` owns Codex payload parsing, Codex environment variables, Codex argv dispatch, Codex transcript metadata parsing, Codex `apply_patch` target parsing, and Codex hook output.

The runtime entrypoint may read stdin, argv, environment variables, and runtime-specific payload fields. Shared plugin functions must receive concrete values such as `project_dir`, `plugin_root`, `session_id`, `read_target`, `edit_targets`, `prompt_text`, or `scan_text`.

### Shared Hook Module

Use `scripts/<plugin>_hook.py` for host-neutral hook behavior. For example, the workflow plugin uses `scripts/workflow_hook.py`.

The shared hook module should contain plain functions, not an abstract `Hook` class, runtime factory, driver, or `main` function. It should not read Claude or Codex environment variables, inspect raw hook payloads, branch on host payload schemas, or parse argv/stdin.

Allowed responsibilities for a shared hook module include:

- Building plugin-specific context text from concrete config and paths.
- Applying host-neutral policy or validation after the adapter supplies normalized inputs.
- Reading and writing plugin-owned state after the adapter supplies concrete state keys.
- Loading plugin config from a concrete project directory.
- Returning host-neutral decisions or data for the adapter to emit in host-specific JSON.

Workflow-specific examples include recording authoring reads, blocking unread local projection writes after the adapter supplies `EditTarget` values, injecting issue-cache context after the adapter supplies prompt text, and recording Stop issue references after the adapter supplies scan text.

### Utility Module

Use `scripts/util.py` only for host-neutral helpers that do not know workflow semantics or host payload schemas. Current utility helpers are:

- `as_string(value)` for value-level type narrowing.
- `read_payload_or_stdin(payload)` and `_read_stdin_json()` for explicit payload or stdin JSON loading.
- `scan_text_values(*values)` for bounded text collection from selected values.
- `emit_json(payload, stdout=...)` for JSON-only hook stdout.
- `resolve_file_path(raw_path, base_dir=...)` for path resolution after the adapter selected the base directory.
- `is_markdown_path(path)`, `is_under(path, root)`, and `is_under_any(path, roots)` for generic path checks.

Do not put payload key extraction such as `tool_input.file_path`, `source`, `prompt`, `last_assistant_message`, or agent markers in `util.py`. Those belong in the runtime adapter.

### Claude Hook Adapter Contract

Claude hook commands should invoke `scripts/hook_claude.py` through `uv run --script` with no event subcommand. The adapter dispatches using the payload `hook_event_name`.

Rules:

- Read `CLAUDE_PLUGIN_ROOT` for the plugin root.
- Read `CLAUDE_PROJECT_DIR` for the project directory. Do not resolve the Claude project from payload `cwd`.
- Represent Claude payloads with dataclasses that mirror documented payload fields exactly, including documented optional fields.
- Do not store adapter-derived values, normalized targets, or raw payload copies on Claude payload dataclasses. Compute derived values in the adapter handler before calling shared workflow logic.
- Handler functions should receive parsed dataclass payloads, not raw `Mapping` objects.
- `SessionStart` source handling is Claude-specific; `compact` is skipped and `clear` may reinject policy.
- Claude operator subagents rely on the `WORKFLOW_*` shell contract persisted by `SessionStart`; do not inject a separate operator context unless a future runtime breaks that contract.

### Codex Hook Adapter Contract

Codex hook commands should invoke `scripts/hook_codex.py` through `uv run --script` with no event subcommand. The adapter dispatches using the payload `hook_event_name`.

Rules:

- Read `PLUGIN_ROOT` for the plugin root from the Codex hook process environment used by this repository.
- Resolve the project from payload `cwd` using git root fallback.
- Keep Codex-only agent detection in `hook_codex.py`; do not move generic agent marker heuristics into shared workflow code.
- Keep transcript metadata parsing in `hook_codex.py`. For workflow operator subagents, `CODEX_THREAD_ID` is the subagent thread id, so the adapter must extract the parent thread id from transcript metadata before writing the subagent export file.
- Keep Codex `apply_patch` target parsing in `hook_codex.py`.
- Codex operator subagent environment is prepared from the Codex `SessionStart` path when transcript metadata identifies `workflow-operator`. The hook should inject only the absolute workflow launcher path as bootstrap context; the operator instructions should not need plugin-root, env-file, or parent-thread implementation details.

Hook entrypoints and workflow launcher-invoked Python scripts should use inline
script dependencies when shared modules require third-party libraries. The
workflow plugin uses this for `python-frontmatter` and `PyYAML`; host hook
processes should not depend on globally installed Python packages.

### Hook Output

Runtime adapters must emit JSON only when stdout is non-empty. Empty stdout means no-op success.

Allowed non-empty JSON output includes:

- `{"decision": "block", "reason": "..."}` for supported blocking hooks.
- `{"hookSpecificOutput": {"hookEventName": "...", "additionalContext": "..."}}` for context injection.

Do not emit plain text from hook scripts. Keep status text in manifest fields such as Codex `statusMessage` when the host supports them.

### Hook State

Separate state by lifetime:

- Persistent plugin data belongs in the host's plugin data directory when the host provides one.
- Project-local validation state belongs under a documented project-local directory.
- Session-scoped state should include the session id and, when useful, the host name.

Use collision-resistant state file names so one host does not delete or reinterpret another host's active session state:

```text
<plugin>-<host>-<event>-<session-id>.json
```

Avoid using a Claude-named path for new host-neutral state. If a plugin already uses a path such as `.claude/tmp/` for historical reasons, keep path handling behind a helper.

### Testing Hook Adapters

Tests should not rely on the developer's current shell environment.

Use fixtures and explicit inputs:

- Provide hook stdin payload fixtures for each supported host.
- Set required environment variables in the test harness.
- Pass argv explicitly for Codex dispatch tests.
- Parse Claude payloads through `parse_claude_event_payload()` before calling Claude handlers.
- Assert non-empty hook stdout parses as a JSON object.
- Include tests for missing optional fields and missing required fields.


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

For Claude hooks that need to persist shell environment changes, use `CLAUDE_ENV_FILE` only in hook events that provide it. Write `export` statements to that file so variables are available to later Bash commands in the same Claude Code session. As of the current Claude Code hooks documentation, `CLAUDE_ENV_FILE` is available for `SessionStart`, `Setup`, `CwdChanged`, and `FileChanged` hooks.

Claude command hooks are a documented exception to the general safety rule that command text substitutions are not automatically process environment variables: Claude exports `CLAUDE_PROJECT_DIR`, `CLAUDE_PLUGIN_ROOT`, and `CLAUDE_PLUGIN_DATA` to command hook subprocesses. Keep shared logic portable by still normalizing those values at the adapter boundary.

For workflow shell commands, Claude hooks may persist the normalized
`WORKFLOW_*` contract by appending `export` statements to `CLAUDE_ENV_FILE`.
The Claude workflow launcher should consume that persisted contract; it should
not synthesize `WORKFLOW_SESSION_ID` from `CLAUDE_CODE_SESSION_ID`.

## Codex-Specific Inputs

Codex plugin contexts have different documented surfaces.

Rules for this repository:

- Studykit Codex hook adapters read `PLUGIN_ROOT` from the hook process environment. Keep that read in `hook_codex.py`; shared hook modules must receive a concrete `plugin_root`.
- Do not copy Claude names such as `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, or `CLAUDE_PROJECT_DIR` into Codex hook logic.
- Codex hooks receive a JSON object on stdin with `session_id`; use that as the official hook session/thread identifier.
- Current Codex skill docs do not define `$ARGUMENTS`, `CODEX_SKILL_DIR`, or `CODEX_PLUGIN_ROOT` skill-body placeholders. Do not design shared skill scripts around those names.
- Studykit shell wrappers launched through the Codex shell tool may read `CODEX_THREAD_ID` at the wrapper boundary for session-scoped state. This is an observed shell-tool convention, not a documented Codex plugin or hook contract. Use it to locate a generated export file, source the normalized `WORKFLOW_*` contract, and then call shared scripts.
- In Codex subagents, `CODEX_THREAD_ID` identifies the subagent thread, not the parent thread. If guarded workflow state belongs to the parent thread, extract that id from hook transcript metadata and write it into the generated `WORKFLOW_SESSION_ID` export.
- If a Codex hook or lifecycle command needs plugin data paths, pass a concrete value through a wrapper, generated hook config, argv, stdin, or a documented manifest mechanism.

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
- Hook scripts use runtime-specific entrypoints unless there is a documented reason to share a driver.
- Hook stdin is parsed in one runtime adapter before shared workflow functions are called.
- Hook scripts do not assume skill-only placeholders.
- Skill-launched scripts do not assume hook-only payloads or variables.
- Shell-tool-only variables are read only by shell script adapters and are passed to shared logic as normalized values.
- Tests use explicit fixtures and environment variables instead of ambient shell state.
