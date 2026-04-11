# Session Procedures

Detailed step-by-step checklists for ending an iteration and finalizing an architecture.

## End Iteration (not finalizing)

1. **Offer a review** — ask the user if they want to run an `arch-reviewer` before closing. If yes:
   - **Pre-review checkpoint** — write all pending confirmed content to the working file and **increment `revision`**.
   - Spawn a fresh `Agent(subagent_type: "arch-reviewer")` with the Full scope request format. Provide the current arch file path, usecase file path, report path per `references/review-report.md` (label: `full-<revision>`), and any previous review report paths.
   - Walk through each flagged issue. The user can accept, modify, or defer items.
   - Update the output file with revisions. Add the review report filename to `reflected_files`. **Increment `revision`** and update `revised` timestamp.
2. **Scan for Open Items** — walk through each section and identify incomplete or unclear items.
3. **Append a Session Close entry** to the history file per `references/session-history.md`. Include: Revisions This Session, Decisions Made, Change Log (interview-driven changes only), Open Items, Next Steps, and Interview Transcript.
4. **Update the working file** — update Open Items and Next Steps. **Increment `revision`** and update `revised` timestamp. Keep `status: draft`.
5. **Report** — show the user the current state and Open Items for next time.
6. **Commit to git** — stage all files under `A4/<topic-slug>.*` and commit:
    ```
    arch(<topic-slug>): revision N
    
    - Areas completed: <list>
    - Open items: <count>
    ```

## Finalize

1. **Verify completeness** — check that all required sections are present:
   - Technology Stack filled
   - Test Strategy filled with at least unit tier
   - All components have interface contracts
   - All UCs with component involvement have information flow diagrams
2. **Pre-review checkpoint** — write all pending confirmed content and **increment `revision`**.
3. **Launch a Full scope `arch-reviewer` subagent** — same pattern as End Iteration. All issues should be resolved; if the user defers any, suggest ending the iteration instead.
4. **Walk through each flagged issue** — resolve all. Update the output file. Add review report to `reflected_files`. **Increment `revision`**.
5. **Append a final Session Close entry** to the history file. Include cleared Open Items.
6. **Update the working file** — clear Open Items and Next Steps. Set `status: final`. **Increment `revision`**.
7. **Report the path** so the user can reference it.
8. **Commit to git** — stage all files under `A4/<topic-slug>.*` and commit:
    ```
    arch(<topic-slug>): finalize
    
    - Areas: technology stack, external dependencies, components, test strategy
    - Status: final
    ```
