# Session Procedures

Detailed step-by-step checklists for ending an iteration and finalizing a specification.

## End Iteration (not finalizing)

1. **Run the spec-reviewer agent** — invoke the `spec-reviewer` agent with the current output file path and all input file paths.
2. **Present the review results** — walk through each flagged issue one at a time. The user can accept, modify, or defer items to the next iteration.
3. **Update the output file** with any revisions from the review.
4. **Scan for Open Items** — walk through each phase and identify incomplete or unclear items (see Revision History section).
5. **Increment `revision`** in frontmatter, update `revised` timestamp. Keep `status: draft`.
6. **Append a new entry to Revision History** — add `### Revision N — <timestamp>` under `## Revision History`. Do not overwrite previous entries. Include: Decisions Made, Change Log (record all changes with source), Open Items, Next Steps, and Interview Transcript (this session's Q&A in a collapsible `<details>` block).
7. **Write the file** using the Write tool.
8. **Report** — show the user the current state and Open Items for next time.

## Finalize

1. **Verify Technology Stack** — check that the Technology Stack section is filled in (at minimum: language and framework). If empty, ask the user: "The Technology Stack isn't specified yet. A coding agent needs this to implement the spec. What language and framework should we use?" Do not proceed to finalize until this is resolved.
2. **Run the spec-reviewer agent** — invoke the `spec-reviewer` agent with the current output file path and all input file paths. All issues should be resolved before finalization; if the user defers any, suggest ending the iteration instead.
3. **Present the review results** — walk through each flagged issue one at a time. The user can accept, modify, or dismiss each suggestion.
4. **Update the output file** with any revisions from the review.
5. **Append a final entry to Revision History** — add `### Revision N — <timestamp>` under `## Revision History`. Include: Decisions Made, Change Log, cleared Open Items table (all items should be resolved), and Interview Transcript.
6. **Finalize the file** — set `status: final` in frontmatter, ensure all sections are complete.
7. **Show the Spec Feedback section prominently** — list all filed upstream feedback GitHub Issues.
8. **Write the file** using the Write tool.
9. **Report the path** so the user can reference it.
