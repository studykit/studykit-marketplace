# Iteration Entry Procedure

When entering **Iteration** mode (an existing `a4/` workspace with UC files is found), perform these checks before starting work. The goal is to surface unresolved review items, unreflected research/exploration reports, and any wiki drift so the session picks up coherently.

## 1. Scan the Workspace

List the current state:

- Wiki pages present: `a4/{context,actors,domain,nfr}.md` (each optional except `context.md`).
- UC count: `ls a4/usecase/*.md | wc -l`.
- Open review items: `grep -l 'status: open' a4/review/*.md` (if any).
- Research reports: `ls a4/research/*.md` (if the folder exists).

Do **not** read every UC up front. Read on demand as the user chooses what to work on.

## 2. Open Review Items Take Priority

Read each open review item file (`a4/review/<id>-<slug>.md` with `status: open`). Present them as a selectable backlog:

> **Open review items:**
>
> | # | Id | Kind | Target | Summary | Priority |
> |---|----|------|--------|---------|----------|
> | 1 | 6  | gap  | UC-3   | Missing validation on empty input | High |
> | 2 | 9  | question | — | How should concurrency be handled? | Medium |
> | 3 | 12 | finding | UC-7 | Implementation leak in Flow step 4 | Medium |
>
> Which items would you like to address, or would you prefer to add new use cases?

For each item the user picks, mark its review file `status: in-progress`, update `updated:`, and open a task like `"Resolve review/<id>: <short summary>"`.

## 3. Unreflected Research / Exploration Reports

Check `a4/research/` for reports that were written but never reflected into UCs. A report is unreflected when no UC cites it in body prose and no review item references it. Present these to the user and decide whether to reflect.

## 4. Work Surface Summary

Present a brief status:

- UCs confirmed: `<count>`, of which `done`: `<count>`, `implementing`: `<count>`, `blocked`: `<count>`
- Actors in `actors.md`: `<count>` (if the file exists)
- Domain concepts in `domain.md`: `<count>` (if the file exists)
- Open review items: `<count>` (listed above)
- Research reports pending review: `<count>`

## 5. User Chooses What to Work On

Possible activities:

- **Resolve review items** — the user picks from the backlog; for each, read the target UC and wiki pages and walk through the resolution with the user.
- **Add new use cases** — resume the Discovery Loop. Each new UC gets a fresh id from the allocator.
- **Refine actors** — edit `actors.md`; add footnote markers for changes.
- **Split oversized UCs** — allocate new ids per child, write new UC files, adjust `depends_on`/`related` in other UCs that referenced the parent.
- **Extend the domain model** — edit `domain.md` via the Domain Model Extraction flow.
- **Re-analyze relationships** — update `depends_on`/`related`/`labels` across UC files.

## Iteration Rules

- Preserve previously confirmed UC content. Never delete or renumber UC files; renumber is especially forbidden because ids are globally monotonic.
- New UCs get the next allocator-provided id (see SKILL.md → Id Allocation). Continue regardless of gaps — gaps are allowed.
- When modifying an existing UC, show the before/after and confirm with the user before writing.
- When a resolution edits a wiki page, add a footnote marker and `## Changes` entry per the Wiki Update Protocol in SKILL.md.
- When a review item is resolved, set its frontmatter to `status: resolved` and append a `## Log` entry (`YYYY-MM-DD — resolved by editing [[usecase/<id>-<slug>]]`). Do not delete review item files.
