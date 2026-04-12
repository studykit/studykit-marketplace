# Session Closing Procedures

## End Iteration

When the user wants to wrap up, explain what will happen and ask for confirmation:

> "Wrapping up involves these steps:
> 1. Save current progress
> 2. Explore — find gaps and new UC candidates from fresh perspectives
> 3. Review — validate all UCs (existing + newly added)
> 4. Record open items
>
> Ready to proceed?"

If the user confirms, create a task list so they can track progress:

- `"Save progress"` → `in_progress`
- `"Explore: find gaps and new perspectives"` → `pending`
- `"Review: validate all UCs"` → `pending`
- `"Record open items"` → `pending`

Then proceed:

1. **Pre-checkpoint** — write all pending confirmed content to the working file. If content was written, **increment `revision`**, update `revised` timestamp, and **commit** (`A4/<topic-slug>.*`). Mark "Save progress" as `completed`.
2. Mark "Explore" as `in_progress`. **Launch explorer subagent** — spawn a fresh `Agent(subagent_type: "usecase-explorer")` with the current working file and report path per `references/exploration-report.md` (label: revision number). If previous exploration reports exist, include their paths so the explorer avoids duplicating candidates. The explorer writes the report and returns results.
3. **Present exploration results** — show each perspective explored and UC candidates found:
   - Ask: "The explorer found these additional angles. Which ones should we add?"
   - If the user picks any, enter the Discovery Loop for those topics (full precision: validation, error handling, etc.)
   - If the user defers any, record as Open Items for next iteration
   - If changes were made, add the exploration file name to `reflected_files`, **increment `revision`**, update `revised` timestamp, and **commit** (`A4/<topic-slug>.*`).
4. Mark "Explore" as `completed`. Mark "Review" as `in_progress`. **Launch reviewer subagent** — spawn a fresh `Agent(subagent_type: "usecase-reviewer")` with the **updated** working file (now including any newly added UCs from exploration) and report path per `references/review-report.md` (label: revision number). If a previous review report exists, include its path. The reviewer writes the report and returns results.
5. **Present the review results** — walk through issues in this order:

   **Actors Review** — for each actor with issues:
   - `ORPHAN` — actor not referenced by any UC. Ask if the user wants to remove it or assign to a UC.
   - `INCOMPLETE ACTOR` — ask the user to fill in the missing Type or Role.
   - `PRIVILEGE SPLIT` — revisit the Actor table and ask the user whether to split the actor into separate roles.
   - `TYPE MISMATCH` / `ROLE MISMATCH` — show the conflict between declared type/role and observed actions, ask the user to resolve.

   **Cross-UC Findings** — for each finding:
   - `STALE RELATIONSHIP` — show the outdated relationship and ask how to update it.
   - `MISSING UC` / `MISSING ACTOR` in diagram — update the diagram after confirming with the user.

   **Per-UC issues** — for each UC with verdict `NEEDS REVISION`:
   - `SPLIT` — propose the split and ask for confirmation
   - `VAGUE` / `UNCLEAR` / `WEAK` — present the suggestion and ask if the user wants to revise
   - `IMPLEMENTATION LEAK` / `TOO ABSTRACT` — point out the problematic text and ask for the user-level intent
   - `MISSING PRECISION` — ask the user to add validation/error handling
   - `OVERLAPS UC-N` — ask if the user wants to merge or differentiate
   - `MISSING ACTOR` / `IMPLICIT ACTOR` — present the discovered actor and ask if the user wants to add it
   - `MISSING SYSTEM ACTOR` — present the automated behavior and ask if a system actor should be added

   **Domain Model Review** — if Domain Model section exists:
   - `MISSING CONCEPT` / `MISSING RELATIONSHIP` / `MISSING STATE` / `NAMING CONFLICT` — walk through each finding and resolve with the user

   **System Completeness** — if `INCOMPLETE`, present the gaps and UC candidates:
   - Show each gap (MISSING JOURNEY, USABILITY GAP, MISSING LIFECYCLE, IMPLICIT PREREQUISITE) with explanation
   - Present the UC candidates as suggestions
   - Ask: "Would you like to address any of these now, or save them for next time?"
   - If the user picks any, enter the Discovery Loop for those topics
   - If the user defers, record as Open Items for next iteration

   The user can accept, modify, or dismiss each suggestion. They can also defer items to the next iteration.
6. **Update the working file with review revisions** — apply all accepted review changes. If changes were made, add the review report file name to `reflected_files`, **increment `revision`**, update `revised` timestamp, and **commit** (`A4/<topic-slug>.*`).
7. **Re-review check** — if significant changes were made during the review walk-through (e.g., UCs split, new UCs from completeness gaps), ask: "Significant changes were made. Run the reviewer again?" If yes, go back to step 4. If no, proceed.
8. Mark "Review" as `completed`. Mark "Record open items" as `in_progress`. **Scan for Open Items** — review all sections for incomplete or unclear items:
   - Use cases flagged by the reviewer but deferred by the user
   - Actors suspected but not confirmed (from Actors Review feedback)
   - Vague situations or weak outcomes the user chose not to address now
   - System Completeness gaps and UC candidates deferred by the user
   - Explorer perspectives and UC candidates deferred by the user
   - Unresolved Open Questions
   - Relationships not yet analyzed (if < 5 UCs)
9. **Append a Session Close entry to the history file** (`<topic-slug>.usecase.history.md`) per `references/session-history.md`. Include: Revisions This Session, Last Completed, Decisions Made, Change Log (interview-driven changes only), Open Items, Next Steps, and Interview Transcript.
10. **Update the working file** — update the Open Items and Next Steps sections with the current state. **Increment `revision`** and update `revised` timestamp. Set `last_step` to `revision N`. Keep `status: draft`. Write using the Write tool. **Commit** (`A4/<topic-slug>.*`):
    ```
    usecase(<topic-slug>): revision N

    - UCs: <total count> (<added> added, <modified> revised)
    - UCs passed: <M> / <N>
    - Open items: <count>
    ```
11. Mark "Record open items" as `completed`.
12. **Offer GitHub Issues** — ask: "Would you like to create GitHub Issues for the use cases?"
    - If yes → for each confirmed UC that doesn't already have an issue:
      1. Create a GitHub Issue with label `usecase`. Title: prefixed with the UC ID (e.g., `UC-1: Share meeting summary`). Body: the full use case text + a clickable markdown link to the working file.
      2. Add a `<!-- references -->` section at the end of the file mapping each UC ID to its GitHub issue URL.
      3. Present the issue mapping to the user.
    - If no → skip.
13. **Report** — show the user the current state and Open Items for next time. Suggest: "To design the architecture from these use cases, run `/think:think-arch <file_path>`."
