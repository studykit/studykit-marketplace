# plugins/workflow/hooks/

Workflow hooks are adapters around shared scripts in `../scripts/`.

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
