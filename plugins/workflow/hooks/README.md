# plugins/workflow/hooks/

Workflow hooks are adapters around shared scripts in `../scripts/`.

## PostToolUse Read

`PostToolUse` on `Read` dispatches to `../scripts/workflow_hook.py post-read`.

Behavior:

- Records reads of plugin-bundled workflow authoring files under `../authoring/`.
- Records paths by absolute path in the session read ledger.
- Emits nothing on success.
- Emits nothing outside configured workflow projects.

## PreToolUse Write/Edit

`PreToolUse` on file writes dispatches to `../scripts/workflow_hook.py pre-write`.

Behavior:

- Checks local workflow projection writes before mutation.
- Uses the shared resolver and ledger guard.
- Blocks the write when required authoring files are missing.
- The block message lists absolute authoring file paths to read.
- Emits nothing for non-workflow projects or non-projection writes.

## SessionStart

`SessionStart` dispatches to `../scripts/workflow_hook.py session-start`.

Behavior:

- If the active project has no `.workflow/config.yml`, the hook emits nothing.
- If the active project has a valid `.workflow/config.yml`, the hook injects a concise authoring resolver policy and provider cache-base context as `additionalContext`.
- The policy announces the workflow plugin root and points to the shared resolver, ledger, guard, and GitHub issue write wrapper commands with root-relative script paths.
- For GitHub issue providers, the policy tells agents to use `../scripts/workflow_github.py` for guarded `edit-body`, `close`, and `reopen` mutations instead of paired ad hoc `gh` write/read calls.
- The cache context announces the workflow cache root and, for GitHub issue providers, the GitHub issue cache base.
- Later hook-reported issue cache paths are relative to the announced GitHub issue cache base.
- The cache context points agents to `../scripts/workflow_cache_fetch.py` for explicit cache fetches through the same shared provider cache path used by `UserPromptSubmit`.
- The hook does not start workflow skills.
- The hook always exits `0`.

## UserPromptSubmit

`UserPromptSubmit` dispatches to `../scripts/workflow_hook.py user-prompt`.

Behavior:

- Scans the submitted prompt for same-repository issue references such as `#45`, `owner/repo#45`, and matching GitHub issue URLs.
- Reads each detected issue through the workflow provider read path with the default cache policy.
- Uses existing cache projections on cache hits; fetches provider data and writes the cache on misses.
- Emits concise `additionalContext` only for issue numbers not already announced in the current session.
- Reports issue cache paths relative to the GitHub issue cache base announced by `SessionStart`, for example `45/`.
- Emits nothing for non-workflow projects, non-GitHub issue providers, missing issue references, or provider read failures.

## Stop

`Stop` dispatches to `../scripts/workflow_hook.py stop`.

Behavior:

- Records issue references from the stop payload and unannounced session-mentioned issues as pending.
- Does not read providers or write issue cache projections; the next `UserPromptSubmit` performs that work.
- Emits no JSON output; `Stop` output is reserved for host-supported block decisions.
- Skips when `stop_hook_active` is true to avoid hook loops.
- Emits nothing for clean no-op cases and never blocks the stop flow.

## Manifests

- `hooks.json` is the Claude hook manifest.
- `hooks.codex.json` is referenced by `../.codex-plugin/plugin.json`.
