# Spark Brainstorm Wrap Up

The session ends only when the user says so. Never conclude unprompted.

When the user indicates they're done:

1. **Ask to summarize** — Ask: "Would you like me to summarize what we've covered?" and wait for the user's response.
2. **If the user declines** — End the session immediately.
3. **If the user agrees** — Draft the summary following the file format below. Ensure these are fully preserved: (1) anything the user emphasized as important during the conversation, (2) key turning points and rejected directions with reasons (→ Discussion Journey section), (3) any research findings from subagent investigations, and (4) any TODOs or action items that came up during the conversation. Each idea must have a short title and a 1-2 sentence description, grouped under theme headings. Present the draft to the user and incorporate any feedback.
4. **Decide status** — Before asking the save location, determine the initial `status:` by interpreting the user's natural-language signals:
   - Signals for `discarded` (session closes without ideas to pursue): "접자", "없던 일로", "그냥 두자", "discard", "drop this", "buried", "not worth it". If these or similar close-out signals dominated the session's end, set `status: discarded`.
   - Otherwise set `status: open` (the session may be revisited, ideas may later graduate).
   - Do **not** set `status: promoted` here. `promoted` is written only when a downstream artifact (spec / usecase / task) is actually produced — that is a separate action from closing the brainstorm. If the user already produced a spec during the session and wants to record the link, ask them to run `/a4:spec` first, then edit `promoted:` by hand.
   - If the signal is ambiguous, ask once: "Close this brainstorm as `open` (we may return to these ideas) or `discarded` (these ideas are buried)?" Accept the user's answer literally.
5. **Ask save location** — Ask where to save. Default path: `a4/spark/<YYYY-MM-DD-HHmm>-<topic-slug>.brainstorm.md` relative to the working directory. Create the directory if it does not exist.
6. **Write the file** — Save using the Write tool. Use the `status:` from step 4.
7. **Report the path** — After writing, report the full file path so the main session can reference it. Mention the recorded status explicitly (e.g., "Saved as `status: discarded` — no further action.").

## File Format

```markdown
---
type: brainstorm
pipeline: spark
topic: "<session topic>"
status: open        # open | promoted | discarded
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
promoted: []        # paths populated when status → promoted (e.g., [spec/<id>-<slug>, usecase/<id>-<slug>])
tags: []
---

## Ideas

### Context

Why this brainstorming was needed. Background, constraints, goals.

### Discussion Journey

Key turning points, rejected directions and why, how the conversation arrived at the final ideas.

### Theme: <theme name>

- **<Idea title>**: <1-2 sentence description>
- **<Idea title>**: <1-2 sentence description>

### Theme: <theme name>

- **<Idea title>**: <1-2 sentence description>
```

Brainstorm body shape requires the `## Ideas` section; `## Notes` and `## Change Logs` are optional. Research findings, TODOs, Constraints, Open Questions, etc. are H3+ headings inside `## Ideas` (or `## Notes` if you prefer to separate them). H1 (`# Title`) is forbidden in body — the topic lives in frontmatter.
