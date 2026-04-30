# Revising an `implementing` UC

When the user asks to edit a UC that is currently `status: implementing` (e.g., "UC 5 Flow 수정해줘", "fix the spec for UC-7"), do not silently edit the body.

## Procedure

1. **Confirm** the transition:

   > UC X is currently `implementing`. Edit in-place means flipping to `revising` (pauses code work; resets `progress`/`failing` tasks to `pending`; `complete` tasks stay). OK?

2. **On user confirmation, edit the UC's `status:`** from `implementing` to `revising` directly with the `Edit` tool. The PostToolUse cascade hook detects the transition, refreshes `updated:` on the UC, and resets `progress` / `failing` tasks across the four issue families (`task` / `bug` / `spike` / `research`) back to `pending`. Surface the hook's `additionalContext` to the user so they can see which tasks were reset.

3. **Walk through the edit with the user** (Flow, actors, Validation, Error handling) — same protocol as iteration on a `draft` UC. When the user indicates the spec is done, the wrap-up ready-gate flips `revising → ready`.

## coder-triggered revisions

If `coder` previously triggered the flip (a review item with `source: coder` exists for this UC), walk those review items first — they describe exactly what ambiguity blocked implementation.
