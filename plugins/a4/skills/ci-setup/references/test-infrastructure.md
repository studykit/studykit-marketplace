# Test Infrastructure Setup

For each tier flagged `missing` in `./tier-assessment.md`:

1. **Install test dependencies** (runner + assertion lib + plugins) using the stack's standard package / dependency manager.
2. **Create the test runner's standard configuration** at the location the runner expects.
3. **Write one minimal passing test per tier**:
   - unit → import + assert true.
   - integration → verify host environment reachable (e.g., the dev server / DB / API endpoint comes up and answers).
   - E2E → launch app + verify main view loads.
4. **Wire the stack's standard task entry points** for each tier (one invocation per tier, e.g., `npm test`, `npm run test:integration`, `npm run test:e2e`).
5. **Verify tier isolation** — tests in one tier do not interfere with others (separate temp dirs, different ports, distinct config files where needed).

Pull concrete file names, commands, and host-specific flags from `architecture.md` Test Strategy's setup notes when present. This file stays stack-agnostic; the architecture decides the ecosystem. When `architecture.md` is absent, derive the minimum configuration consistent with the project's existing stack.
