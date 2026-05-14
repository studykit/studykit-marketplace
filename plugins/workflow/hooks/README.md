# plugins/workflow/hooks/

Workflow hooks dispatch through runtime-specific entry scripts. Both scripts
dispatch from the payload `hook_event_name` and own their runtime-specific
payload/env extraction. They call common plain functions from
`../scripts/workflow_hook.py` for shared workflow behavior such as policy
injection, authoring ledger updates, local projection guards, and issue-cache
context.

The Codex manifest registers only `SessionStart`, `UserPromptSubmit`, and
`Stop`. The Claude-side `PostToolUse` Read ledger and `PreToolUse` write
guard are intentionally not wired on Codex: Codex has no built-in `Read`
tool (reads happen through `Bash` or MCP), so the read ledger cannot be
populated and the matching write guard would block unconditionally.

When either runtime script writes hook output to stdout, it writes JSON only.
Empty stdout is used for no-op hook runs.

## PostToolUse Read (Claude only)

`PostToolUse` on `Read` records the read.

Behavior:

- Records reads of plugin-bundled workflow authoring files under `../authoring/`.
- Records paths by absolute path in the session read ledger.
- Emits nothing on success.
- Emits nothing outside configured workflow projects.

## PreToolUse Write/Edit (Claude only)

`PreToolUse` on file writes checks the write.

Behavior:

- Checks local workflow projection writes before mutation.
- Uses the shared resolver and ledger guard.
- Blocks the write when required authoring files are missing.
- The block message lists absolute authoring file paths to read.
- Emits nothing for non-workflow projects or non-projection writes.

## SessionStart

`SessionStart` injects workflow policy for configured projects.

Behavior:

- If the active project has no `.workflow/config.yml`, the hook emits nothing.
- The hook prepares a normalized shell environment contract for workflow shell commands: `WORKFLOW`, `WORKFLOW_PLUGIN_ROOT`, `WORKFLOW_PROJECT_DIR`, and `WORKFLOW_SESSION_ID`.
- Claude writes that contract to `CLAUDE_ENV_FILE` when Claude provides it for `SessionStart`. Claude operator subagent shell commands can use the same persisted `WORKFLOW_*` contract, so the workflow plugin does not use a Claude `SubagentStart` hook.
- Codex cannot persist environment variables from `SessionStart`; `hook_codex.py` writes a session-scoped export file under `.workflow-cache/hook-state/`, keyed by the Codex hook `session_id`. The `../scripts/workflow` wrapper later locates and sources that file from the shell-visible `CODEX_THREAD_ID`.
- If the active project has a valid `.workflow/config.yml`, the hook injects a concise routing policy as `additionalContext`. The policy is intentionally narrow: it announces that the project is workflow-configured, names the issue provider, tells the main assistant to delegate workflow operations to `../agents/workflow-operator.md`, and reiterates that the operator returns metadata and paths only — the main assistant reads artifact content directly.
- In Codex subagent shells, `CODEX_THREAD_ID` is the subagent's own thread id and no parent-thread environment variable is available. For Codex subagent `SessionStart` payloads, `hook_codex.py` checks `transcript_path` for `session_meta` records that identify the spawned agent. When the spawned agent matches `workflow-operator`, the hook extracts the parent thread id from transcript metadata and writes the Codex export file under the subagent hook `session_id`, with `WORKFLOW_SESSION_ID` set to the parent thread id. The hook also injects a concise bootstrap context containing the absolute `../scripts/workflow` launcher path. The operator uses that path as `$WORKFLOW`; `../scripts/workflow` owns session translation.
- For all other subagent SessionStart payloads (non-operator agents, or operator subagents without an extractable parent id), the hook emits nothing.
- Claude operator subagents use the persisted contract from the Claude session environment. If Claude sends an agent-tagged `SessionStart` payload, the hook does not inject the main-session policy into that subagent.
- For GitHub issue providers, the policy adds that the main assistant does not run raw `gh` for workflow operations; the operator runs workflow scripts and may fall back to raw `gh` internally.
- For filesystem issue providers, the policy adds that workflow issues are local Markdown artifacts edited directly at the paths the operator returns; provider cache, write-back, and comment-append delegation does not apply.
- For other providers, the policy tells the main assistant to report any limitation when the operator cannot complete a provider operation, rather than reaching for provider-specific tools directly.
- Detailed authoring resolver, ledger, guard, `NONE` convention, and script command syntax are not injected here — those live in `../agents/workflow-operator.md` and are discovered when the operator is consulted.
- The hook always exits `0`.

## UserPromptSubmit

`UserPromptSubmit` caches issue references.

Behavior:

- Scans the submitted prompt for same-repository issue references such as `#45`, `owner/repo#45`, and matching GitHub issue URLs.
- Reads each detected issue through the workflow provider read path with the default cache policy.
- Uses existing cache projections on cache hits; fetches provider data and writes the cache on misses.
- Emits concise `additionalContext` only for issue numbers not already announced in the current session.
- Reports project-relative issue cache paths, for example `.workflow-cache/issues/45/`.
- Emits nothing for non-workflow projects, non-GitHub issue providers, missing issue references, or provider read failures.

## Stop

`Stop` records pending issue references.

Behavior:

- Records issue references from the stop payload and unannounced session-mentioned issues as pending.
- Does not read providers or write issue cache projections; the next `UserPromptSubmit` performs that work.
- Emits no JSON output; `Stop` output is reserved for host-supported block decisions.
- Skips when `stop_hook_active` is true to avoid hook loops.
- Emits nothing for clean no-op cases and never blocks the stop flow.

## Manifests

- `hooks.json` is the Claude hook manifest; all event commands invoke `../scripts/hook_claude.py`.
- `hooks.codex.json` is referenced by `../.codex-plugin/plugin.json`; all event commands invoke `../scripts/hook_codex.py`.
