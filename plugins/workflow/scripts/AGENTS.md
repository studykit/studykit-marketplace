# Workflow scripts instructions

This directory contains workflow plugin script code. Before changing script behavior, route through `../../../guide/AGENTS.md` and follow `../../../guide/adapter-guide.md` for adapter boundaries and invocation-context assumptions.

## Authoring policy boundary

Authoring policy is procedural, not hidden script enforcement. Keep the authoring resolver available so operators can return required authoring paths, but do not add hook-side read-state tracking or script-side authoring-read enforcement.

- Do not block provider writes because hidden read-state is missing.
- Do not add runtime-specific exceptions for authoring-read tracking.
- Preserve runtime/session state used for workflow env exports, hook state, and context injection.
- Preserve provider cache projection protections such as frontmatter ownership checks.
- For issue create/update flows, use the workflow operator path: resolve required authoring files, read those docs in-session, draft the change, then let `workflow-operator` perform the provider write and cache verification.
