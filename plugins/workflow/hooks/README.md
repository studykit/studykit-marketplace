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

- If the active project has no `workflow.config.yml`, the hook emits nothing.
- If the active project has a valid `workflow.config.yml`, the hook injects a concise authoring resolver policy as `additionalContext`.
- The policy points to the shared resolver, ledger, and guard commands.
- The hook does not start workflow skills.
- The hook always exits `0`.

## Manifests

- `hooks.json` is the Claude hook manifest.
- `hooks.codex.json` is referenced by `../.codex-plugin/plugin.json`.
