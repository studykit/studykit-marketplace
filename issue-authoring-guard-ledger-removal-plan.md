# Authoring Guard and Ledger Removal Plan

## Goal

Remove the hidden mechanical authoring enforcement from workflow hooks and scripts while keeping the authoring policy and operator workflow intact.

The authoring policy remains: before provider writes, the assistant should resolve required authoring paths, read the returned documents, draft the content, and ask `workflow-operator` to perform the provider/cache operation and verification.

## Non-Goals

- Do not remove runtime/session identification.
- Do not remove `CODEX_THREAD_ID`, `CLAUDE_CODE_SESSION_ID`, `WORKFLOW_SESSION_ID`, workflow env exports, hook-state lookup, or session-scoped context injection.
- Do not remove authoring path discovery or resolver logic.
- Do not weaken cache refresh, cache projection validation, metadata protection, or provider write verification.
- Do not replace the hidden guard with a deprecated no-op compatibility layer.

## Removal Scope

Remove guard-only behavior:

- Authoring read ledger files and state.
- Hook-side automatic tracking of authoring file reads.
- Script-side checks that block provider writes because required authoring files were not recorded in a session ledger.
- CLI flags that exist only to drive authoring guard evaluation, such as guard type or guard state directory flags.
- Tests that assert writes are blocked by missing authoring ledger entries.
- Operator or guide text that tells agents to satisfy, inspect, or reason about the hidden ledger.

Keep policy-facing behavior:

- Required authoring path discovery.
- Main assistant responsibility to read required authoring docs before drafting.
- `workflow-operator` responsibility to execute provider/cache operations and refresh/verify cache state.
- Runtime/session state used for workflow context, exports, and hook lifecycle behavior.

## Expected Code Areas

Inspect and update these areas:

- `plugins/workflow/scripts/authoring_guard.py`
- `plugins/workflow/scripts/authoring_ledger.py`
- `plugins/workflow/scripts/workflow_github.py`
- `plugins/workflow/scripts/workflow_providers.py`
- `plugins/workflow/scripts/workflow_cache_writeback.py`
- `plugins/workflow/scripts/workflow_cache_comments.py`
- `plugins/workflow/scripts/workflow_cache_relationships.py`
- `plugins/workflow/scripts/workflow_cache_issue_drafts.py`
- `plugins/workflow/scripts/workflow_hook.py`
- `plugins/workflow/scripts/hook_claude.py`
- `plugins/workflow/scripts/hook_codex.py`
- `plugins/workflow/tests/`
- `plugins/workflow/agents/workflow-operator.md`
- `.codex/agents/workflow-operator.toml`
- `guide/adapter-guide.md`
- `plugins/workflow/scripts/AGENTS.md`

## Implementation Steps

1. Search for all imports, CLI flags, tests, and documentation references to `authoring_guard`, `authoring_ledger`, `guard-type`, `state-dir`, read ledger, and authoring guard messages.
2. Classify each usage as one of:
   - guard/ledger enforcement: remove;
   - authoring path discovery/policy: keep;
   - runtime/session state: keep;
   - unrelated provider/cache validation: keep.
3. Remove guard/ledger modules and hook wiring.
4. Remove provider write guard callback plumbing from workflow scripts.
5. Remove guard-only CLI options while preserving non-guard runtime/session options.
6. Update tests to assert provider/cache operations and policy-facing path discovery instead of hidden ledger blocking.
7. Update operator and guide text so agents do not reason about hidden ledger state.
8. Run focused workflow tests, then the full workflow plugin test suite.

## Verification

Run:

```bash
uv run --with pytest --with python-frontmatter --with PyYAML pytest plugins/workflow/tests
```

Also inspect command help for changed scripts to ensure removed guard-only flags are not documented anymore, while runtime/session behavior remains intact where it is not guard-related.

## Acceptance Criteria

- No hook or script blocks provider writes based on an authoring-read ledger.
- No agent-facing documentation asks operators or assistants to satisfy a hidden authoring ledger.
- Authoring resolver/path discovery remains available.
- Runtime/session state behavior remains intact.
- Provider/cache write, refresh, and verification flows still pass tests.
- Full workflow tests pass.
