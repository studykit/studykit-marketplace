# Session Procedures

Detailed step-by-step checklist for ending an iteration.

## End Iteration

When the user wants to wrap up, explain what will happen and ask for confirmation:

> "Wrapping up involves these steps:
> 1. Save current progress
> 2. Review — validate architecture completeness and consistency
> 3. Record open items
>
> Ready to proceed?"

If the user confirms, create wrap-up tasks:

- `"Save progress"` → `in_progress`
- `"Review: validate architecture"` → `pending`
- `"Record open items"` → `pending`

Then proceed:

1. **Pre-review checkpoint** — write all pending confirmed content to the working file. If content was written, **increment `revision`**, update `revised` timestamp, and **commit** (`A4/<topic-slug>.*`). Mark "Save progress" as `completed`.
2. Mark "Review" as `in_progress`. **Launch `arch-reviewer` subagent** — spawn a fresh `Agent(subagent_type: "think:arch-reviewer")` with the Full scope request format. Provide the current arch file path, usecase file path, report path per `references/review-report.md` (label: `full-<revision>`), and any previous review report paths.
3. **Walk through each flagged issue** — the user can accept, modify, or defer items. If changes were made, update the output file with revisions, add the review report filename to `reflected_files`, **increment `revision`**, update `revised` timestamp, and **commit** (`A4/<topic-slug>.*`).
4. Mark "Review" as `completed`. Mark "Record open items" as `in_progress`. **Scan for Open Items** — walk through each section and identify incomplete or unclear items.
5. **Append a Session Close entry** to the history file per `references/session-history.md`. Include: Revisions This Session, Decisions Made, Change Log (interview-driven changes only), Open Items, Next Steps, and Interview Transcript.
6. **Update the working file** — update Open Items and Next Steps. **Increment `revision`** and update `revised` timestamp. **Commit** (`A4/<topic-slug>.*`):
    ```
    arch(<topic-slug>): revision N

    - Areas completed: <list>
    - Open items: <count>
    ```
7. Mark "Record open items" as `completed`. **Report** — show the user the current state and Open Items for next time. Suggest: "To set up the development environment, run `/think:auto-bootstrap <file_path>`."
