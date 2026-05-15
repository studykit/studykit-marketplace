# Workflow scripts instructions

This directory contains workflow plugin script code. Before changing script behavior, route through `../../../guide/AGENTS.md` and follow `../../../guide/adapter-guide.md` for adapter boundaries and invocation-context assumptions.

## Authoring guard boundary

`./authoring_ledger.py` and `./authoring_guard.py` are Claude Code hook-side helpers.

- They are not Codex issue creation or issue update scripts.
- Do not wire Codex issue create/update flows to these files.
- Do not treat their ledger state as the Codex write authorization source.
- For Codex issue create/update flows, use the workflow operator path: resolve required authoring files, read those docs in-session, draft the change, then let `workflow-operator` perform the provider write and cache verification.

If this boundary changes, update the hook adapter documentation and tests in the same change.
