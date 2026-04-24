# Reviewer Output — Per-Finding Review Items

The `usecase-reviewer` agent no longer writes a single aggregated review report. Instead, it writes **one markdown file per finding** into `a4/review/<id>-<slug>.md`, matching the review-item schema documented in the `spec-as-wiki-and-issues` ADR.

## Per-Item File Format

Frontmatter:

```yaml
---
id: <allocated via scripts/allocate_id.py>
kind: finding | gap | question
status: open
target: usecase/<id>-<slug>       # omit for cross-cutting findings
source: usecase-reviewer
wiki_impact: [<wiki basenames>]   # [] when no wiki update is implied
priority: high | medium | low
labels: []
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---
```

Body structure:

```markdown
# <short finding title>

> Review run: <YYYY-MM-DD HH:mm>

## Summary

One-paragraph statement of the issue.

## Evidence

Quote the specific UC lines, actor table row, or wiki section that demonstrate the issue. Embed the target for context: `![[usecase/<id>-<slug>]]`.

## Suggestion

Concrete, user-level suggestion for the fix. Do not rewrite the UC body — suggest direction and let the facilitator/author apply the edit.
```

## Kind Mapping

| Reviewer verdict (legacy terminology) | `kind` | Notes |
|---------------------------------------|--------|-------|
| `SPLIT` | `finding` | UC is too large; body proposes the split |
| `VAGUE ACTOR`, `VAGUE SITUATION`, `UNCLEAR GOAL`, `WEAK OUTCOME`, `TOO ABSTRACT`, `INCOMPLETE FLOW`, `IMPLEMENTATION LEAK`, `MISSING PRECISION`, `OVERLAPS UC-N` | `finding` | Target set to the offending UC |
| `MISSING ACTOR`, `ORPHAN`, `INCOMPLETE ACTOR`, `PRIVILEGE SPLIT`, `IMPLICIT ACTOR`, `MISSING SYSTEM ACTOR`, `TYPE MISMATCH`, `ROLE MISMATCH` | `finding` | `target: actors` when the concern is the actors table; otherwise target the UC |
| `STALE RELATIONSHIP`, `MISSING UC IN DIAGRAM` | `finding` | Diagram is now a derived view; these translate to frontmatter mismatches between UCs. Target the stale side |
| Domain model: `MISSING CONCEPT`, `MISSING RELATIONSHIP`, `MISSING STATE`, `NAMING CONFLICT` | `finding` | `target: domain`, `wiki_impact: [domain]` |
| System completeness: `MISSING JOURNEY`, `USABILITY GAP`, `MISSING LIFECYCLE`, `IMPLICIT PREREQUISITE` | `gap` | Body includes the UC candidate suggestion; target may be null |
| Open questions surfaced during review | `question` | Target points at the owning UC or wiki page |

## `wiki_impact` Rules

Set when the resolution will require editing a wiki page:

- Finding about an actor → `wiki_impact: [actors]`
- Finding about a domain concept / relationship / state → `wiki_impact: [domain]`
- Finding about problem framing or scope → `wiki_impact: [context]`
- Finding about NFRs → `wiki_impact: [nfr]`
- Pure per-UC edits (flow, outcome, validation) → `wiki_impact: []`

The close-guard at session-end checks these before closing.

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
