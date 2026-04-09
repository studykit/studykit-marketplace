# Session Procedures

Detailed step-by-step checklists for ending an iteration and finalizing an implementation plan.

## End Iteration (not finalizing)

1. **Launch a Full scope `plan-reviewer` subagent** — if a `plan-reviewer` agent was already spawned in this session, offer the user a choice to reuse it (via `SendMessage`) or spawn fresh (see `${CLAUDE_PLUGIN_ROOT}/references/agent-reuse-guide.md`). For a fresh spawn, use `Agent(subagent_type: "plan-reviewer", name: "plan-reviewer")` with the Full scope request format (all criteria #1–#8). Provide the current plan file path, spec file path, report path per `references/review-report.md` (label: `full-<revision>`), and any previous review report paths.
2. **Present the review results** — walk through each flagged issue one at a time. The user can accept, modify, or defer items to the next iteration.
3. **Update the output file** with any revisions from the review. Add the review report file name to the frontmatter `reflected_files` list. **Increment `revision`** and update `revised` timestamp.
4. **Scan for Open Items** — walk through each section and identify incomplete or unclear items.
5. **Append a Session Close entry to the history file** (`<topic-slug>.impl-plan.history.md`) per `references/session-history.md`. Include: Revisions This Session, Decisions Made, Change Log (interview-driven changes only), Open Items, Next Steps, and Interview Transcript.
6. **Update the working file** — update the Open Items and Next Steps sections with the current state. **Increment `revision`** and update `revised` timestamp. Keep `status: draft`. Write using the Write tool.
7. **Report** — show the user the current state and Open Items for next time.
8. **Commit to git** — stage all files under `A4/co-think/<topic-slug>.*` and commit:
    ```
    impl-plan(<topic-slug>): revision N
    
    - Units: <count>
    - Open items: <count>
    ```

## Finalize

1. **Verify completeness** — check that all FRs from the spec are covered, all units have test strategies, and no critical Open Items remain.
2. **Launch a Full scope `plan-reviewer` subagent** — same pattern as End Iteration. All issues should be resolved before finalization; if the user defers any, suggest ending the iteration instead.
3. **Present the review results** — walk through each flagged issue one at a time.
4. **Update the output file** with any revisions from the review. Add the review report file name to the frontmatter `reflected_files` list. **Increment `revision`** and update `revised` timestamp.
5. **Append a final Session Close entry to the history file** per `references/session-history.md`. Include cleared Open Items.
6. **Update the working file** — clear Open Items and Next Steps. Set `status: final` in frontmatter. **Increment `revision`** and update `revised` timestamp.
7. **Write the file** using the Write tool.
8. **Report the path** so the user can reference it.
9. **Commit to git** — stage all files under `A4/co-think/<topic-slug>.*` and commit:
    ```
    impl-plan(<topic-slug>): finalize
    
    - Units: <count>
    - Status: final
    ```
