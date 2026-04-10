# Session Procedures

Detailed step-by-step checklists for ending an iteration and finalizing a specification.

## End Iteration (not finalizing)

1. **Pre-review checkpoint** — write all pending confirmed content to the working file and **increment `revision`**. This stamps the exact document state the reviewer will evaluate.
2. **Launch a Full scope `spec-reviewer` subagent** — spawn a fresh `Agent(subagent_type: "spec-reviewer")` with the Full scope request format (all criteria #0–#7). Provide the current output file path, all input file paths, report path per `references/review-report.md` (label: `full-<revision>`), and any previous review report paths.
3. **Present the review results** — walk through each flagged issue one at a time. The user can accept, modify, or defer items to the next iteration.
4. **Update the output file** with any revisions from the review. Add the review report file name to the frontmatter `reflected_files` list. **Increment `revision`** and update `revised` timestamp.
5. **Scan for Open Items** — walk through each phase and identify incomplete or unclear items.
6. **Append a Session Close entry to the history file** (`<topic-slug>.spec.history.md`) per `references/session-history.md`. Include: Revisions This Session, Decisions Made, Change Log (interview-driven changes only), Open Items, Next Steps, and Interview Transcript.
7. **Update the working file** — update the Open Items and Next Steps sections with the current state. **Increment `revision`** and update `revised` timestamp. Keep `status: draft`. Write using the Write tool.
8. **Report** — show the user the current state and Open Items for next time.
9. **Commit to git** — stage all files under `A4/<topic-slug>.*` and commit:
    ```
    spec(<topic-slug>): revision N
    
    - Phases: <completed phases>
    - Open items: <count>
    ```

## Finalize

1. **Verify Technology Stack** — check that the Technology Stack section is filled in (at minimum: language and framework). If empty, ask the user: "The Technology Stack isn't specified yet. A coding agent needs this to implement the spec. What language and framework should we use?" Do not proceed to finalize until this is resolved.
2. **Pre-review checkpoint** — write all pending confirmed content to the working file and **increment `revision`**. This stamps the exact document state the reviewer will evaluate.
3. **Launch a Full scope `spec-reviewer` subagent** — spawn a fresh `Agent(subagent_type: "spec-reviewer")` with the Full scope request format (all criteria #0–#7). Provide the current output file path, all input file paths, report path per `references/review-report.md` (label: `final`), and any previous review report paths. All issues should be resolved before finalization; if the user defers any, suggest ending the iteration instead.
4. **Present the review results** — walk through each flagged issue one at a time. The user can accept, modify, or dismiss each suggestion.
5. **Update the output file** with any revisions from the review. Add the review report file name to the frontmatter `reflected_files` list. **Increment `revision`** and update `revised` timestamp.
6. **Append a final Session Close entry to the history file** (`<topic-slug>.spec.history.md`) per `references/session-history.md`. Include: Revisions This Session, Decisions Made, Change Log (interview-driven changes only), cleared Open Items, and Interview Transcript.
7. **Update the working file** — clear Open Items and Next Steps. Set `status: final` in frontmatter, ensure all sections are complete. **Increment `revision`** and update `revised` timestamp.
8. **Show the Spec Feedback section prominently** — list all filed upstream feedback GitHub Issues.
9. **Write the file** using the Write tool.
10. **Report the path** so the user can reference it.
11. **Commit to git** — stage all files under `A4/<topic-slug>.*` and commit:
    ```
    spec(<topic-slug>): finalize
    
    - Phases: requirements, domain model, architecture
    - Status: final
    ```

## Upstream Feedback Issues

During the specification process, problems in upstream artifacts (use cases) may surface. When this happens:

1. **Note the problem** — describe what's wrong with the upstream artifact.
2. **Ask the user** — "I noticed UC-3 has a vague situation. Should I create a GitHub Issue to track this?"
3. **If approved, create a GitHub Issue:**
   - **Labels:** `usecase` + `feedback`
   - **Title:** Brief description of the problem
   - **Body:** Include the artifact reference, what's unclear, and how it affects the current work. Include a clickable markdown link to the artifact file.
4. **Continue working** — don't block on the upstream issue. Make reasonable assumptions and note them.

Do NOT create issues proactively. Only create them as problems surface naturally during the interview.
