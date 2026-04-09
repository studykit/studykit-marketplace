# Session Procedures

Detailed step-by-step checklists for ending an iteration and finalizing an implementation plan.

## End Iteration (not finalizing)

1. **Offer a review** — ask the user if they want to run a `plan-reviewer` before closing. If yes:
   - Spawn a fresh `Agent(subagent_type: "plan-reviewer")` with the Full scope request format (all criteria #1–#8). Provide the current plan file path, spec file path, report path per `references/review-report.md` (label: `full-<revision>`), and any previous review report paths.
   - Walk through each flagged issue. The user can accept, modify, or defer items.
   - Update the output file with revisions. Add the review report filename to `reflected_files`.
2. **Scan for Open Items** — walk through each section and identify incomplete or unclear items.
3. **Append a Session Close entry** to the history file per `references/session-history.md`. Include: Revisions This Session, Decisions Made, Change Log (interview-driven changes only), Open Items, Next Steps, and Interview Transcript.
4. **Update the working file** — update Open Items and Next Steps. Increment revision per `references/revision-rules.md`. Keep `status: draft`.
5. **Report** — show the user the current state and Open Items for next time.
6. **Commit to git** — stage all files under `A4/<topic-slug>.*` and commit:
    ```
    impl-plan(<topic-slug>): revision N
    
    - Units: <count>
    - Open items: <count>
    ```

## Finalize

1. **Verify completeness** — check that all FRs from the spec are covered, all units have test strategies, and no critical Open Items remain.
2. **Launch a Full scope `plan-reviewer` subagent** — same pattern as End Iteration step 1. All issues should be resolved before finalization; if the user defers any, suggest ending the iteration instead.
3. **Walk through each flagged issue** — resolve all before proceeding. Update the output file with revisions. Add the review report filename to `reflected_files`.
4. **Append a final Session Close entry** to the history file per `references/session-history.md`. Include cleared Open Items.
5. **Update the working file** — clear Open Items and Next Steps. Set `status: final`. Increment revision per `references/revision-rules.md`.
6. **Report the path** so the user can reference it.
7. **Commit to git** — stage all files under `A4/<topic-slug>.*` and commit:
    ```
    impl-plan(<topic-slug>): finalize
    
    - Units: <count>
    - Status: final
    ```
