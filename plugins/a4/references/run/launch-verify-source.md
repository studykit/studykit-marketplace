# Launch & Verify Source

`/a4:run` does not auto-detect commands.

## Resolution

1. **`a4/bootstrap.md`** — single source of truth. Read its `<verify>` section (verified commands, smoke scenario, test isolation flags) plus `<launch>` (build / launch). Both `/a4:auto-bootstrap` and the manual bootstrap flow write these sections; the roadmap (when present) links to them but does **not** own them.

2. **Halt and delegate to `/a4:compass`** when `bootstrap.md` is absent. Invoke compass with the structured diagnosis argument so its Step 3 Gap Diagnosis recommends the correct upstream skill:

   ```
   Skill({ skill: "a4:compass", args: "from=run; missing=bootstrap.md" })
   ```

   `/a4:run` does not pre-judge which upstream skill applies, does not auto-chain into the recommendation, and does not look upstream of `bootstrap.md` itself — compass's pipeline walk owns those decisions. `roadmap.md`'s presence or absence is irrelevant to L&V resolution.
