# Launch & Verify Source

The implement loop does not auto-detect commands.

## Resolution

1. **`a4/bootstrap.md`** — single source of truth. Read its `## Verify` section (verified commands, smoke scenario, test isolation flags) plus `## Launch` (build / launch). The bootstrap-authoring flow writes these sections; the roadmap (when present) links to them but does **not** own them.

2. **Halt** when `bootstrap.md` is absent. The implement loop does not pre-judge which upstream work applies, does not auto-chain into a fix, and does not look upstream of `bootstrap.md` itself. `roadmap.md`'s presence or absence is irrelevant to L&V resolution.
