# Session History

Session history captures autonomous decisions and quality round changes so that `think-plan` can pick up context when iterating on auto-plan output.

## File Path

`A4/<topic-slug>.plan.history.md`

## Format

```markdown
---
type: session-history
source: <topic-slug>.plan.md
---

### Compose — <YYYY-MM-DD HH:mm>

#### Strategy Decision
- **Chosen:** <strategy name>
- **Reason:** <why this strategy was selected over alternatives>

#### Unit Summary
- Total units: <count>
- UC coverage: <covered> / <total>

#### Key Decisions
- <autonomous decision — e.g., "split auth into two units because token refresh has no shared state with login">
- <autonomous decision — e.g., "assigned ambiguous UC-7 to unit 3 based on component overlap">

#### Open Items at Compose
- <items recorded as needing user review>

---

### Quality Round <N> — <YYYY-MM-DD HH:mm>

#### Review Verdict
- **Result:** NEEDS_REVISION | ACTIONABLE
- **Issues found:** <count>

#### Changes Applied
| Unit / Section | Change | Reason |
|----------------|--------|--------|
| <unit or section> | <what changed> | <why — from review report> |

#### Decisions Made
- <decision during revision — e.g., "merged units 2 and 3 to resolve circular dependency">

#### Remaining Issues
- <unresolved items carried forward>
```

## Rules

- **Compose entry** is written once after Step 7 (initial plan creation).
- **Quality round entries** are appended after each revision in Step 10. Rounds with verdict `ACTIONABLE` record only the verdict — no changes table.
- Previous entries are preserved — never overwrite them.
- Use the Write tool to append new entries. Read the existing file first to preserve previous entries.
- Keep entries concise. The goal is decision rationale, not a full diff.
