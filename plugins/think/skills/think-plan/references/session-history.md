# Session History

Session history is stored in a separate file from the working plan file to keep the plan lean.

## File Path

`A4/<topic-slug>.impl-plan.history.md`

## Format

```markdown
---
type: session-history
source: <topic-slug>.impl-plan.md
---

### Session Close — <YYYY-MM-DD HH:mm>

#### Revisions This Session
- Revision N: <what was reflected>

#### Decisions Made
- <key decision — e.g., "chose vertical slice approach over bottom-up">

#### Change Log

| Section | Change | Reason | Source |
|---------|--------|--------|--------|
| <section> | <what changed> | <why> | <interview or review report> |

#### Open Items

| Section | Item | What's Missing | Priority |
|---------|------|---------------|----------|
| <section> | <item> | <gap> | High / Medium / Low |

#### Next Steps
- <suggested work items>

#### Interview Transcript
<details>
<summary>Q&A</summary>

**Q:** <question>
**A:** <answer>

</details>
```

## Rules

- Each session appends a new `### Session Close` entry. Previous entries are preserved — never overwrite them.
- The Change Log records **interview-driven changes only**. Review reflection changes are recorded at reflection time in the working file's revision increment, not duplicated here.
- Open Items and Next Steps are **also maintained in the working file body** for quick access. The history copy preserves the snapshot at session close.
- Use the Write tool to append new entries. Read the existing file first to preserve previous entries.
