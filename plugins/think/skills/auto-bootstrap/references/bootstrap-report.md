# Bootstrap Report Template

## File Path

- **Current report:** `A4/<topic-slug>.bootstrap.md`
- **Archived reports:** `A4/<topic-slug>.bootstrap.r<N>.md` (e.g., `.bootstrap.r0.md`, `.bootstrap.r1.md`)

On iteration, the existing report is renamed to `.bootstrap.r<current-revision>.md` before the new report is written. The `.bootstrap.md` file always contains the latest result.

## Frontmatter

```yaml
---
type: bootstrap-report
topic: "<topic>"
created: <YYYY-MM-DD HH:mm>
revised: <YYYY-MM-DD HH:mm>
revision: 0
status: pass | fail
sources:
  - file: <topic-slug>.arch.md
    revision: <arch revision>
    sha: <git hash-object>
bootstrap_commit: <git hash of bootstrap commit>
---
```

## Template

```markdown
# Bootstrap Report: <topic>
> Source: [<arch-file-name>](./<arch-file-name>)

## Environment

| Item | Value |
|------|-------|
| Language | <from arch Technology Stack> |
| Framework | <from arch Technology Stack> |
| Platform | <from arch Technology Stack> |
| Package manager | <npm / pip / cargo / etc.> |
| Project root | <path> |

## Project Structure

```
<directory tree of created files, depth 2-3>
```

## Verified Commands

| Command | Purpose | Status |
|---------|---------|--------|
| `<build command>` | Build | PASS / FAIL |
| `<run command>` | Launch app | PASS / FAIL |
| `<unit test command>` | Unit tests | PASS / FAIL |
| `<integration test command>` | Integration tests | PASS / FAIL |
| `<e2e test command>` | E2E tests | PASS / FAIL |
| `<dev loop>` | Edit → build → test cycle | PASS / FAIL |

## Test Infrastructure

| Tier | Tool | Version | Config File | Test File | Status |
|------|------|---------|-------------|-----------|--------|
| Unit | <e.g., Vitest> | <version> | <config path> | <test path> | PASS / FAIL |
| Integration | <e.g., @vscode/test-electron> | <version> | <config path> | <test path> | PASS / FAIL |
| E2E | <e.g., WebdriverIO> | <version> | <config path> | <test path> | PASS / FAIL |

## Verification Results

### Build
- Command: `<command>`
- Result: PASS / FAIL
- Output: <summary or error>

### Run
- Command: `<command>`
- Result: PASS / FAIL
- Output: <summary or error>

### Test Runners

#### Unit
- Command: `<command>`
- Result: PASS / FAIL — <N> tests
- Output: <summary or error>

#### Integration
- Command: `<command>`
- Result: PASS / FAIL — <N> tests
- Output: <summary or error>

#### E2E
- Command: `<command>`
- Result: PASS / FAIL — <N> tests
- Output: <summary or error>

### Dev Loop
- Change: <what was modified>
- Rebuild: PASS / FAIL
- Retest: PASS / FAIL

## Issues

| # | Issue | Stage | Research | Auto-fix | Result |
|---|-------|-------|----------|----------|--------|
| 1 | <description> | arch / environment | [research-<label>.md](./<slug>.bootstrap.research-<label>.md) or — | <what was tried> | FIXED / UNFIXED |

### Upstream Feedback (arch issues)

- [ ] <issue description — what needs to change in the architecture>

## Summary

- **Status:** PASS / FAIL
- **Build:** PASS / FAIL
- **Run:** PASS / FAIL
- **Test tiers:** <N> / <M> passing
- **Dev loop:** PASS / FAIL
- **Arch issues:** <count>
- **Environment issues:** <count> (<fixed count> auto-fixed)
```

## Required Sections

- Environment
- Verified Commands
- Test Infrastructure
- Verification Results
- Summary

## Conditional Sections

- Issues — only if issues were found
- Upstream Feedback — only if arch-level issues were found
- Project Structure — only on fresh bootstrap (not incremental)

## Purpose

- Provides **verified facts** for think-plan's Launch & Verify section
- Preserves the exact commands that work — no guessing
- Enables think-arch to receive structured feedback on architecture issues
- Each bootstrap run is preserved as its own artifact via revision tracking
