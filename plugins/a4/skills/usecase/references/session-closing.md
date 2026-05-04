# Session Closing Procedures

## End Iteration

When the user wants to wrap up, explain what will happen and ask for confirmation:

> Wrapping up involves these steps:
> 1. Explore — find gaps and new UC candidates from fresh perspectives
> 2. Review — validate all UCs (existing + newly added) and emit per-finding review items
> 3. Walk through each emitted review item and resolve or defer
> 4. Wiki close guard — verify wiki footnotes exist for resolved items whose `target:` lists a wiki basename
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
- **Defer** — create a review item: allocate id, write `a4/review/<id>-<slug>.md` with `kind: gap`, `status: open`, `source: usecase-explorer`, `target: []` (or `[<wiki basename>]` if applicable), body summarizing the candidate and why it was deferred.

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
1. Edit the review item's `status:` to `resolved` directly.
2. If the edit touched a wiki page and the review item's `target:` listed a wiki basename, append a dated bullet with a markdown link to the review item itself inside the page's `## Change Logs` section per the Wiki Update Protocol.

**Defer** — leave the review item `status: open`. For a pure-defer pause the deferral reason is captured in conversation notes / handoff; if the user wants it inscribed in the issue body, append it by hand to the optional `## Log` section.

**Discard** — append the rationale to the review item's optional `## Log` section first (one-line dated bullet), then edit `status:` to `discarded` directly.

Common finding types the reviewer emits (mirrored from `${CLAUDE_SKILL_DIR}/authoring/review-report.md`):

- **UC quality issues** — `size/split`, `vague actor`, `unclear goal`, `vague situation`, `incomplete flow`, `implementation leak`, `weak outcome`, `missing precision`, `overlap`.
- **Actor findings** — `orphan actor`, `incomplete actor`, `privilege split`, `type mismatch`, `role mismatch`, `implicit actor`, `missing system actor`.
- **Cross-UC findings** — `stale relationship`, `missing UC/actor in diagram` (diagram is now derived, so this becomes "missing from frontmatter `actors:` or from the UC's `## Dependencies` body section").
- **Domain model findings** — `missing concept`, `missing relationship`, `missing state`, `naming conflict`.
- **System completeness findings** — `missing journey`, `usability gap`, `missing lifecycle`, `implicit prerequisite`. These become `kind: gap` review items with UC candidates in the body.

Mark "Walk findings and open review items" completed.

### 4. Wiki Close Guard

Mark "Wiki close guard" `in_progress`.

For each review item that transitioned to `resolved` in this session whose `target:` lists one or more wiki basenames:

1. For each wiki basename in `target:` (e.g., `domain`), read `a4/<basename>.md`.
2. Check whether the page's `## Change Logs` section contains a bullet whose markdown link points at the resolved review item.
3. If missing, warn the user: `"<basename>.md has no change-log entry for <causing issue>. Resolve anyway?"`. On override, accept and proceed. On correction, edit the wiki page to add the bullet (creating `## Change Logs` if absent).

Mark "Wiki close guard" completed.

### 5. Report

Produce a short session report:

- UCs confirmed this session: `<count>` (ids: `<list>`)
- UCs revised this session: `<count>` (ids: `<list>`)
- Wiki pages written or edited: `<list>`
- Review items opened: `<count>` (ids: `<list>`)
- Review items resolved: `<count>` (ids: `<list>`)
- Review items still open after session: `<count>`

`/a4:usecase iterate` is the right path to pick up remaining open review items later.

## Commit

Commit timing is user-driven: after each significant batch (e.g., after review-items walk, after wiki close guard). Recommend `/a4:handoff` as the session-end commit path so the resumption handoff file records the shape of the session. Never commit from the main session without the user's say-so.
