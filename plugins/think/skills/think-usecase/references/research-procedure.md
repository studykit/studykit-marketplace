# Similar Systems Research Procedure

Research is **not automatic** — only trigger when the user explicitly asks (e.g., "what do similar apps do?", "check competitors", "look up existing solutions", "research this").

## Nudge

After 3+ use cases are confirmed and the conversation reaches a natural pause, offer once:
> "We have N use cases so far. Want me to research similar products in the background to see if there are common features we haven't considered? I can do that while we keep talking."

Only nudge once per session. If the user declines, do not ask again.

## Procedure

If the user agrees:
1. Launch a research subagent via `Agent` with `run_in_background: true`.
2. Prompt the subagent with the current Context and confirmed UC list — ask it to find comparable products and identify features not yet covered.
3. **Continue the interview** — do not wait for research results. Notification arrives automatically when the agent completes.
4. When notified, save the full results per `research-report.md` (in this references directory) with label numbered sequentially. Summarize findings at the next natural break:
   > "The research found these features common in similar systems that we haven't covered yet: [list]. Want to explore any of these?"
5. **Update the working file** — write the research results to the **Similar Systems Research** section. Add the research report file name to the frontmatter `reflected_files` list. Add **Source** fields to any research-derived UCs going forward.
6. If the user picks any, enter the Discovery Loop for those topics. UC candidates the user explicitly declines go into **Excluded Ideas** with the reason discussed.
7. If the user doesn't pick any, record the candidates in Open Questions for future reference.
