# Plan History

Append-only event log tracking all state changes across the plan lifecycle.

## File Path

`A4/<topic-slug>.plan.history.md`

## Frontmatter

```yaml
---
type: plan-history
source: <topic-slug>.plan.md
---
```

## Format

Events are grouped by phase. Each event records a timestamp, event type, revision, and summary.

```markdown
### Phase 1 — Plan Review

#### r1 — <YYYY-MM-DD HH:mm>
- **Event:** Plan created
- **Revision:** 1
- **Summary:** <IU count, FR coverage, component coverage>

#### r2 — <YYYY-MM-DD HH:mm>
- **Event:** Review reflected
- **Revision:** 2
- **Report:** <slug>.plan.review-r1.md
- **Changes:** <what was fixed — e.g., "FR-3 test coverage added, IU-4 dependency corrected">

#### r3 — <YYYY-MM-DD HH:mm>
- **Event:** Verification passed
- **Revision:** 3

### Phase 2 — Implement & Test

#### c1 — <YYYY-MM-DD HH:mm>
- **Event:** Implementation complete + unit tests passed
- **Revision:** 4

#### c1 — <YYYY-MM-DD HH:mm>
- **Event:** Integration/smoke test failed
- **Report:** <slug>.test-report.c1.md
- **Diagnosis:** <plan | arch | usecase> — <brief description>
- **Changes:** <what was updated in the plan>

#### c2 — <YYYY-MM-DD HH:mm>
- **Event:** Implementation complete + unit tests passed
- **Revision:** 5

#### c2 — <YYYY-MM-DD HH:mm>
- **Event:** All tests passed
- **Revision:** 6
- **Status:** complete
```

## Event Types

| Event | When |
|-------|------|
| Plan created | Phase 1 Step 3 — initial plan generation |
| Review reflected | Phase 1 Step 4 — after auto-reflecting reviewer findings |
| Verification passed | Phase 1 — all review rounds pass |
| Blocked (arch/usecase) | Phase 1 or 2 — upstream issue detected |
| Implementation complete | Phase 2 Step 5 — code + unit tests pass |
| Integration/smoke test failed | Phase 2 Step 6 — test report written |
| Test reflected | Phase 2 Step 7 — plan updated from test failures |
| All tests passed | Phase 2 — final success |
| Cycle exhausted | Phase 2 — 3 cycles without passing |

## Rules

- Each event appends a new entry. Previous entries are never overwritten.
- Use the Edit tool to append new entries. Read the existing file first to preserve previous content.
- Group entries under the current phase heading. If the phase changes, add a new phase heading.
- The `r<N>` prefix denotes review rounds (Phase 1). The `c<N>` prefix denotes test cycles (Phase 2).
