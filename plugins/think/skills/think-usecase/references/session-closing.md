# Session Closing Procedures

## End Iteration (not finalizing)

Exploration and review are a combined process: **Explorer → Review**. Explorer finds gaps and new UC candidates first, then Review validates all UCs (existing + newly added) in one pass.

1. **Pre-checkpoint** — write all pending confirmed content to the working file and **increment `revision`**.
2. **Launch explorer subagent** — spawn a fresh `Agent(subagent_type: "usecase-explorer")` with the current working file and report path per `references/exploration-report.md` (label: revision number). If previous exploration reports exist, include their paths so the explorer avoids duplicating candidates. The explorer writes the report and returns results.
3. **Present exploration results** — show each perspective explored and UC candidates found:
   - Ask: "The explorer found these additional angles. Which ones should we add?"
   - If the user picks any, enter the Discovery Loop for those topics (full precision: validation, error handling, etc.)
   - If the user defers any, record as Open Items for next iteration
   - After reflecting, add the exploration file name to `reflected_files`. **Increment `revision`** and update `revised` timestamp.
4. **Launch reviewer subagent** — spawn a fresh `Agent(subagent_type: "usecase-reviewer")` with the **updated** working file (now including any newly added UCs from exploration) and report path per `references/review-report.md` (label: revision number). If a previous review report exists, include its path. The reviewer writes the report and returns results.
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
6. **Update the working file with review revisions** — apply all accepted review changes. Add the review report file name to `reflected_files`. **Increment `revision`** and update `revised` timestamp.
7. **Re-review check** — if significant changes were made during the review walk-through (e.g., UCs split, new UCs from completeness gaps), ask: "Significant changes were made. Run the reviewer again?" If yes, go back to step 4. If no, proceed.
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

1. **Verify Domain Model** — check that the Domain Model section exists with at least a Glossary and Concept Relationships diagram. If missing, inform the user: "Domain Model is required before finalization. It provides the shared vocabulary for architecture and implementation." Do not proceed until resolved.
1b. **Pre-review checkpoint** — write all pending confirmed content to the working file and **increment `revision`**. This stamps the exact document state the reviewer will evaluate.
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
