# Revising an `implementing` UC

When the user asks to edit a UC that is currently `status: implementing` (e.g., "UC 5 Flow 수정해줘", "fix the spec for UC-7"), do not silently edit the body.

## Procedure

1. **Confirm** the transition:

   > UC X is currently `implementing`. Edit in-place means flipping to `revising` (pauses code work; resets `progress`/`failing` tasks to `pending`; `complete` tasks stay). OK?

2. **On user confirmation, call the writer:**

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" \
     "$(git rev-parse --show-toplevel)/a4" \
     --file "usecase/<id>-<slug>.md" --to revising \
     --reason "user-triggered spec edit"
   ```

   The script cascades task status automatically.

3. **Walk through the edit with the user** (Flow, actors, Validation, Error handling) — same protocol as iteration on a `draft` UC. When the user indicates the spec is done, the wrap-up ready-gate flips `revising → ready`.

## task-implementer-triggered revisions

If `task-implementer` previously triggered the flip (a review item with `source: task-implementer` exists for this UC), walk those review items first — they describe exactly what ambiguity blocked implementation.
