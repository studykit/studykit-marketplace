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
- Any existing `A4/<topic-slug>.integration-report.r*.md` files (for prior verification results)

## Step 1: Environment Setup

### Read Launch & Verify

Extract from the plan's **Launch & Verify** section:
- App type, build command, launch command, launch URL/view
- Verify tool and fallback
- Smoke scenario

If the plan has no Launch & Verify section, attempt auto-detection using the same procedure as planning-guide → "Launch & Verify Derivation." Ask the user to confirm.

### Install Verification Tools

Based on the verify tool field, ensure the tool is available. If the primary tool fails to install, fall back to the fallback tool. If both fail, inform the user and stop.

## Step 2: Build & Launch

### Build

Run the build command from Launch & Verify. If build fails → report as L1 failure in the integration report and do NOT proceed to launch.

### Launch

Apply the **Test isolation** flags from the plan's Launch & Verify section to the launch command. Run and wait for the app to be ready (timeout: 60 seconds). If the app doesn't become ready → report as L1 failure.

### Full Test Suite

Run the project's test suite and record pass/fail count. Test failures don't block verification — they are reported alongside UI verification results.

## Step 3: FR Verification

This is the core verification step. For **each FR** in the spec, interact with the running application and verify the FR's behavior.

### Verification Procedure

For each FR, in spec order:

1. **Read the FR** — understand User action, System behavior steps, Validation, Error handling.

2. **Navigate to the right view** — using the FR's Screen/View field and the UI Screen Groups.

3. **Perform the User action** using the verification tool.

4. **Check System behavior** — verify each step against the FR's expected behavior (screenshot, read page content).

5. **Record the result**:
   - `PASS` — behavior matches the FR
   - `FAIL` — behavior differs from the FR (describe what happened vs what was expected)
   - `BLOCKED` — cannot test because a prerequisite is missing (e.g., no input box to type in)
   - `SKIP` — FR is non-UI or cannot be verified through the UI tool

### Verification Order

1. **Platform capabilities first** — verify platform FRs (if any) before feature FRs. If the basic interaction loop doesn't work, most feature FRs will be BLOCKED.
2. **Smoke scenario** — verify the smoke scenario from Launch & Verify. If it fails, note which platform capabilities are missing.
3. **Feature FRs** — verify in spec order.

Take screenshots at key verification moments as evidence for the report.

## Step 4: Diagnosis

After all FRs are verified, diagnose each failure using the **Waterfall Trace** — a top-down procedure that checks each pipeline stage in order. Stop at the first stage that fails.

For the full Waterfall Trace procedure, read **`${CLAUDE_SKILL_DIR}/references/waterfall-trace.md`**.

## Step 5: Auto-Fix (Code Issues)

For issues diagnosed as **code**-level:

1. Spawn a `coder` agent with:
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

Generate a fresh report file for every verify run. Do **not** overwrite a previous integration report.

Write the report to `A4/<topic-slug>.integration-report.r<plan-revision>[.<n>].md`.
- Use the source plan file's `revision` from frontmatter.
- If no report exists yet for that revision, write `r<plan-revision>`.
- If a report already exists for that revision, append `.2`, `.3`, etc. like review-report style run preservation.

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

Present a summary table (build status, test suite results, FR pass/fail counts, auto-fixes, issues by stage). For issues requiring upstream fixes, point the user to the relevant skill (`think-spec` or `think-plan` — they detect integration reports automatically).

Clean up any launched dev servers and browser tabs.

## Session Management

The user can pause at any point. Progress is preserved in the generated integration reports — verified FRs stay recorded, auto-fixes stay committed, and each verification run remains auditable.

After reporting, the user decides next steps. Never conclude on your own.
