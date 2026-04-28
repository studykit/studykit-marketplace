# Use Case Session Wrap Up

The interview ends only when the user says so. Never conclude on your own — even if all gaps seem covered, the user may want to go deeper.

When the user indicates they're done, mark the in-progress phase task `completed`, then run **End Iteration**.

## End Iteration procedure

1. **Launch `Agent(subagent_type: "a4:usecase-explorer")`** to surface additional perspectives. Pass `a4/` path and the expected report output path (`a4/research/<label>.md`).

2. **Reflect accepted candidates** as new UC files (allocate id, write `usecase/<id>-<slug>.md` per `./progressive-extraction.md`).

3. **Launch `Agent(subagent_type: "a4:usecase-reviewer")`**. Pass `a4/` path and any prior-session review item ids. The reviewer emits one review item file per finding into `a4/review/<id>-<slug>.md`.

4. **Walk findings** — for each emitted review item, present to the user. Resolve in place (edit the target UC / wiki page, set `status: resolved` in the review item via `transition_status.py`) or defer (leave `status: open`).

5. **Wiki close guard** — for each resolved review item with non-empty `wiki_impact`, verify each referenced wiki page has a `<change-logs>` bullet whose markdown link points at the causing issue. Warn + allow override when missing.

6. **Ready-gate.** Per-UC ask the user whether each UC at `status: draft` or `status: revising` is ready to hand off. Accept natural-language answers:
   - yes / ok / 확정 / `"mark ready"` → call the writer:
     ```bash
     uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" \
       "$(git rev-parse --show-toplevel)/a4" \
       --file "usecase/<id>-<slug>.md" --to ready \
       --reason "user confirmed ready-gate"
     ```
   - no / `"아직"` / `"still iterating"` / silence → leave at current status.

   Only `draft` and `revising` UCs are offered. UCs at `ready`, `implementing`, `shipped`, `superseded`, `discarded`, or `blocked` are skipped. `task-implementer` refuses to start on a UC at any status other than `ready`, so this gate is the hand-off point between spec work and coding.

7. **Report a summary**: UCs confirmed, UCs flipped to `ready`, wiki pages written, review items opened/resolved. Suggest `/a4:domain` next (cross-cutting concept extraction). If `a4/domain.md` already exists and looks current, suggest `/a4:arch` instead.

## Cross-stage findings

This skill primary-authors `context.md`, `actors.md`, and `nfr.md` (per `../wiki-authorship.md`). When iteration uncovers an issue in `domain.md` or `architecture.md`, **continue** with usecase work and emit a review item targeting the upstream wiki — do not edit it inline.

## Execution order

Explorer first (find gaps and new UC candidates), then reviewer (validates the full set).
