# bootstrap.md Template (auto-bootstrap Step 6)

Use the `Write` tool with this scaffold for fresh runs. On incremental bootstrap, use `Edit` to touch only the sections that changed and append a `## Change Logs` bullet citing what drove the update (typically `[architecture](architecture.md)` when architectural changes triggered re-bootstrap).

`references/bootstrap-authoring.md` requires `## Environment`, `## Launch`, `## Verify`. `## Change Logs` is optional but written whenever a change cites a causing wiki/issue.

````markdown
---
type: bootstrap
updated: <today>
---

## Environment

Verifies the dev environment for the architecture in [architecture](architecture.md).

| Item | Value |
|------|-------|
| Language | <e.g., TypeScript 5.3> |
| Framework | <e.g., Next.js 15> |
| Platform | <e.g., node 20> |
| Package manager | <npm / pnpm / pip / …> |
| Project root | <path relative to git root> |

### Test Infrastructure

| Tier | Tool | Version | Config | Minimal Test | Status |
|------|------|---------|--------|--------------|--------|
| Unit | Vitest | 1.6 | `vitest.config.ts` | `tests/smoke.test.ts` | PASS |
| Integration | @vscode/test-electron | 2.5 | `.vscode-test.js` | `tests/integration/activate.test.ts` | PASS |
| E2E | WebdriverIO + wdio-vscode-service | 8.x | `wdio.conf.ts` | `tests/e2e/panel.test.ts` | PASS |

## Launch

| Command | Purpose | Status |
|---------|---------|--------|
| `npm run build` | Build | PASS |
| `npm run dev` | Launch app | PASS |

## Verify

### Verified Commands

| Command | Purpose | Status |
|---------|---------|--------|
| `npm test` | Unit tests | PASS |
| `npm run test:integration` | Integration tests | PASS |
| `npm run test:e2e` | E2E tests | PASS |
| edit → build → test | Dev loop | PASS |

### Test Isolation Flags

| Tier | Flags |
|------|-------|
| Integration | `--disable-extensions`, `--extensions-dir=<tmpdir>` |
| E2E | `--user-data-dir=<tmpdir>`, `--no-sandbox` (CI) |

### Smoke Scenario

<Single minimal user-observable interaction — e.g., "VS Code launches with only the dev extension active; running command `hello.world` shows a toast." This becomes the project's smoke scenario, read by `/a4:run`.>

### Issues

<Only when issues were encountered. Link to the review items emitted above.>

- Architecture issues (`status: open`): [review/<id>-<slug>](review/<id>-<slug>.md) × N
- Environment issues (`status: resolved`): [review/<id>-<slug>](review/<id>-<slug>.md) × M
- Environment issues (`status: open`): [review/<id>-<slug>](review/<id>-<slug>.md) × K

## Change Logs

- <today> — [architecture](architecture.md)
````
