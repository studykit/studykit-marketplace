# Workflow Plugin

Provider-backed workflow over GitHub Issues, Jira, GitHub repository `wiki/` directory, and Confluence.

The plugin separates issue-backed work tracking from knowledge-backed documentation. Local files are optional projections, not the source of truth in provider-backed mode.

## Current status

This plugin is a clean-break implementation in progress.

Implemented so far:

- Provider-backed design notes in `doc/`.
- Workflow configuration schema and shared loader in `scripts/workflow_config.py`.
- Authoring contracts in `authoring/`.
- Authoring resolver script in `scripts/authoring_resolver.py`.
- Session authoring read ledger in `scripts/authoring_ledger.py`.
- Authoring write guard in `scripts/authoring_guard.py`.
- SessionStart authoring policy hook in `scripts/workflow_hook.py`.

## Configuration

A configured project uses a repository-root `workflow.config.yml`.

Example:

```yaml
version: 1
mode: remote-native

providers:
  issues:
    kind: github
    repo: org/repo
  knowledge:
    kind: confluence
    site: example.atlassian.net
    space: ENG

local_projection:
  mode: none

commit_refs:
  enabled: true
  style: provider-native
```

See `doc/workflow-config.md` for the version 1 schema, provider aliases, and validation rules.

Inspect the resolved configuration:

```bash
python3 plugins/workflow/scripts/workflow_config.py \
  --project . \
  --require \
  --json
```

## Authoring resolver

Resolve required authoring files before creating or editing workflow artifacts:

```bash
python3 plugins/workflow/scripts/authoring_resolver.py \
  --project . \
  --type review \
  --role issue \
  --json
```

The resolver returns absolute plugin-bundled authoring file paths.

## SessionStart policy

Configured projects receive a concise SessionStart policy only when `workflow.config.yml` exists.

The hook injects the resolver command and reminds the assistant to read every path from `required_authoring_files` before writing workflow artifacts. It does not auto-trigger workflow skills.

## Authoring read ledger

Record authoring files after they are read:

```bash
python3 plugins/workflow/scripts/authoring_ledger.py \
  --project . \
  --session SESSION_ID \
  record --json \
  /absolute/path/to/plugins/workflow/authoring/review-authoring.md
```

Check required reads before writing:

```bash
python3 plugins/workflow/scripts/authoring_ledger.py \
  --project . \
  --session SESSION_ID \
  check --json \
  /absolute/path/to/plugins/workflow/authoring/review-authoring.md
```

## Authoring write guard

Check resolver requirements against the session read ledger before writing:

```bash
python3 plugins/workflow/scripts/authoring_guard.py \
  --project . \
  --session SESSION_ID \
  --type review \
  --role issue \
  --provider github \
  --json
```
