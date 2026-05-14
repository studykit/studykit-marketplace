# Workflow Plugin

Provider-backed workflow over GitHub Issues, Jira, GitHub repository `wiki/`
files, and Confluence.

The plugin keeps issue-backed work tracking separate from knowledge-backed
documentation. In provider-backed mode, local files are optional projections;
the provider remains the source of truth.

## Runtime Surface

Key files:

- `.claude-plugin/plugin.json` — Claude plugin metadata.
- `.codex-plugin/plugin.json` — Codex plugin metadata.
- `hooks/hooks.json` — Claude hook declarations.
- `hooks/hooks.codex.json` — Codex hook declarations.
- `agents/workflow-operator.md` — operator agent instructions.
- `scripts/` — provider, cache, authoring, ledger, guard, and hook scripts.
- `authoring/` — workflow artifact authoring contracts.

Use `hooks/README.md` for hook-specific behavior. Use
`../../wiki/workflow/workflow-configuration.md` for the configuration schema.

## Configuration

A configured project has `.workflow/config.yml` at the repository root.

Minimal shape:

```yaml
version: 1
mode: remote-native

providers:
  issues:
    kind: github
    repo: org/repo
  knowledge:
    kind: github

issue_id_format: github

local_projection:
  mode: none

commit_refs:
  enabled: true
  style: provider-native
```

Inspect resolved configuration:

```bash
"./plugins/workflow/scripts/workflow" workflow_config.py \
  --require \
  --json
```

The `scripts/workflow` launcher normalizes shell-tool runtime state before it
executes a workflow script. It preserves `WORKFLOW_PLUGIN_ROOT`,
`WORKFLOW_PROJECT_DIR`, and `WORKFLOW_SESSION_ID` so repeated shell commands do
not need to pass plugin root, project root, or session id flags.

## Authoring Policy

Workflow authoring contracts apply only to workflow artifact types:

- Issue-backed: `task`, `bug`, `spike`, `epic`, and `review`.
- Knowledge-backed: `spec`, `architecture`, `domain`, `context`, `actors`,
  `nfr`, and `ci`.
- Dual-role: `usecase` and `research`.

Before editing a workflow artifact, resolve and read the required files from
`authoring/`. For non-workflow artifacts, such as `AGENTS.md`, `CLAUDE.md`,
plugin README files, ordinary docs outside configured workflow knowledge, or
host configuration files, the workflow operator returns `NONE`.

Resolve authoring files:

```bash
"./plugins/workflow/scripts/workflow" authoring_resolver.py \
  --type review \
  --role issue \
  --json
```

Check the session authoring guard:

```bash
"./plugins/workflow/scripts/workflow" authoring_guard.py \
  --type review \
  --role issue \
  --provider github \
  --json
```

## Workflow Operator

The main assistant delegates workflow provider/cache operations to
`agents/workflow-operator.md` instead of carrying script recipes in context.

Use the operator for:

- Cache-aware provider reads.
- Guarded GitHub issue writes.
- Local issue projection write-back.
- Pending local comment or relationship apply.
- Authoring resolver, ledger, and guard operations.
- Provider mutation verification and cache refresh.

The operator returns operational metadata, paths, relationship metadata, and
verification details only. It does not summarize issue bodies, comments, or
knowledge page content; the main assistant reads and interprets content
directly.

## Hooks

Session hooks are intentionally concise:

- `SessionStart` injects configured workflow policy only for main sessions.
- `UserPromptSubmit` prepares cache projections for mentioned GitHub issue
  references and injects project-relative cache paths.
- `Stop` records mentioned issue references as pending for the next prompt.
- `PostToolUse` on reads records authoring file reads in the session ledger.
- `PreToolUse` on writes blocks local projection writes until required
  authoring files were read.

Non-workflow projects receive no workflow hook output.

## Cache Projections

GitHub issue reads may be cached under `.workflow-cache/`, which is ignored by
Git.

Configured-repository shape:

```text
.workflow-cache/issues/ISSUE_NUMBER/
  issue.md
  comments/
    index.yml
    YYYY-MM-DDTHHMMSSZ-PROVIDER_COMMENT_ID.md
  relationships.yml
```

External GitHub repositories are namespaced under
`.workflow-cache/github.com/OWNER/REPO/issues/ISSUE_NUMBER/`.

Cache policies:

- `default` — read existing cache first, otherwise fetch and cache provider
  data.
- `refresh` — fetch provider data and overwrite the cache.
- `bypass` — fetch provider data without reading or writing the cache.

Fetch issue cache explicitly:

```bash
"./plugins/workflow/scripts/workflow" workflow_cache_fetch.py \
  --json \
  42
```

## Validation

Run workflow plugin tests:

```bash
uv run --with pytest pytest plugins/workflow/tests
```
