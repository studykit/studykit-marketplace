# Workflow Authoring Write Guard

Date: 2026-05-13

## Purpose

The authoring write guard checks whether the current session has read every authoring file required for a workflow artifact write.

It combines:

- `authoring_resolver.py` for the required contract list.
- `authoring_ledger.py` for the session read list.

## Script

Guard entry point:

```text
plugins/workflow/scripts/authoring_guard.py
```

Example:

```bash
python3 plugins/workflow/scripts/authoring_guard.py \
  --project . \
  --session SESSION_ID \
  --type review \
  --role issue \
  --provider github \
  --json
```

Exit codes:

- `0`: all required authoring files have been read.
- `3`: one or more required authoring files are missing from the ledger.
- `2`: resolver or ledger error.

## JSON output

```json
{
  "ok": false,
  "required_authoring_files": [
    "/absolute/path/to/plugins/workflow/authoring/metadata-contract.md"
  ],
  "missing_authoring_files": [
    "/absolute/path/to/plugins/workflow/authoring/metadata-contract.md"
  ],
  "artifact": {
    "type": "review",
    "role": "issue",
    "provider": "github"
  },
  "config_path": "/repo/workflow.config.yml"
}
```

## Intended callers

- Provider wrapper commands before `gh`, Jira REST, Confluence REST, GitHub repository `wiki/` git writes, or MCP fallback writes.
- Session hooks before local projection writes.
- Skills that create or update workflow artifacts.

## Config behavior

Use `--require-config` when the caller should only operate in configured workflow projects.

Without `--require-config`, the guard can still run with explicit `--provider`. This is useful for tests and tool development.
