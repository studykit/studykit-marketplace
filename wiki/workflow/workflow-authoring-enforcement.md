# Workflow Authoring Enforcement

## Purpose

Workflow authoring enforcement ensures that agents read the correct plugin-bundled authoring contracts before creating or editing workflow artifacts.

The rule is:

```text
required_authoring_files ⊆ read_authoring_files
```

## Authoring Contract Source

Runtime authoring contracts live under [`plugins/workflow/authoring/`](../../plugins/workflow/authoring/).

This wiki page describes the enforcement model and links to the contract directory when needed. It should not duplicate the full contract bodies from `authoring/`.

## Components

### Authoring Resolver

Script: `plugins/workflow/scripts/authoring_resolver.py`

The resolver decides which authoring files are required for a workflow artifact. It uses artifact type, role, provider, and `.workflow/config.yml` when available.

Every resolution includes:

1. `metadata-contract.md`
2. `body-conventions.md`
3. `issue-authoring.md` for issue-backed artifacts, or `knowledge-body.md` for knowledge-backed artifacts
4. `<type>-authoring.md`
5. Provider-wide authoring file when available
6. Provider type-specific authoring file when available
7. Provider guardrail files, such as anti-pattern files, when available

The resolver returns absolute paths so the agent does not guess relative locations.

### SessionStart Policy

Script: `plugins/workflow/scripts/workflow_hook.py`

SessionStart injects a concise workflow authoring policy only when the active project has `.workflow/config.yml`.

The injected policy includes:

- The resolved config file path.
- The issue provider and knowledge provider.
- A reminder to delegate workflow provider, cache, write-back, comment append, and authoring guard operations to `plugins/workflow/agents/workflow-operator.md`.
- A role boundary that the workflow operator returns provider/cache metadata and paths only; issue and wiki content interpretation stays in the main assistant.
- No output for spawned agent sessions.

SessionStart does not inject workflow script command recipes into the main assistant context.

### Hook Read Recording And Local Projection Guard

Script: `plugins/workflow/scripts/workflow_hook.py`

Workflow hooks also connect the read ledger and write guard:

- `post-read` records reads of plugin-bundled authoring files by absolute path.
- `pre-write` checks local projection writes before mutation.
- Missing reads block the write and list absolute authoring file paths to read.
- Non-workflow projects receive no workflow hook output.

The write guard is transport-neutral. Future provider wrappers should call the same guard before GitHub, Jira, Confluence, repository `wiki/`, or MCP writes.

### Authoring Read Ledger

Script: `plugins/workflow/scripts/authoring_ledger.py`

The ledger records which absolute authoring file paths were read in the current session. It is session-scoped and project-scoped.

By default, ledger state is stored outside the repository under the operating-system temp directory.

### Authoring Write Guard

Script: `plugins/workflow/scripts/authoring_guard.py`

The guard combines resolver output with the ledger. Provider wrappers and hooks can call it before local projection writes or remote provider writes.

Exit codes:

- `0`: all required authoring files have been read.
- `3`: one or more required authoring files are missing.
- `2`: resolver or ledger error.

## Intended Flow

1. SessionStart injects the policy only when `.workflow/config.yml` exists.
2. Before a write, the caller resolves required authoring files.
3. The agent reads every required authoring file.
4. The runtime or wrapper records those reads in the ledger.
5. The write guard checks the ledger before mutation.
6. Provider writes proceed only when every required file was read.

## Scope

This enforcement applies to:

- Issue-backed artifacts.
- Knowledge-backed artifacts.
- Dual artifacts such as `usecase` and `research`.
- Local projection writes.
- Native provider writes.
- MCP fallback writes.

## Current Limitations

- Local projection write guarding is implemented for configured local projection and filesystem provider paths.
- Provider write wrappers are not implemented yet.
- The ledger records that a file was read; it cannot prove semantic use.

## Change Log

- 2026-05-13 — [#28](https://github.com/studykit/studykit-plugins/issues/28) — Published curated authoring enforcement page in repository `wiki/` directory.
- 2026-05-13 — [#30](https://github.com/studykit/studykit-plugins/issues/30) — Documented SessionStart authoring policy injection.
- 2026-05-13 — [#31](https://github.com/studykit/studykit-plugins/issues/31) — Documented hook read recording and local projection write guarding.
