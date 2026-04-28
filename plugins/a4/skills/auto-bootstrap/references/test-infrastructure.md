# Test Infrastructure Setup

For each tier in Test Strategy:

1. **Install test dependencies** (runner + assertion lib + plugins).
2. **Create test configuration file** (`vitest.config.ts`, `.vscode-test.js`, `wdio.conf.ts`, etc.).
3. **Write one minimal passing test per tier**:
   - unit → import + assert true
   - integration → verify host environment reachable
   - E2E → launch app + verify main view loads
4. **Add package scripts** (`test`, `test:integration`, `test:e2e`) or equivalent.
5. **Verify tier isolation** — tests in one tier do not interfere with others.

Use Test Strategy's **setup notes** from `architecture.md` when present. Apply specific flags — e.g., `--disable-extensions` for VS Code, temp user-data-dir for Electron.
