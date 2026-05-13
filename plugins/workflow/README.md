# Workflow Plugin

Provider-backed workflow over GitHub Issues, Jira, GitHub repository `wiki/` directory, and Confluence.

The plugin separates issue-backed work tracking from knowledge-backed documentation. Local files are optional projections, not the source of truth in provider-backed mode.

## Current status

This plugin is a clean-break implementation in progress.

Implemented so far:

- Provider-backed knowledge and design notes in `../../wiki/workflow/`.
- Workflow configuration schema and shared loader in `scripts/workflow_config.py`.
- Authoring contracts in `authoring/`.
- Authoring resolver script in `scripts/authoring_resolver.py`.
- Session authoring read ledger in `scripts/authoring_ledger.py`.
- Authoring write guard in `scripts/authoring_guard.py`.
- Workflow hooks in `scripts/workflow_hook.py` for SessionStart policy/cache context injection, prompt/stop issue cache preparation, authoring read recording, and local projection write guarding.
- Provider interface scaffold in `scripts/workflow_providers.py` for issue and knowledge provider dispatch.
- Repo-local provider read cache projections in `scripts/workflow_cache.py`.
- Opt-in provider write-back freshness checks that compare cache projection timestamps with current provider state before mutation.
- Pending GitHub relationship apply from `relationships-pending.yml` through provider wrapper operations.
- Workflow operator agent in `agents/workflow-operator.md` for running provider/cache scripts without pushing command recipes into the main assistant context.

## Configuration

A configured project uses a repository-root `.workflow/config.yml`.

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

issue_id_format: github

local_projection:
  mode: none

commit_refs:
  enabled: true
  style: provider-native
```

See `../../wiki/workflow/workflow-configuration.md` for the version 1 schema, provider aliases, and validation rules.

Inspect the resolved configuration:

```bash
python3 plugins/workflow/scripts/workflow_config.py \
  --project . \
  --require \
  --json
```

## Provider interfaces

Provider operations should use `scripts/workflow_providers.py` instead of direct ad-hoc provider calls. The scaffold defines issue and knowledge provider interfaces, a transport registry, and a dispatcher.

Transport priority is represented in code as:

1. Native wrapper transport.
2. MCP fallback transport.

The default registry currently wires the GitHub Issues native transport to `scripts/workflow_github.py`. Knowledge transports and MCP fallback adapters are scaffolded by interface and can be registered as they are implemented.

Write-capable provider operations must pass through the dispatcher with an authoring guard callback before mutation. Read-capable provider operations use `ProviderContext.cache_policy` to choose local-cache-first, refresh, or bypass behavior where cache support exists.

GitHub issue write operations can request a freshness check by setting `freshness_check` in the provider payload. The check compares the relevant cache projection metadata (`source_updated_at` and `fetched_at`) with the current provider timestamp before writing. Supported targets are `issue`, `comments`, and `relationships`; omit `freshness_target` to use the operation default. Stale or missing local freshness metadata blocks writes to existing provider artifacts with a refresh-first remediation message. Pending new artifacts can set `pending_new` to skip remote freshness checks for an artifact that does not exist yet.

## Provider read cache

GitHub issue reads can be cached under repository-local `.workflow-cache/` projections. The cache root is ignored by Git.

Current configured-repository projection shape:

```text
.workflow-cache/issues/ISSUE_NUMBER/
  issue.md
  comments/
    index.yml
    YYYY-MM-DDTHHMMSSZ-PROVIDER_COMMENT_ID.md
  relationships.yml
```

External GitHub repositories use a namespaced projection shape:

```text
.workflow-cache/github.com/OWNER/REPO/issues/ISSUE_NUMBER/
  issue.md
  comments/
    index.yml
    YYYY-MM-DDTHHMMSSZ-PROVIDER_COMMENT_ID.md
  relationships.yml
```

`issue.md` stores minimal frontmatter and raw provider body Markdown. Comment history uses `comments/index.yml` plus one raw body file per remote comment. `relationships.yml` stores current provider-native relationship data only. Timeline, event, and body-edit reads stay remote provider operations and are not cached by this projection.

Cache policies:

- `default`: read existing cache first, otherwise fetch provider data and write the cache.
- `refresh`: fetch provider data and overwrite the cache.
- `bypass`: fetch provider data without reading or writing the cache.

Hook issue cache behavior:

- `SessionStart` injects workflow authoring policy without cache location context.
- `SessionStart` emits nothing for spawned agent sessions when the host exposes agent markers directly or, in Codex, when the documented `transcript_path` points at session metadata marked as a subagent thread.
- `SessionStart` asks the main assistant to ask `agents/workflow-operator.md` which authoring file paths must be read before documentation or workflow artifact edits. The operator returns paths only; the main assistant reads them directly.
- `SessionStart` tells the main assistant not to delegate issue or wiki content interpretation to `agents/workflow-operator.md`; the operator returns provider/cache metadata, issue relationship metadata, and paths only.
- For GitHub issue providers, `SessionStart` asks the main assistant to delegate explicit provider/cache script operations and raw GitHub CLI (`gh`) operations to `agents/workflow-operator.md` first.
- The workflow operator uses workflow scripts first, then falls back to raw `gh` when those scripts cannot support or complete the GitHub operation.
- For filesystem issue providers, `SessionStart` describes local Markdown artifact editing instead of provider cache, write-back, comment append, or raw `gh` delegation.
- The main assistant does not run raw `gh` for workflow operations; if the workflow operator cannot complete a GitHub operation, the main assistant reports that limitation.
- `UserPromptSubmit` detects same-repository issue references and reads them through the default provider cache policy.
- `Stop` records session-mentioned issue references as pending without provider reads.
- The next `UserPromptSubmit` reads pending issue references through the default provider cache policy and injects their cache paths.
- Hook-injected issue cache paths are project-relative, for example `.workflow-cache/issues/45/`.
- Use hook-provided issue context before ad hoc provider reads when it is available.

Operator-facing explicit cache fetch:

```bash
python3 plugins/workflow/scripts/workflow_cache_fetch.py \
  --project . \
  --json \
  42
```

Use `--cache-policy refresh` when the agent intentionally needs to refresh provider data instead of accepting an existing local projection.

## Workflow operator agent

The main assistant should not need to keep detailed workflow script usage in
context. Delegate script operations to `agents/workflow-operator.md`.

Use the operator agent for:

- Cache-aware provider reads.
- Guarded GitHub issue writes.
- Local issue projection write-back.
- Pending local comment append.
- Authoring file path discovery before documentation or workflow artifact edits.
- Authoring resolver, ledger, and guard execution.
- Provider mutation verification and cache refresh.

The operator owns exact commands and wrapper ordering. The main assistant keeps
only workflow intent, issue refs, artifact type, and the session id needed by
guarded writes.

For path discovery requests, the operator returns required authoring file paths
only. For issue or wiki context, it returns provider/cache metadata, issue
relationship metadata, and paths only. The main assistant reads and summarizes
artifact content directly.

Operator-facing issue cache write-back:

```bash
python3 plugins/workflow/scripts/workflow_cache_writeback.py \
  --project . \
  --session <session-id> \
  --type task \
  --json \
  42
```

Write-back reads `.workflow-cache/.../issues/<issue>/issue.md`, checks provider freshness, updates the provider through guarded wrapper operations, and refreshes the affected cache projection on success.

Operator-facing pending relationship apply:

```bash
python3 plugins/workflow/scripts/workflow_cache_relationships.py \
  --project . \
  --session <session-id> \
  --type task \
  --json \
  42
```

Relationship apply reads `.workflow-cache/.../issues/<issue>/relationships-pending.yml`, checks relationship freshness, applies supported GitHub parent, child, blocked-by, and blocking operations through provider wrappers, removes the consumed pending file, and refreshes `relationships.yml`.

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

Configured projects receive a concise SessionStart policy only when `.workflow/config.yml` exists.

The hook injects provider configuration and a reminder to ask `agents/workflow-operator.md` for required authoring file paths before documentation or workflow artifact edits. The operator returns paths only; it does not read or summarize the files for this discovery step. The policy also keeps issue and wiki content interpretation in the main assistant: the operator returns provider/cache metadata, issue relationship metadata, and paths only. For GitHub issue providers, the workflow operator uses workflow scripts first and falls back to raw `gh` when those scripts cannot support or complete the operation; the main assistant does not run raw `gh` for workflow operations. For filesystem issue providers, the hook points at local Markdown artifact editing instead of provider write-back or raw `gh` delegation. It does not inject cache locations or script command recipes into the main assistant context, and it emits nothing for spawned agent sessions when the host exposes agent markers directly or the Codex transcript metadata marks the thread as a subagent.

## Hook enforcement

Workflow hooks integrate the ledger and guard:

- `UserPromptSubmit` prepares cache projections for mentioned GitHub issue references and injects project-relative cache paths.
- `Stop` records session-mentioned issue references as pending without provider reads or JSON output.
- The next `UserPromptSubmit` prepares pending issue cache projections and injects project-relative cache paths.
- `PostToolUse` on `Read` records plugin-bundled authoring file reads by absolute path.
- `PreToolUse` on writes checks local projection targets before mutation.
- Missing reads block local projection writes with a message listing absolute paths to read.
- Non-workflow projects receive no workflow hook output.

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
