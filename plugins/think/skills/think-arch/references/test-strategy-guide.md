# Test Strategy Guide

Detailed procedure for selecting test tools per tier based on the technology stack.

## Tier Identification

Every project needs at least a unit test tier. Integration and E2E tiers depend on the architecture:

| Architecture Signal | Integration Tier Needed | E2E Tier Needed |
|-------------------|:-:|:-:|
| Components communicate across process boundaries (postMessage, HTTP, IPC) | Yes | Yes |
| UI layer exists (webview, browser, native) | — | Yes |
| Host environment APIs (VS Code API, Electron API, browser APIs) | Yes | — |
| External service dependencies | Yes | — |
| Single-process, no UI (CLI, library) | — | — |

## Tool Selection

Select tools based on app type. Use the table in SKILL.md Phase 4 as the starting point, then verify each choice:

### Verification Checklist

For each selected tool:
1. **Version compatibility** — does the tool work with the project's language/framework version?
2. **Platform support** — does the tool run on the target platform(s)?
3. **Layer access** — can the tool reach the layer it needs to test? (e.g., can WebdriverIO access VS Code webview iframes?)
4. **Existing dependencies** — is a compatible tool already installed in the project?

Use Technical Claim Verification (in SKILL.md) for any non-obvious compatibility claim.

## Recording

For each tier, record:
- **Tool name and version constraint** (e.g., `@vscode/test-electron@^2.5`)
- **What it tests** — which layer/boundary
- **Rationale** — why this tool over alternatives
- **Special setup notes** — anything auto-scaffold needs to know (e.g., "requires Java for PlantUML", "needs display server for E2E")
