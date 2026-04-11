---
name: think-verify
description: "This skill should be used when the user needs to verify that an implemented project actually works — launching the application, interacting with its UI, and checking each FR against the running product. Common triggers include: 'verify', 'verify the implementation', 'does it work', 'test the app', 'integration test', 'check if it runs', 'smoke test', 'verify the build'. Also applicable after think-code completes all IUs and the user wants end-to-end verification."
argument-hint: <path to .impl-plan.md or .spec.md file, or topic slug>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskList
---

# Integration Verifier

Takes an implemented project (after think-code) and verifies it works — building the app, launching it, interacting with the UI, and checking each FR against the running product. Produces an integration report and auto-fixes code-level issues.

## Step 0: Input

Resolve the input from **$ARGUMENTS** using the file resolution rules below, then read the files.

If no argument is provided, ask the user for a slug, filename, or path.

### File Resolution

Arguments can be full paths, partial filenames, or slugs. Resolve in order:

1. **Full path** — use directly if the file exists
2. **Partial match** — glob for `A4/*<argument>*.impl-plan.md` and `A4/*<argument>*.spec.md`
3. **Fallback** — if `A4/` does not exist, glob from project root
4. **Multiple matches** — present candidates and ask the user to pick
5. **No match** — inform the user and ask for a different term

After resolution, read:
- The `.impl-plan.md` file (for Launch & Verify, file mappings, Shared Integration Points)
- The `.spec.md` file (for FR list, UI Screen Groups, platform capabilities)
- Any existing `.integration-report.md` (for prior verification results)

## Step 1: Environment Setup

### Read Launch & Verify

Extract from the plan's **Launch & Verify** section:
- App type, build command, launch command, launch URL/view
- Verify tool and fallback
- Smoke scenario

If the plan has no Launch & Verify section, attempt auto-detection using the same procedure as planning-guide → "Launch & Verify Derivation." Ask the user to confirm.

### Install Verification Tools

Based on the verify tool field, ensure the tool is available:

| Tool | Check | Install |
|------|-------|---------|
| Playwright CLI | `npx @playwright/cli --version` | `npm i -g @playwright/cli && npx playwright install` |
| Playwright MCP | `npx @playwright/mcp --version` | `npm i -g @playwright/mcp` |
| WebdriverIO + wdio-vscode-service | `npx wdio --version` | `npm i -D @wdio/cli wdio-vscode-service` |
| chrome MCP | Already available in Claude Code | — |
| computer-use MCP | Already available in Claude Code | — |

If the primary tool fails to install, fall back to the fallback tool. If both fail, inform the user and stop.

## Step 2: Build & Launch

### Build

Run the build command from Launch & Verify:

```bash
<build command>  # e.g., npm run compile
```

If build fails → report as L1 failure in the integration report. Attempt to diagnose (read error output). Do NOT proceed to launch.

### Launch

Run the launch command and wait for the app to be ready:

| App Type | Launch | Ready Signal |
|----------|--------|-------------|
| Web app | `<launch command>` (background) | HTTP response from launch URL |
| VS Code Extension | `code --extensionDevelopmentPath=.` | Extension Host window opens |
| Electron | `<launch command>` (background) | Window appears |
| API service | `<launch command>` (background) | HTTP response from health/root endpoint |
| CLI | N/A (run per test) | N/A |

Timeout: 60 seconds. If the app doesn't become ready → report as L1 failure.

### Full Test Suite

Run the project's test suite (test runner identified from plan's codebase context):

```bash
<test runner command>  # e.g., npm test, pytest, ./gradlew test
```

Record pass/fail count. Test failures don't block verification — they are reported alongside UI verification results.

## Step 3: FR Verification

This is the core verification step. For **each FR** in the spec, interact with the running application and verify the FR's behavior.

### Verification Procedure

For each FR, in spec order:

1. **Read the FR** — understand User action, System behavior steps, Validation, Error handling.

2. **Navigate to the right view** — using the FR's Screen/View field and the UI Screen Groups.

3. **Perform the User action** — using the verification tool:
   - Playwright CLI: `playwright-cli click`, `playwright-cli type`, etc.
   - WebdriverIO: Execute test script
   - chrome MCP: `navigate`, `form_input`, `find`, `click`, etc.
   - computer-use MCP: `screenshot`, `left_click`, `type`, etc.

4. **Check System behavior** — verify each step:
   - Take a screenshot after each significant interaction
   - Read page content / accessibility tree
   - Compare against the FR's expected behavior

5. **Record the result**:
   - `PASS` — behavior matches the FR
   - `FAIL` — behavior differs from the FR (describe what happened vs what was expected)
   - `BLOCKED` — cannot test because a prerequisite is missing (e.g., no input box to type in)
   - `SKIP` — FR is non-UI or cannot be verified through the UI tool

### Verification Order

1. **Platform capabilities first** — verify platform FRs (if any) before feature FRs. If the basic interaction loop doesn't work, most feature FRs will be BLOCKED.
2. **Smoke scenario** — verify the smoke scenario from Launch & Verify. If it fails, note which platform capabilities are missing.
3. **Feature FRs** — verify in spec order.

### Screenshot Evidence

Take screenshots at key moments:
- Initial state of each view
- After performing the user action
- After system response
- On unexpected behavior

Reference screenshots in the report as evidence.

## Step 4: Diagnosis

After all FRs are verified, diagnose each failure using the **Waterfall Trace** — a top-down procedure that checks each pipeline stage in order. Stop at the first stage that fails.

### Waterfall Trace Procedure

For each FAIL or BLOCKED result:

**Step 4.1: Does an FR exist for this capability?**

Search the spec's FR list for an FR that covers the failed behavior.

- If **no FR found** → **SPEC issue** (missing FR or missing platform capability).
  - Check: is this a platform capability assumed by multiple FRs? (e.g., message input, conversation display)
  - Check: was this excluded in the usecase's Excluded Ideas as "basic behavior"?
  - Recommended fix: add FR to spec.
  - **Stop here.** Do not check plan or code — there's nothing to implement without an FR.

**Step 4.2: Does an IU cover this FR?**

Find the IU(s) assigned to this FR in the plan.

- If **no IU covers the FR** → **PLAN issue** (FR not mapped to any IU).
  - Recommended fix: assign FR to an existing or new IU.
  - **Stop here.**

**Step 4.3: Are the IU's instructions sufficient?**

Read the IU's description, file mapping, and acceptance criteria. Check whether they adequately describe the work needed for this FR to function:

- Does the file mapping include all necessary files? (e.g., HTML entry point, component mount file)
- Does the description specify integration behavior? (e.g., "mount in DOM" vs just "wire up handlers")
- If a Shared Integration Points table exists, does it describe this IU's contribution to shared files?
- Do the acceptance criteria include an end-to-end verification scenario?

- If **IU instructions are insufficient** → **PLAN issue** (IU scope or detail gap).
  - Recommended fix: expand IU description, file mapping, or Shared Integration Points.
  - **Stop here.**

**Step 4.4: Does the code match the IU instructions?**

Read the actual implementation files. Check whether the code does what the IU says:

- Are the files listed in the file mapping created/modified as described?
- Does the component exist but is it not imported/mounted/registered?
- Is the logic correct but the wiring missing?
- Is there a runtime error visible in console/logs?

- If **code doesn't match IU** → **CODE issue** (implementation bug or integration oversight).
  - Recommended fix: specific code change (mount component, fix import, register handler, etc.).

### Diagnosis Summary

| Trace Step | Check | Failure → Stage |
|-----------|-------|----------------|
| 4.1 | FR exists in spec? | No → **spec** |
| 4.2 | IU covers FR in plan? | No → **plan** |
| 4.3 | IU instructions sufficient? | No → **plan** |
| 4.4 | Code matches IU? | No → **code** |

### Example: visual-claude

| Failure | 4.1 FR? | 4.2 IU? | 4.3 Sufficient? | 4.4 Code? | Verdict |
|---------|---------|---------|-----------------|-----------|---------|
| No message input | ❌ No FR | — | — | — | **spec** |
| Sidebar not visible | ✅ FR-9 | ✅ IU-7 | ❌ "Wire up" without mount detail | — | **plan** |
| Diagram render crash | ✅ FR-1 | ✅ IU-2 | ✅ Sufficient | ❌ Wrong CLI path | **code** |

For each diagnosed issue, record:
- What failed (FR reference + description)
- Which trace step identified the root cause (4.1 / 4.2 / 4.3 / 4.4)
- Root cause (what's missing or wrong)
- Responsible stage (spec / plan / code)
- Recommended fix (specific and actionable)

## Step 5: Auto-Fix (Code Issues)

For issues diagnosed as **code**-level:

1. Spawn a `code-executor` agent with:
   - The specific issue description
   - The relevant IU context from the plan
   - The fix to apply (e.g., "mount ConversationView in main.ts")
   - Shared Integration Points for the affected files

2. After the fix, **re-verify the affected FR** (not all FRs — just the one that failed).

3. If the fix works → mark as FIXED in the report.

4. If the fix doesn't work → try once more (different approach).

5. After 2 failed fix attempts → escalate to plan/spec level in the report.

**Maximum auto-fix attempts per issue: 2**

## Step 6: Integration Report

Write the report to `A4/<topic-slug>.integration-report.md`.

### Report Format

Read `${CLAUDE_SKILL_DIR}/references/integration-report.md` for the exact template.

The report includes:
- **Environment** — app type, build/launch commands, tools used
- **Build & Test Status** — build pass/fail, test suite results
- **FR Verification** — per-FR status with evidence
- **Diagnosis** — per-issue root cause and responsible stage
- **Auto-Fix Attempts** — what was tried and results
- **Summary** — pass/fail counts, issues by stage

### Commit

Stage and commit the report:
```
verify(<topic-slug>): integration report

- FRs verified: N / M
- Passed: P
- Code fixes applied: F
- Spec issues: S
- Plan issues: L
```

## Step 7: Report to User

Present the results:

> **Integration Verification Complete**
>
> | Category | Result |
> |----------|--------|
> | Build | PASS |
> | Test suite | 413/413 pass |
> | FRs verified | 15/17 |
> | FRs passed | 12/15 |
> | Auto-fixed | 2 |
> | Spec issues | 1 (missing platform FR) |
>
> **Issues requiring upstream fixes:**
> 1. [spec] No FR for conversation input UI — 8 FRs blocked
>
> Report saved to `A4/<topic-slug>.integration-report.md`
>
> To fix spec issues, run `think-spec` — it will detect this report automatically.
> To fix plan issues, run `think-plan` — it will detect this report automatically.

## Cleanup

After verification is complete (or on error), clean up:
- Stop any launched dev servers / app processes
- Close any opened browser tabs or application windows

## Tool Selection Reference

### Web Apps (Playwright CLI)

```bash
# Navigate
playwright-cli open http://localhost:3000

# Interact
playwright-cli click "Submit button"
playwright-cli type "Hello world" --element "Message input"
playwright-cli screenshot --output evidence-fr1.png

# Read
playwright-cli get-text "#response-area"
```

### VS Code Extensions (WebdriverIO)

Write a minimal test script, execute with wdio:
```javascript
// verify-extension.test.ts
describe('Extension Verification', () => {
  it('should open panel and show UI', async () => {
    const workbench = await browser.getWorkbench();
    await workbench.executeCommand('Visual Claude: Open Panel');
    // Verify webview content
  });
});
```

### Desktop / Native (computer-use MCP)

```
screenshot → identify elements → left_click → type → screenshot → verify
```

### Fallback: chrome MCP (already available)

```
navigate → read_page → form_input → find → screenshot → verify
```

## Session Management

The user can pause at any point. Progress is preserved in the integration report — verified FRs stay recorded, auto-fixes stay committed.

After reporting, the user decides next steps. Never conclude on your own.
