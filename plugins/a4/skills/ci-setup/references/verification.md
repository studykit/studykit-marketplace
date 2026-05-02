# Verification Checklist

Run each check and record outcomes for the issue-handling step. The same outcomes feed the `## How to run tests` table in `a4/ci.md` (Step 5).

For every tier in scope:

- **Runner exits 0** with at least one passing test.
- **Tier isolation** — running the tier in question does not leak state into other tiers (no temp-dir collisions, no port reuse without cleanup, no global mutation).
- **Task entry point** — the wired command (e.g., `npm test`) actually invokes the tier as expected.

After all in-scope tiers pass:

- **Multi-tier run** — running tiers sequentially (or as the CI pipeline runs them) produces deterministic outcomes.
