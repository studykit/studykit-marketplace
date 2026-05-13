# Workflow Authoring Read Ledger

Date: 2026-05-13

## Purpose

The authoring read ledger records which plugin-bundled authoring files were read in the current session.

The ledger supports the rule:

```text
required_authoring_files ⊆ read_authoring_files
```

A write guard can deny or delay workflow artifact writes until every authoring file returned by the resolver has been read.

## Script

Ledger entry point:

```text
plugins/workflow/scripts/authoring_ledger.py
```

The ledger is session-scoped and project-scoped.

By default, ledger state is stored under the operating-system temp directory, not in the repository. This avoids adding local workflow state to projects that use remote providers as the source of truth.

## Session identity

The script accepts `--session`.

If omitted, it reads the first available environment variable:

1. `WORKFLOW_SESSION_ID`
2. `CODEX_THREAD_ID`
3. `CLAUDE_SESSION_ID`
4. `CLAUDE_CONVERSATION_ID`

If none exist, the command fails.

## Record reads

```bash
python3 plugins/workflow/scripts/authoring_ledger.py \
  --project . \
  --session SESSION_ID \
  record --json \
  /absolute/path/to/plugins/workflow/authoring/review-authoring.md
```

Use `--require-config` on `record` when the caller wants the ledger to operate only in configured workflow projects.

```bash
python3 plugins/workflow/scripts/authoring_ledger.py \
  --project . \
  --session SESSION_ID \
  record --require-config \
  /absolute/path/to/contract.md
```

The workflow `PostToolUse` read hook records plugin-bundled authoring files automatically when a configured project reads a file under `plugins/workflow/authoring/`.

## Check reads

```bash
python3 plugins/workflow/scripts/authoring_ledger.py \
  --project . \
  --session SESSION_ID \
  check --json \
  /absolute/path/to/required-1.md \
  /absolute/path/to/required-2.md
```

Exit codes:

- `0`: every required path was read.
- `3`: one or more required paths are missing.
- `2`: command or ledger error.

## Show ledger

```bash
python3 plugins/workflow/scripts/authoring_ledger.py \
  --project . \
  --session SESSION_ID \
  show --json
```

## Integration with resolver

Typical write guard flow:

1. Call `authoring_resolver.py` for the target artifact.
2. Read every returned absolute path.
3. Call `authoring_ledger.py record` with those paths.
4. Before a provider write, call `authoring_ledger.py check` with the resolver output.
5. Deny or delay the write if check exits `3`.

## Current limitations

- The ledger cannot prove that an LLM semantically used a file. It records that the runtime or wrapper marked the file as read.
- Hook integration records plugin-bundled authoring file reads, but it does not observe non-tool reads outside the host runtime.
- Remote provider write wrappers are not implemented yet.
