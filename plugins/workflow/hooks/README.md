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
- For Codex subagent SessionStart payloads, the hook checks `transcript_path` for `session_meta` records that identify the spawned agent. When the spawned agent matches `workflow-operator`, the hook injects a separate `## workflow operator session` block with the parent thread id extracted from the transcript so the operator can pass it to `--session` in every ledger and guard call.
- For all other subagent SessionStart payloads (non-operator agents, or operator subagents without an extractable parent id), the hook emits nothing.
- Claude does not fire `SessionStart` for subagents at all; the operator subagent path lives in `SubagentStart` instead (see below).
- For GitHub issue providers, the policy adds that the main assistant does not run raw `gh` for workflow operations; the operator runs workflow scripts and may fall back to raw `gh` internally.
- For filesystem issue providers, the policy adds that workflow issues are local Markdown artifacts edited directly at the paths the operator returns; provider cache, write-back, and comment-append delegation does not apply.
- For other providers, the policy tells the main assistant to report any limitation when the operator cannot complete a provider operation, rather than reaching for provider-specific tools directly.
- Detailed authoring resolver, ledger, guard, `NONE` convention, and script command syntax are not injected here — those live in `../agents/workflow-operator.md` and are discovered when the operator is consulted.
- The hook always exits `0`.

## SubagentStart (Claude only)

Claude fires `SubagentStart` with matcher `workflow-operator` from the `hooks` block defined inside `../agents/workflow-operator.md` frontmatter. The matcher restricts firing to the operator subagent. The hook command runs `../scripts/workflow_hook_claude.py`.

Behavior:

- Validates that the payload targets `workflow-operator` (defensive re-check against the manifest matcher).
- Loads the active project's `.workflow/config.yml`; on missing config or load failure the hook emits nothing.
- Emits `additionalContext` titled `## workflow operator session` containing the parent session id (`session_id` field in the SubagentStart payload, which carries the main session's id) and the workflow project root.
- The injected text instructs the operator to pass the parent session id as `--session` for every authoring ledger, guard, and provider script invocation. Reads recorded by the main session live under that id; defaulting to the subagent's own session id or environment variables would check the wrong ledger.
- Codex has no `SubagentStart` event, so the same outcome is achieved via the Codex branch in the `SessionStart` handler above.
- The hook never blocks (Claude `SubagentStart` has no decision control) and always exits `0`.

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
