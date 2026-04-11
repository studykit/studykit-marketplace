# Session History

Session history records each scaffold execution for auditability.

## File Path

`A4/<topic-slug>.scaffold.history.md`

## Format

```markdown
---
type: session-history
source: <topic-slug>.scaffold.md
---

### Scaffold Run — <YYYY-MM-DD HH:mm>

#### Source
- Arch file: <topic-slug>.arch.md (revision N, sha: <hash>)

#### Mode
- Fresh scaffold / Incremental (changes: <what changed in arch>)

#### Actions Taken
- <what was created/modified/installed>

#### Verification Results
| Check | Result |
|-------|--------|
| Build | PASS / FAIL |
| Run | PASS / FAIL |
| Unit tests | PASS / FAIL |
| Integration tests | PASS / FAIL |
| E2E tests | PASS / FAIL |
| Dev loop | PASS / FAIL |

#### Issues
- <issue and resolution, if any>

#### Commit
- <git hash>
```

## Rules

- Each scaffold execution appends a new `### Scaffold Run` entry. Previous entries are preserved.
- Use the Write tool to append new entries. Read the existing file first to preserve previous entries.
