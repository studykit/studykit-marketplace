# Reviewer Output — Per-Finding Review Items

The `usecase-reviewer` agent no longer writes a single aggregated review report. Instead, it writes **one markdown file per finding** into `a4/review/<id>-<slug>.md`, matching the review-item schema documented in the `spec-as-wiki-and-issues` spec.

## Per-Item File Format

Frontmatter:

```yaml
---
type: review
id: <allocated via scripts/allocate_id.py>
kind: finding | gap | question
status: open
target: [usecase/<id>-<slug>, <wiki basenames as needed>]   # [] for cross-cutting
source: usecase-reviewer
priority: high | medium | low
title: "<short finding title>"
labels: []
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---
```

Body structure (per `references/review-authoring.md` — `<description>` required, `<log>` and `<change-logs>` optional):

```markdown
<description>

> Review run: <YYYY-MM-DD HH:mm>

**Summary.** One-paragraph statement of the issue.

**Evidence.** Quote the specific UC lines, actor table row, or wiki section that demonstrate the issue. Reference the target via standard markdown link — `[usecase/<id>-<slug>](../usecase/<id>-<slug>.md)`.

**Suggestion.** Concrete, user-level suggestion for the fix. Do not rewrite the UC body — suggest direction and let the facilitator/author apply the edit.

</description>
```

## Kind Mapping

| Reviewer verdict (legacy terminology) | `kind` | Notes |
|---------------------------------------|--------|-------|
| `SPLIT` | `finding` | UC is too large; body proposes the split |
| `VAGUE ACTOR`, `VAGUE SITUATION`, `UNCLEAR GOAL`, `WEAK OUTCOME`, `TOO ABSTRACT`, `INCOMPLETE FLOW`, `IMPLEMENTATION LEAK`, `MISSING PRECISION`, `OVERLAPS UC-N` | `finding` | Target set to the offending UC |
| `MISSING ACTOR`, `ORPHAN`, `INCOMPLETE ACTOR`, `PRIVILEGE SPLIT`, `IMPLICIT ACTOR`, `MISSING SYSTEM ACTOR`, `TYPE MISMATCH`, `ROLE MISMATCH` | `finding` | `target: actors` when the concern is the actors table; otherwise target the UC |
| `STALE RELATIONSHIP`, `MISSING UC IN DIAGRAM` | `finding` | Diagram is now a derived view; these translate to frontmatter mismatches between UCs. Target the stale side |
| Domain model: `MISSING CONCEPT`, `MISSING RELATIONSHIP`, `MISSING STATE`, `NAMING CONFLICT` | `finding` | `target: [domain]` |
| System completeness: `MISSING JOURNEY`, `USABILITY GAP`, `MISSING LIFECYCLE`, `IMPLICIT PREREQUISITE` | `gap` | Body includes the UC candidate suggestion; `target:` may be `[]` |
| Open questions surfaced during review | `question` | Target points at the owning UC or wiki page |

## Wiki entries in `target:`

Append wiki basenames to `target:` when the resolution will require editing a wiki page:

- Finding about an actor → add `actors`
- Finding about a domain concept / relationship / state → add `domain`
- Finding about problem framing or scope → add `context`
- Finding about NFRs → add `nfr`
- Pure per-UC edits (flow, outcome, validation) → no wiki entry needed

The close-guard at session-end checks each wiki entry in `target:` before closing.

## Id Allocation

The reviewer must allocate ids via the shared utility:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "<a4-absolute-path>"
```

Allocate one id per finding at the moment the file is written, not up front for the whole batch — parallel reviewer runs (future) should not race.

## Idempotency and Resumption

If the reviewer is re-run on the same `a4/`, it must not create duplicate review items for findings that already exist and are still `open`. Before writing a new review item, check `a4/review/*.md` for an open item whose `target` + short body match the finding; if one exists, skip.

## Return Summary

After writing all review item files, the reviewer returns a concise summary to the caller:

```
verdict: ALL_PASS | NEEDS_REVISION
passed: <M> / <N>
items_written: [12, 13, 14, 15]      # list of allocated ids
domain_model: OK | NEEDS_REVISION | NOT_YET_CREATED
completeness: SUFFICIENT | INCOMPLETE
```

The invoking skill uses this summary to drive the walk-through; it does not re-read each review file for the summary.
