# bootstrap.md Template (auto-bootstrap Step 6)

Use the `Write` tool with this scaffold for fresh runs. On incremental bootstrap, use `Edit` to touch only the sections that changed and add a footnote marker + `## Changes` entry citing what drove the update (typically `[[architecture]]` when architectural changes triggered re-bootstrap).

```markdown
---
kind: bootstrap
updated: <today>
---

# Bootstrap

> Verifies the dev environment for the architecture in [[architecture]].

## Environment

| Item | Value |
|------|-------|
| Language | <e.g., TypeScript 5.3> |
| Framework | <e.g., Next.js 15> |
| Platform | <e.g., node 20> |
| Package manager | <npm / pnpm / pip / …> |
| Project root | <path relative to git root> |

## Verified Commands

| Command | Purpose | Status |
|---------|---------|--------|
| `npm run build` | Build | PASS |
| `npm run dev` | Launch app | PASS |
| `npm test` | Unit tests | PASS |
| `npm run test:integration` | Integration tests | PASS |
| `npm run test:e2e` | E2E tests | PASS |
| edit → build → test | Dev loop | PASS |

## Test Infrastructure

| Tier | Tool | Version | Config | Minimal Test | Status |
|------|------|---------|--------|--------------|--------|
| Unit | Vitest | 1.6 | `vitest.config.ts` | `tests/smoke.test.ts` | PASS |
| Integration | @vscode/test-electron | 2.5 | `.vscode-test.js` | `tests/integration/activate.test.ts` | PASS |
| E2E | WebdriverIO + wdio-vscode-service | 8.x | `wdio.conf.ts` | `tests/e2e/panel.test.ts` | PASS |

## Test Isolation Flags

| Tier | Flags |
|------|-------|
| Integration | `--disable-extensions`, `--extensions-dir=<tmpdir>` |
| E2E | `--user-data-dir=<tmpdir>`, `--no-sandbox` (CI) |

## Smoke Scenario

<Single minimal user-observable interaction — e.g., "VS Code launches with only the dev extension active; running command `hello.world` shows a toast." This becomes plan's Launch & Verify smoke scenario.>

## Issues

<Only when issues were encountered. Link to the review items emitted above.>

- Architecture issues (`status: open`): [[review/<id>-<slug>]] × N
- Environment issues (`status: resolved`): [[review/<id>-<slug>]] × M
- Environment issues (`status: open`): [[review/<id>-<slug>]] × K

## Changes

[^1]: <today> — [[architecture]]
```
