# Test Report Persistence

After running integration and smoke tests in Phase 2, write a test report capturing the results.

## File Path

`a4/<topic-slug>.test-report.c<N>.md`

Where `<N>` is the test cycle number (1, 2, 3).

## Frontmatter

```markdown
---
type: test-report
source: <topic-slug>.plan.md
cycle: <N>
revision: <plan revision at time of testing>
tested: <YYYY-MM-DD HH:mm>
---
```

## Template

```markdown
## Test Report — Cycle <N>

**Plan file:** <plan file path>
**Plan revision:** <revision>

### Environment

| Item | Value |
|------|-------|
| App type | <from Launch & Verify> |
| Build command | <from Launch & Verify> |
| Launch command | <from Launch & Verify> |

### Build Status

- **Result:** PASS | FAIL
- **Details:** <build output summary if failed>

### Unit Test Results

- **Result:** PASS | FAIL
- **Passed:** <count>
- **Failed:** <count>
- **Details:** <failure summary if any>

### Integration Test Results

| Test | Result | Details |
|------|--------|---------|
| <test name> | PASS / FAIL | <failure description if failed> |

### Smoke Test Results

| Test | Result | Details |
|------|--------|---------|
| <test name> | PASS / FAIL | <failure description if failed> |

### Failure Analysis

For each failure, record **facts only** — do not classify as plan/arch/usecase. Diagnosis is performed by think-plan after reading this report.

#### <test name>
- **Error:** <error message or behavior>
- **Expected:** <what should have happened>
- **Root cause:** <what the subagent identified as the issue — e.g., "DB connection config missing", "API endpoint returns 404", "component contract mismatch">
- **Attempted fixes:** <what was tried and why it didn't resolve the issue>

### Summary

| Category | Passed | Failed | Total |
|----------|--------|--------|-------|
| Unit | <n> | <n> | <n> |
| Integration | <n> | <n> | <n> |
| Smoke | <n> | <n> | <n> |

**Overall:** PASS | FAIL
```

## Diagnosis

Diagnosis classification (plan / arch / usecase) is **not performed by the subagent**. The subagent records factual results only — what failed, what error occurred, what was tried.

think-plan reads this report and classifies each failure using its knowledge of the architecture and plan context:

- **plan** — the implementation plan has incorrect or missing information (wrong file mapping, missing dependency, incomplete test strategy). Fix by updating the plan.
- **arch** — the architecture document has an issue (incorrect contract, missing component interaction, wrong tech choice). Cannot fix in the plan — requires upstream arch update.
- **usecase** — the use case specification has an issue (ambiguous FR, conflicting requirements, missing edge case). Cannot fix in the plan — requires upstream usecase update.

## Purpose

- Provides factual failure records for think-plan to analyze and classify
- Enables diagnosis-based routing: plan issues are auto-fixed, arch/usecase issues stop the pipeline
- Preserves the testing trail across cycles
- Tracks which reports have been reflected via the plan's `reflected_files` frontmatter
