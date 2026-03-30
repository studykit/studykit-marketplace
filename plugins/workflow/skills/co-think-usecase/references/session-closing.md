# Session Closing Procedures

## End Iteration (not finalizing)

1. **Run the usecase-reviewer agent** — invoke the `usecase-reviewer` agent with the current working file path.
2. **Present the review results** — show the user the review report. For each flagged issue, walk through it one at a time:
   - `SPLIT` — propose the split and ask for confirmation
   - `VAGUE` / `UNCLEAR` / `WEAK` — present the suggestion and ask if the user wants to revise
   - `IMPLEMENTATION LEAK` — point out the implementation term and ask for the user-level intent
   - `OVERLAPS` — ask if the user wants to merge or differentiate
   - The user can accept, modify, or dismiss each suggestion. They can also defer items to the next iteration.
3. **Update the working file** with any revisions from the review.
4. **Scan for Open Items** — review all sections for incomplete or unclear items:
   - Use cases flagged by the reviewer but deferred by the user
   - Actors suspected but not confirmed (from Actor Discovery feedback)
   - Vague situations or weak outcomes the user chose not to address now
   - Unresolved Open Questions
   - Relationships not yet analyzed (if < 5 UCs)
5. **Increment `revision`** in frontmatter and update `revised` timestamp. Keep `status: draft`.
6. **Write the Session Checkpoint** — update the heading to `## Session Checkpoint (Revision N)` with the new revision number. Record decisions made and Open Items for next iteration.
7. **Update the Change Log** — record all changes made in this iteration with the new revision number.
8. **Append this session's Interview Transcript** as a new round.
9. **Report** — show the user the current state and Open Items for next time.

## Finalize

1. **Run the usecase-reviewer agent** — invoke the `usecase-reviewer` agent with the current working file path.
2. **Present the review results** — walk through each flagged issue one at a time. All issues should be resolved before finalization; if the user defers any, suggest ending the iteration instead.
3. **Update the working file** with any revisions from the review.
4. **Finalize the Use Case Diagram** — ensure all confirmed use cases, actors, and relationships (include/extend) are reflected in the PlantUML diagram.
5. **Create GitHub Issues for each use case** — for each finalized use case:
   1. Create a GitHub Issue with label `usecase`. Title: prefixed with the UC ID (e.g., `UC-1: Share meeting summary`). Body: the full use case text + a clickable markdown link to the working file (e.g., `[A4/co-think/file.usecase.md](https://github.com/{owner}/{repo}/blob/main/A4/co-think/file.usecase.md)`).
   2. Keep the UC-N ID in the heading as-is (e.g., `### UC-1. Share meeting summary` stays unchanged).
   3. Add a `<!-- references -->` section at the end of the file mapping each UC ID to its GitHub issue URL.
   4. Present the issue mapping to the user:

      > | ID | Issue | Title |
      > |----|-------|-------|
      > | UC-1 | #42 | Share meeting summary |
      > | UC-2 | #43 | Review weekly report |

6. **Finalize the working file** — write the final version with all sections completed:
   - Ensure all headings use UC-N IDs
   - Finalize the Context section with the complete understanding from the interview
   - Ensure all confirmed Use Cases are present and in order
   - Ensure the Actors table is complete
   - Ensure the Use Case Diagram is complete
   - Clear the Open Items table (all items should be resolved)
   - Add the Open Questions section if unresolved topics remain
   - Append the full Interview Transcript
   - Set `status: final` in frontmatter
   - Remove any placeholder text
7. **Report the path and issues** so the user can reference them.
