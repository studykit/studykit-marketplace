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
- If the active project has a valid `.workflow/config.yml`, the hook injects concise workflow policy as `additionalContext`.
- If the hook payload identifies a spawned agent session, the hook emits nothing.
- In Codex, `SessionStart` does not provide a direct subagent field in the hook payload, so the adapter also checks the documented `transcript_path` for initial session metadata marked as a subagent thread.
- The policy asks the main assistant to ask `../agents/workflow-operator.md` which authoring file paths must be read before workflow artifact edits, or documentation edits that create or update workflow-backed knowledge artifacts. The operator returns paths only for workflow artifacts and `NONE` for non-workflow artifacts; the main assistant reads returned paths directly.
- The policy keeps content interpretation in the main assistant: the workflow operator returns provider/cache metadata, issue relationship metadata, and paths only, not issue or wiki content summaries.
- For GitHub issue providers, the policy asks the main assistant to delegate workflow provider, cache, write-back, comment append, authoring guard operations, and any raw GitHub CLI (`gh`) operation to `../agents/workflow-operator.md` first.
- The workflow operator uses workflow scripts first, then falls back to raw `gh` when those scripts cannot support or complete the GitHub operation.
- For filesystem issue providers, the policy describes local Markdown artifact editing instead of provider cache, write-back, comment append, or raw `gh` delegation.
- The main assistant does not run raw `gh` for workflow operations; if the workflow operator cannot complete a GitHub operation, the main assistant reports that limitation.
- The main assistant passes workflow intent, issue refs, artifact type, and session id rather than carrying command syntax in context.
- The hook always exits `0`.

## UserPromptSubmit

`UserPromptSubmit` dispatches to `../scripts/workflow_hook.py user-prompt`.

Behavior:

- Scans the submitted prompt for same-repository issue references such as `#45`, `owner/repo#45`, and matching GitHub issue URLs.
- Reads each detected issue through the workflow provider read path with the default cache policy.
- Uses existing cache projections on cache hits; fetches provider data and writes the cache on misses.
- Emits concise `additionalContext` only for issue numbers not already announced in the current session.
- Reports project-relative issue cache paths, for example `.workflow-cache/issues/45/`.
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
