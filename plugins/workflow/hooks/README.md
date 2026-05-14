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
- If the active project has a valid `.workflow/config.yml`, the hook injects a concise routing policy as `additionalContext`. The policy is intentionally narrow: it announces that the project is workflow-configured, names the issue provider, tells the main assistant to delegate workflow operations to `../agents/workflow-operator.md`, and reiterates that the operator returns metadata and paths only — the main assistant reads artifact content directly.
- If the hook payload identifies a spawned agent session, the hook emits nothing.
- In Codex, `SessionStart` does not provide a direct subagent field in the hook payload, so the adapter also checks the documented `transcript_path` for initial session metadata marked as a subagent thread.
- For GitHub issue providers, the policy adds that the main assistant does not run raw `gh` for workflow operations; the operator runs workflow scripts and may fall back to raw `gh` internally.
- For filesystem issue providers, the policy adds that workflow issues are local Markdown artifacts edited directly at the paths the operator returns; provider cache, write-back, and comment-append delegation does not apply.
- For other providers, the policy tells the main assistant to report any limitation when the operator cannot complete a provider operation, rather than reaching for provider-specific tools directly.
- Detailed authoring resolver, ledger, guard, `NONE` convention, and script command syntax are not injected here — those live in `../agents/workflow-operator.md` and are discovered when the operator is consulted.
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
