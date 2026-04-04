---
type: exploration-report
source: agent-orchestrator.usecase.md
explored: 2026-04-04
---

## Exploration Report

**Perspectives explored:** 5
**UC candidates found:** 3

### Usage Environment
- **Mobile:** not applicable
  - The orchestrator is a terminal-based CLI tool (Claude Code + tmux). Mobile usage is not a meaningful scenario.
- **PC/Desktop:** applicable — no gaps found
  - All 8 UCs assume a desktop terminal environment with multiple panes. This matches the tool's inherent usage context. Power-user desktop features (keyboard shortcuts, multi-window) are handled by the terminal multiplexer itself, not the orchestrator.
- **Tablet:** not applicable
  - Same reasoning as Mobile — the system requires a terminal multiplexer and multiple concurrent CLI sessions.

### User Proficiency
- **First-time user:** applicable — no new gaps (previously explored)
  - A first-time user must understand the session lifecycle (spawn → discuss → terminate → results delivered). UC-2's flow is fairly self-explanatory, and "Get guided session suggestions" was already considered and excluded (exploration-7) as low priority. The existing UCs are self-contained enough for a user who understands Claude Code basics.
- **Regular user:** applicable — no gaps found
  - A power user might want template-based session spawning or saved context configurations. However, "Reuse session configuration" was already explored and excluded (exploration-7, low priority). The existing UC-2 + UC-14 flow accommodates quick spawning for users who know what they want. UC-19 + UC-11 provide efficient session management by name.
- **Returning after absence:** applicable — gap found
  - UC-11 (Resume child session) reopens a terminated session with "its full history intact." But the *artifacts* referenced in the original context handoff (UC-14) may have changed since the session ended — the user edited the design doc, another session modified shared files, or time simply passed. The resumed session starts with stale context but neither the user nor the session knows this.
  - UC-19 shows session state (active/terminated) and original purpose, but not whether the session's context is still current.
  - **Gap:** No UC addresses awareness of context drift when returning to a previously terminated session.
  - → UC candidate: **"Flag context drift on session resume"** — User wants to know whether the artifacts or files referenced in a child session's original context have changed since the session was last active, so they can decide whether to proceed with the existing context or update it.

### Collaboration Patterns
- **Handoff:** applicable — adequately covered
  - UC-14 (context handoff main→child) and UC-10 (result delivery child→main) cover the two-directional handoff. No gap.
- **Concurrent work:** applicable — gap found
  - The system supports multiple child sessions (UC-19 lists them). Each child session independently tracks files (UC-8), identifies results (UC-9), and delivers them (UC-10). But UC-10's flow describes a single delivery: "Main session detects the new deliverable" → "presents the delivered result."
  - When multiple child sessions deliver results around the same time (e.g., user terminates two sessions in quick succession, or two sessions are actively producing deliverables), the main session receives interleaved notifications. There is no UC addressing how the user distinguishes which deliverables came from which session, or how the main session presents a coherent picture when results arrive from multiple sources.
  - **Gap:** UC-10 implicitly assumes a single active delivery stream. Multi-session delivery sequencing and attribution are unaddressed.
  - → UC candidate: **"Review deliverables by session"** — User wants to see deliverables grouped by their originating child session so they can understand which session produced what, especially when multiple sessions have delivered results.
- **Sharing and visibility:** not applicable
  - Single-user system. No external sharing actors.

### Error and Exception Handling
- **Action failure:** applicable — gap found
  - UC-12 (Handle child session failure) was excluded because "interactive sessions have the user present to handle issues directly." However, the user is often *not* present in the child session — they may be working in the main session or another child session. If a child session crashes or becomes unresponsive while the user is elsewhere, they have no way to learn about it until they either switch to that terminal pane (and see it's dead) or run UC-19 to check session states.
  - UC-11 enables recovery *after* the user discovers the crash, and UC-19 enables discovery *on demand*. But there is no proactive notification.
  - **Gap:** No UC covers the scenario where the user learns about an unexpected child session termination without actively checking. The existing exclusion rationale ("user is present") does not hold when the user is in a different session.
  - → UC candidate: **"Notify user of unexpected session end"** — User wants to be alerted in the main session when a child session terminates unexpectedly (crash, closed terminal, timeout), so they can decide whether to resume it (UC-11) or accept the partial results.
  - *Note:* This overlaps with excluded UC-3 (Report child session status) and UC-12 (Handle child session failure). The distinction is narrow scope — only unexpected termination events, not continuous status monitoring or automated recovery. The existing exclusion rationale should be re-evaluated given that the user works across multiple sessions simultaneously.
- **Recovery:** applicable — adequately covered
  - UC-11 (Resume child session) covers recovery after both graceful and unexpected termination. UC-6 ensures results are delivered before graceful termination. The combination provides adequate recovery coverage.
- **Edge cases:** applicable — no new UC warranted (note below)
  - *Empty session termination:* If a child session is terminated (UC-6) but no files were created or modified (UC-8 tracked nothing), the UC-9 → UC-10 flow has no deliverables to identify or deliver. This is an edge case within UC-6 and UC-9, not a separate UC — UC-9 step 2 ("reviews which files were created or changed") would simply find nothing, and the summary in UC-6 step 2 would reflect that. No new UC needed, but UC-6 and UC-9 flows should handle the empty case gracefully.
  - *Session resumed after results already delivered:* UC-11 reopens a session whose results were already delivered via UC-10. New file changes in the resumed session would be tracked (UC-8) and could be delivered again. This is adequately covered by the existing flow — each session lifecycle independently tracks and delivers.

### Security and Privacy
- **Authorization:** not applicable
  - Single-user system with no role-based access. All sessions belong to the same user.
- **Data control:** not applicable
  - The user owns all sessions and files. No multi-user data visibility concerns.
- **Safeguards:** applicable — no gaps found
  - UC-6 includes a confirmation step (step 4: "User confirms session termination or chooses to continue") before ending a session. UC-9 requires explicit user approval before marking deliverables. These provide adequate safeguards against accidental data loss or premature termination. Destructive operations like deleting session history were already excluded ("Clean up session history" — exploration-7, workaround exists).

### Summary
- **Total UC candidates:** 3
- **Top candidates:**
  1. **"Flag context drift on session resume"** — Addresses a real gap in UC-11: resumed sessions may reference stale artifacts. High impact because context freshness is critical for productive discussion. *(User Proficiency — Returning after absence)*
  2. **"Review deliverables by session"** — Addresses a gap in UC-10 when multiple child sessions deliver results. Moderate impact — becomes important as users adopt multi-session workflows. *(Collaboration — Concurrent work)*
  3. **"Notify user of unexpected session end"** — Challenges the exclusion rationale for UC-12 by noting the user is often in a *different* session. Moderate impact but overlaps with previously excluded UCs; warrants re-evaluation rather than automatic inclusion. *(Error — Action failure)*
