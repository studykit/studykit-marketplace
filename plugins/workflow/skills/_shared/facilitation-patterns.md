# Co-Think Shared Facilitation Patterns

Patterns shared across all co-think skills. Each skill customizes these to its domain.

## One Question at a Time

Ask exactly ONE question per turn. Wait for the answer. Then ask the next. This is non-negotiable.

Multiple questions produce shallow answers. A single focused question forces both sides to think deeply about one thing before moving on.

## Navigation Principles

- **User controls all transitions.** Never move to the next phase/step/topic automatically. When the current phase feels sufficiently covered, suggest moving on — but let the user decide.
- **Revisiting is welcome.** The user may return to a previous phase at any time — e.g., research may reveal that earlier decisions need updating.
- **Pausing is fine.** The user may want to hold the current phase and come back later. Acknowledge and resume when ready.
- **Phases can interleave.** If work in one phase reveals something relevant to another, note it and ask the user if they want to address it now or later.

## Progress Checkpoints

Every 3-5 exchanges, provide a brief progress snapshot — what's been covered, what's decided, what's next. Update the working file with the latest understanding.

## Reviewer Agent Flow (Wrapping Up)

The session ends only when the user says so. Never conclude unilaterally — even if all work seems covered, the user may want to revisit or go deeper.

When the user indicates they're done:

1. **Run the skill's reviewer agent** with the current output file path.
2. **Present the review results** — show the user the review report. For each flagged issue, walk through it one at a time. The user can accept, modify, or dismiss each suggestion. Respect their decision.
3. **Update the output file** with any revisions from the review.
4. **Finalize the file** — ensure all sections are complete, remove placeholder text, update status fields from draft to final.
5. **Stage the file** — run `git add <file_path>` to include it in version control.
6. **Report the path** so the user can reference it.
7. **Suggest next steps** — if the output feeds into another co-think skill, mention it.
