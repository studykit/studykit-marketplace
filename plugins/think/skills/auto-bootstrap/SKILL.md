---
name: auto-bootstrap
description: "This skill should be used when the user needs to set up a development base from an architecture document — project structure, dependencies, build configuration, and test infrastructure for each tier. Common triggers include: 'bootstrap', 'set up the project', 'bootstrap the project', 'create the dev environment', 'set up testing'. Also applicable after think-arch finalizes and before think-plan starts."
argument-hint: <path to .arch.md file>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, WebFetch, TaskCreate, TaskUpdate, TaskList
---

# Project Bootstrap

Takes an architecture document (from think-arch) and sets up a working development base — project structure, dependencies, build configuration, and test infrastructure for each tier. This skill runs autonomously with no user interaction during execution. It produces a bootstrap report that think-plan reads as verified input.

## What This Skill Does

1. Sets up project structure, installs dependencies, configures build
2. Sets up test infrastructure for each tier defined in the architecture's Test Strategy
3. Verifies everything works: build, run, test runners, dev loop
4. Reports results with verified commands that downstream skills use as-is

## What This Skill Does NOT Do

- Implement any use case or feature logic
- Create feature tests
- Make architecture decisions — all decisions come from the `.arch.md`

## Step 0: Input

Resolve the input from **$ARGUMENTS**.

If no argument is provided, ask the user for a slug, filename, or path.

### File Resolution

1. **Full path** — use directly if the file exists
2. **Partial match** — glob for `A4/*<argument>*.arch.md`
3. **Fallback** — if `A4/` does not exist, glob from project root
4. **Multiple matches** — present candidates and ask the user to pick
5. **No match** — inform the user and ask for a different term

After resolution, read the `.arch.md` file. Extract:
- **Technology Stack** — language, framework, platform
- **Component structure** — component names, data stores
- **Test Strategy** — tier-by-tier tool selections with setup notes
- **External Dependencies** — what needs to be installed or configured

Also read the source `.usecase.md` (from arch frontmatter `sources`) for project context.

## Step 1: Codebase Assessment

Check whether a codebase already exists:

- **No existing code** → fresh bootstrap (Step 2)
- **Existing code** → incremental bootstrap. Identify what's already in place (project structure, dependencies, build config, test setup) and what's missing. Only set up what's needed.

## Step 2: Project Structure

Based on the Technology Stack and Component structure:

1. **Create directory structure** following framework conventions
2. **Initialize project files** — package.json / pyproject.toml / Cargo.toml / etc.
3. **Install dependencies** from the Technology Stack and External Dependencies
4. **Configure build** — tsconfig, esbuild, webpack, vite, etc.
5. **Create entry point** — minimal app that starts without error

**Minimal app criteria:** The entry point must produce a running application, not just compile. For a web app, the dev server starts and serves a page. For a VS Code extension, the extension activates and opens a panel. For a CLI, the command runs and exits cleanly. For an API, the server starts and responds to a health check.

## Step 3: Test Infrastructure

For each tier in the architecture's Test Strategy:

1. **Install test dependencies** — test runner, assertion library, any plugins
2. **Create configuration** — test runner config file (vitest.config.ts, .vscode-test.js, wdio.conf.ts, etc.)
3. **Write a minimal passing test** — one test per tier that proves the runner works:
   - **Unit:** import a module, assert true
   - **Integration:** if host environment (e.g., VS Code Extension Host), verify the app activates
   - **E2E:** if UI exists, launch the app and verify the main view loads
4. **Add npm scripts** (or equivalent) for each tier — `test`, `test:integration`, `test:e2e`
5. **Verify isolation** — test tiers don't interfere with each other

Use the Test Strategy's **special setup notes** from the arch. If a tool requires specific configuration (e.g., `--disable-extensions` for VS Code, temp user data dir), apply it.

## Step 4: Verification

Run all checks and record results:

### 4.1: Build

```
Run build command → SUCCESS / FAIL (with error)
```

### 4.2: Run

```
Launch app → starts without error → SUCCESS / FAIL (with error)
```

For apps that stay running (dev servers, extensions), verify startup then clean up.

### 4.3: Test Runners

For each tier:
```
Run test command → minimal test passes → SUCCESS / FAIL (with error)
```

### 4.4: Dev Loop

```
Make a trivial code change → rebuild → run tests → SUCCESS / FAIL
```

This verifies the edit → build → test cycle works end-to-end.

## Step 5: Bootstrap Report

Generate the bootstrap report. Read `${CLAUDE_SKILL_DIR}/references/bootstrap-report.md` for the exact template.

The report includes:
- **Environment** — technology stack, project structure summary
- **Verified Commands** — build, run, and test commands that actually work (think-plan reads these directly for Launch & Verify)
- **Test Infrastructure** — per-tier setup status with tool versions
- **Verification Results** — pass/fail for each check
- **Issues** — any problems found, with stage attribution (arch / environment)

### Commit

Stage and commit all bootstrap files:
```
bootstrap(<topic-slug>): initial project setup

- Build: PASS/FAIL
- Test tiers: N/M passing
- Dev loop: PASS/FAIL
```

## Step 6: Feedback

If any verification step fails:

1. **Diagnose** — determine whether the issue is:
   - **arch** — architecture's technology choice or test tool selection is incompatible (e.g., WebdriverIO doesn't support the VS Code version)
   - **environment** — local environment issue (e.g., missing Java for PlantUML, no display server for E2E)

2. **Do not attempt to fix arch issues** — these require architecture decisions. Record and move on.

3. **Research before fixing environment issues** — do not guess from error messages alone. Before attempting a fix:
   a. **Spawn an api-researcher agent** — launch an `Agent(subagent_type: "api-researcher")` with the error message, relevant config files, and the technology stack. The agent should:
      - Search API/library documentation via `chub` first, then fall back to `WebSearch`/`WebFetch`
      - Read library source code when documentation is insufficient (e.g., checking default config, supported options, version-specific behavior)
      - Check version-specific notes, known issues, and migration guides
      - Write findings to `A4/<topic-slug>.bootstrap.research-<label>.md` per the format below. `<label>` is a short slug describing the issue (e.g., `jest-esm-flags`, `esbuild-target-mismatch`)
   b. **Apply the fix** based on the research agent's findings, not assumptions.
   c. **Re-verify** after fix.
   d. If the fix fails, spawn a new api-researcher agent with the updated error — do not retry the same fix.

4. **Record in report** — issues with `Stage: arch` become upstream feedback for think-arch. Issues with `Stage: environment` are recorded with a reference to the research report that informed the fix.

Research reports use the format in `${CLAUDE_SKILL_DIR}/references/research-report-format.md`.

## Iteration

When re-run on an existing bootstrap (e.g., after arch changes):

1. **Archive the current report** — rename `A4/<slug>.bootstrap.md` to `A4/<slug>.bootstrap.r<current-revision>.md` before writing the new report. This preserves the previous result as-is.
2. Read the archived report's frontmatter `sources`
3. Diff the current `.arch.md` against the archived report's source SHA
4. Identify what changed (new test tier, different tool, new dependency)
5. Apply only the incremental changes
6. Re-verify all checks
7. Write the new report to `A4/<slug>.bootstrap.md` with incremented revision

## Session Management

This skill runs autonomously. No user interaction during execution. The user invokes it and receives the bootstrap report when done.

If a verification step fails and cannot be auto-fixed, the report documents the failure. The user decides next steps based on the report.

## Next Step

After reporting results, suggest the next pipeline step:

> The dev environment is ready. The next step is `think-plan` to generate an implementation plan and build from the architecture.
>
> Run: `/think:think-plan <slug>`

If the bootstrap has unresolved `Stage: arch` issues, suggest `think-arch` first to address architecture-level problems before planning.
