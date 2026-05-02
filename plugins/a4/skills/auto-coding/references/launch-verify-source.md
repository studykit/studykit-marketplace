# Launch & Verify Source

The implement loop does not auto-detect commands.

## Resolution

1. **`a4/ci.md`** — single source of truth. Read its `## How to run tests` section (per-tier commands, multi-tier run, test isolation flags) plus `## Test layout` (where to put new tests) and any optional `## Smoke scenario`. The ci-authoring flow writes these sections.

2. **Halt** when `ci.md` is absent. The implement loop does not pre-judge which upstream work applies, does not auto-chain into a fix, and does not look upstream of `ci.md` itself. Tell the user to run `/a4:ci-setup` first, then resume.
