# Progressive Use Case Extraction

When the conversation reveals enough context, draft a Use Case and present it to the user for confirmation. Every UC has five required fields: **Actor**, **Goal**, **Situation**, **Flow**, **Expected Outcome**. Abstraction must stay at the user level — the banned-term list and conversion examples are in `./abstraction-guard.md`.

## How to present

> Based on what you've described, here's a Use Case:
>
> **UC-draft. Share meeting summary**
> - **Actor:** Meeting organizer
> - **Goal:** Share key decisions with absent teammates quickly
> - **Situation:** Just finished a 30-minute meeting; absent teammates need the outcome
> - **Flow:** 1. Open the meeting record … 5. Send to the team channel
> - **Expected Outcome:** Absent teammates receive a 3-line summary within minutes; organizer spends < 2 minutes instead of 20
>
> Does this capture it? Anything to adjust?

## After core confirmation: drill into precision

- **Validation** — input constraints, limits, required formats (user-visible, not system-internal).
- **Error handling** — what the user sees when things fail.
- **Boundary conditions** — empty input, maximum items, concurrent access, timeouts.

Record these in the UC's body as `## Validation` / `## Error Handling` sections. Both are optional — omit when the UC has no meaningful constraints or failure modes.

## Write the UC file on confirmation

1. Derive a kebab-case slug from the title (`Share meeting summary` → `share-summary`).
2. Run `allocate_id.py` to get the next id `N`.
3. Write `a4/usecase/<N>-<slug>.md` per `../../../authoring/usecase-authoring.md`. Required body sections: `## Goal`, `## Situation`, `## Flow` (numbered list), `## Expected Outcome`. Optional: `## Validation`, `## Error Handling`, `## Dependencies`, `## Change Logs`, `## Log` (hand-maintained).
4. Create a task `"Discovery: UC-<N> <title>"` and mark it completed.
5. **In-situ nudge** — see `./in-situ-wiki-nudge.md`.
