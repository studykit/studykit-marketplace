# Session Closing Procedures

## End Iteration

When the user wants to wrap up, explain what will happen and ask for confirmation:

> Wrapping up involves these steps:
> 1. Explore — find gaps and new UC candidates from fresh perspectives
> 2. Review — validate all UCs (existing + newly added) and emit per-finding review items
> 3. Walk through each emitted review item and resolve or defer
> 4. Wiki close guard — verify wiki footnotes exist for resolved items with `wiki_impact`
>
> Ready to proceed?

If the user confirms, create tasks:

- `"Explore: find gaps and new perspectives"` → `in_progress`
- `"Review: validate all UCs"` → `pending`
- `"Walk findings and open review items"` → `pending`
- `"Wiki close guard"` → `pending`

Then proceed:

### 1. Explore

Launch `Agent(subagent_type: "a4:usecase-explorer")`. Pass:
- `a4/` absolute path
- Expected report output path: `a4/research/exploration-<YYYY-MM-DD>.md` (create `a4/research/` if missing)
- Any prior exploration report paths so the explorer avoids duplicates

The explorer writes the report and returns a short summary listing UC candidates.

**Walk candidates with the user.** For each candidate:
- **Accept** — enter the Discovery Loop for that topic (full precision: Flow, Outcome, Validation, Error handling). Write the new UC file as usual.
- **Defer** — create a review item: allocate id, write `a4/review/<id>-<slug>.md` with `kind: gap`, `status: open`, `source: usecase-explorer`, `target: null` (or a wiki basename if applicable), body summarizing the candidate and why it was deferred.

Mark "Explore" completed.

### 2. Review

Mark "Review: validate all UCs" `in_progress`. Launch `Agent(subagent_type: "a4:usecase-reviewer")`. Pass:
- `a4/` absolute path
- List of review item ids from any prior session so the reviewer can check whether prior findings were addressed (skip if this is the first review)

The reviewer writes **one review item file per finding** directly into `a4/review/<id>-<slug>.md` (using the allocator). It returns a summary listing the ids written, overall verdict (`ALL_PASS` or `NEEDS_REVISION`), and system-completeness status.

Mark "Review" completed.

### 3. Walk Findings and Open Review Items

Mark "Walk findings and open review items" `in_progress`.

For each new review item from the reviewer (ordered by priority then id), read the file, present the finding to the user, and walk through resolution. Resolution paths:

**Fix now** — edit the target (UC file or wiki page). On success:
1. Update the review item frontmatter: `status: resolved`, `updated: <today>`, `resolved_by: edit` (or similar custom field if useful).
2. Append a `## Log` entry to the review item: `YYYY-MM-DD — resolved by editing [[<target path>]]`.
3. If the edit touched a wiki page and the review item had a non-empty `wiki_impact`, add the footnote marker + `## Changes` entry on that wiki page per the Wiki Update Protocol.

**Defer** — leave the review item `status: open`. Add a `## Log` entry noting the deferral reason.

**Dismiss** — set `status: dismissed`, `updated: <today>`, append `## Log` entry with the reason.

Common finding types the reviewer emits (mirrored from `${CLAUDE_SKILL_DIR}/references/review-report.md`):

- **UC quality issues** — `size/split`, `vague actor`, `unclear goal`, `vague situation`, `incomplete flow`, `implementation leak`, `weak outcome`, `missing precision`, `overlap`.
- **Actor findings** — `orphan actor`, `incomplete actor`, `privilege split`, `type mismatch`, `role mismatch`, `implicit actor`, `missing system actor`.
- **Cross-UC findings** — `stale relationship`, `missing UC/actor in diagram` (diagram is now derived, so this becomes "missing from frontmatter `actors`/`depends_on`").
- **Domain model findings** — `missing concept`, `missing relationship`, `missing state`, `naming conflict`.
- **System completeness findings** — `missing journey`, `usability gap`, `missing lifecycle`, `implicit prerequisite`. These become `kind: gap` review items with UC candidates in the body.

Mark "Walk findings and open review items" completed.

### 4. Wiki Close Guard

Mark "Wiki close guard" `in_progress`.

For each review item that transitioned to `resolved` in this session AND has a non-empty `wiki_impact`:

1. For each wiki basename in `wiki_impact` (e.g., `domain`), read `a4/<basename>.md`.
2. Check whether the page has a footnote in `## Changes` whose payload wikilinks the causing issue (the resolved item's `target`, or the item itself if `target` was null).
3. If missing, warn the user: `"<basename>.md has no footnote for [[<causing issue>]]. Resolve anyway?"`. On override, accept and proceed. On correction, edit the wiki page to add the footnote.

Mark "Wiki close guard" completed.

### 5. Report

Produce a short session report:

- UCs confirmed this session: `<count>` (ids: `<list>`)
- UCs revised this session: `<count>` (ids: `<list>`)
- Wiki pages written/updated: `<list>`
- Review items opened: `<count>` (ids: `<list>`)
- Review items resolved: `<count>` (ids: `<list>`)
- Review items still open after session: `<count>`

Suggest the next step: `/a4:arch` once the UC set and domain model feel stable, or `/a4:usecase iterate` to pick up remaining review items later.

## Commit

Commit timing is user-driven: after each significant batch (e.g., after review-items walk, after wiki close guard). Recommend `/a4:handoff` as the session-end commit path so the resumption handoff file records the shape of the session. Never commit from the main session without the user's say-so.
