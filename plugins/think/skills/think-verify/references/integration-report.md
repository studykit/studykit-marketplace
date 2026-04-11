# Integration Report Template

## File Path

`A4/<topic-slug>.integration-report.md`

## Frontmatter

```yaml
---
type: integration-report
pipeline: co-think
topic: "<topic>"
created: <YYYY-MM-DD HH:mm>
status: pass | fail
sources:
  - file: <topic-slug>.spec.md
    revision: <spec revision>
    sha: <git hash-object>
  - file: <topic-slug>.impl-plan.md
    revision: <plan revision>
    sha: <git hash-object>
fix_commits: []      # git hashes of auto-fix commits
---
```

## Template

```markdown
# Integration Report: <topic>
> Sources: [spec](./<topic-slug>.spec.md) | [plan](./<topic-slug>.impl-plan.md)

## Environment

| Item | Value |
|------|-------|
| App type | <from plan's Launch & Verify> |
| Build command | <command> |
| Build status | PASS / FAIL |
| Launch command | <command> |
| Launch status | PASS / FAIL |
| Verify tool | <tool used> |
| Test suite | <pass count> / <total count> |

## FR Verification

### Platform Capabilities

| FR | Description | Status | Evidence |
|----|------------|--------|----------|
| (platform) | <description> | PASS / FAIL / MISSING | <screenshot ref or description> |

### Feature FRs

| FR | Description | Verification | Status | Evidence |
|----|------------|-------------|--------|----------|
| FR-1 | <title> | <what was tested> | PASS / FAIL / BLOCKED / SKIP | <screenshot ref or description> |
| FR-2 | <title> | <what was tested> | PASS / FAIL / BLOCKED / SKIP | <evidence> |

### Status Summary

| Status | Count | FRs |
|--------|-------|-----|
| PASS | N | FR-1, FR-3, ... |
| FAIL | N | FR-5, ... |
| BLOCKED | N | FR-2, FR-7, ... (blocked by: <reason>) |
| SKIP | N | FR-8 (non-UI) |

## Diagnosis

| # | Issue | Root Cause | Stage | Recommended Fix |
|---|-------|-----------|-------|----------------|
| 1 | <what failed> | <why it failed> | spec / plan / code | <specific fix> |
| 2 | ... | ... | ... | ... |

### Stage Summary

| Stage | Issues | Description |
|-------|--------|-------------|
| spec | N | <brief: missing FRs, ambiguous behavior, etc.> |
| plan | N | <brief: missing integration points, etc.> |
| code | N | <brief: mounting issues, handler bugs, etc.> |

## Auto-Fix Attempts

| # | Issue | Fix Applied | Attempt | Result | Commit |
|---|-------|------------|---------|--------|--------|
| 1 | <issue> | <what was changed> | 1/2 | FIXED / FAILED | <hash> |
| 2 | <issue> | <what was changed> | 1/2 | FIXED / FAILED | <hash> |
| 3 | <issue> | <escalated after 2 attempts> | — | ESCALATED | — |

## Summary

- **Status:** PASS / FAIL
- **FRs verified:** N / M
- **Passed:** P / N
- **Failed:** F / N
- **Blocked:** B / N
- **Skipped:** S / N
- **Code fixes applied:** X
- **Code fixes failed:** Y (escalated)
- **Spec issues:** Z
- **Plan issues:** W

## Upstream Actions Required

### Spec Issues
> To address these, run `think-spec` on the spec file. It will detect this report during iteration entry.

- [ ] <issue description — what FR to add or modify>

### Plan Issues
> To address these, run `think-plan` on the plan file. It will detect this report during iteration entry.

- [ ] <issue description — what integration point or IU to fix>
```

## Required Sections

- Environment
- FR Verification (with Platform Capabilities and Feature FRs sub-sections)
- Diagnosis
- Summary

## Conditional Sections

- Auto-Fix Attempts — only if auto-fixes were attempted
- Upstream Actions Required — only if spec or plan issues were found
