# Session Closing Procedures

## End Iteration (not finalizing)

1. **Pre-review checkpoint** — write all pending confirmed content to the working file and **increment `revision`**. This stamps the exact document state the reviewer will evaluate.
2. **Launch reviewer subagent** — spawn a fresh `Agent(subagent_type: "usecase-reviewer")` with the current working file path and report path per `references/review-report.md` (label: revision number). If a previous review report exists, include its path so the reviewer can check whether prior findings have been addressed. The reviewer writes the report and returns results.
3. **Present the review results** — show the user the review report. Walk through issues in this order:

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
   - `OVERLAPS UC-N` — ask if the user wants to merge or differentiate
   - `MISSING ACTOR` / `IMPLICIT ACTOR` — present the discovered actor and ask if the user wants to add it
   - `MISSING SYSTEM ACTOR` — present the automated behavior and ask if a system actor should be added

   **System Completeness** — if `INCOMPLETE`, present the gaps and UC candidates:
   - Show each gap (MISSING JOURNEY, USABILITY GAP, MISSING LIFECYCLE) with explanation
   - Present the UC candidates as suggestions for the next iteration
   - Ask: "Would you like to explore any of these now, or save them for next time?"
   - If the user picks any, enter the Discovery Loop for those topics
   - If the user defers, record as Open Items for next iteration

   The user can accept, modify, or dismiss each suggestion. They can also defer items to the next iteration.
4. **Update the working file with review revisions** — apply all accepted review changes to the working file. Add the review report file name to the frontmatter `reflected_files` list. **Increment `revision`** and update `revised` timestamp.
5. **Ask for next step** — present the user with a choice:
   > "Review changes have been applied. What would you like to do next?"
   > 1. **Run exploration** — let the explorer find new perspectives and UC candidates based on the updated file
   > 2. **Re-review** — run the reviewer again against the updated file (useful if significant changes were made)

   - If the user chooses **exploration** → proceed to step 6.
   - If the user chooses **re-review** → go back to step 1 with the updated file (pre-review checkpoint bumps revision, so the new report naturally gets a distinct label). Repeat steps 1–5 until the user chooses exploration or explicitly skips it.
   - If the user wants to **skip exploration entirely** → proceed directly to step 8.
6. **Launch explorer subagent** — spawn a fresh `Agent(subagent_type: "usecase-explorer")` with the **updated** working file and report path per `references/exploration-report.md` (label: revision number). If previous exploration reports exist, include their paths so the explorer avoids duplicating candidates. The explorer writes the report and returns results. Present the exploration results:
   - Show each perspective explored and UC candidates found
   - Ask: "The explorer found these additional angles we haven't covered. Would you like to explore any now, or save them for next time?"
   - If the user picks any, enter the Discovery Loop for those topics. After reflecting the results, add the exploration file name to the frontmatter `reflected_files` list.
   - If the user defers, record as Open Items for next iteration (exploration file remains unconsumed for next session)
7. **Update the working file with exploration results** — apply any accepted exploration changes. Add the exploration report file name to the frontmatter `reflected_files` list. **Increment `revision`** and update `revised` timestamp.
8. **Scan for Open Items** — review all sections for incomplete or unclear items:
   - Use cases flagged by the reviewer but deferred by the user
   - Actors suspected but not confirmed (from Actors Review feedback)
   - Vague situations or weak outcomes the user chose not to address now
   - System Completeness gaps and UC candidates deferred by the user
   - Explorer perspectives and UC candidates deferred by the user
   - Unresolved Open Questions
   - Relationships not yet analyzed (if < 5 UCs)
9. **Append a Session Close entry to the history file** (`<topic-slug>.usecase.history.md`) per `references/session-history.md`. Include: Revisions This Session, Last Completed, Decisions Made, Change Log (interview-driven changes only), Open Items, Next Steps, and Interview Transcript.
10. **Update the working file** — update the Open Items and Next Steps sections with the current state. **Increment `revision`** and update `revised` timestamp. Set `last_step` to `revision N`. Keep `status: draft`. Write using the Write tool.
11. **Commit to git** — stage all files under `A4/<topic-slug>.*` and commit:
    ```
    usecase(<topic-slug>): revision N
    
    - UCs: <total count> (<added> added, <modified> revised)
    - UCs passed: <M> / <N>
    - Open items: <count>
    ```
12. **Report** — show the user the current state and Open Items for next time.

## Finalize

1. **Pre-review checkpoint** — write all pending confirmed content to the working file and **increment `revision`**. This stamps the exact document state the reviewer will evaluate.
2. **Launch final reviewer subagent** — spawn a fresh `Agent(subagent_type: "usecase-reviewer")` with the current working file path and report path per `references/review-report.md` (label: `final`). If previous review reports exist, include their paths. The reviewer writes the report and returns results.
3. **Present the review results** — walk through each flagged issue one at a time. All issues should be resolved before finalization; if the user defers any, suggest ending the iteration instead. If System Completeness is `INCOMPLETE`, inform the user of the gaps and ask whether to proceed with finalization or end the iteration to address them first.
4. **Update the working file** with any revisions from the review. Add the review report file name to the frontmatter `reflected_files` list. **Increment `revision`** and update `revised` timestamp. Record changes in the Change Log with the review report file name as Source.
5. **Finalize the Use Case Diagram** — ensure all confirmed use cases, actors, and relationships (include/extend) are reflected in the PlantUML diagram.
6. **Create GitHub Issues for each use case** — for each finalized use case:
   1. Create a GitHub Issue with label `usecase`. Title: prefixed with the UC ID (e.g., `UC-1: Share meeting summary`). Body: the full use case text + a clickable markdown link to the working file (e.g., `[A4/file.usecase.md](https://github.com/{owner}/{repo}/blob/main/A4/file.usecase.md)`).
   2. Keep the UC-N ID in the heading as-is (e.g., `### UC-1. Share meeting summary` stays unchanged).
   3. Add a `<!-- references -->` section at the end of the file mapping each UC ID to its GitHub issue URL.
   4. Present the issue mapping to the user:

      > | ID | Issue | Title |
      > |----|-------|-------|
      > | UC-1 | #42 | Share meeting summary |
      > | UC-2 | #43 | Review weekly report |

7. **Finalize the working file** — write the final version with all sections completed:
   - Ensure all headings use UC-N IDs
   - Finalize the Context section with the complete understanding from the interview
   - Ensure all confirmed Use Cases are present and in order
   - Ensure the Actors table is complete
   - Ensure the Use Case Diagram is complete
   - Clear the Open Items and Next Steps sections (all items should be resolved)
   - Add the Open Questions section if unresolved topics remain
   - Append final Session Close entry to the history file (`<topic-slug>.usecase.history.md`) per `references/session-history.md`: Revisions This Session, Decisions Made, Change Log (interview-driven changes only), cleared Open Items, and Interview Transcript.
   - Set `status: final` and `last_step` to `finalize` in frontmatter. **Increment `revision`** and update `revised` timestamp.
   - Remove any placeholder text
8. **Commit to git** — stage all files under `A4/<topic-slug>.*` and commit:
   ```
   usecase(<topic-slug>): finalize
   
   - UCs: <total count>
   - UCs passed: <N> / <N>
   - GitHub issues: <issue numbers>
   ```
9. **Report the path and issues** so the user can reference them.
