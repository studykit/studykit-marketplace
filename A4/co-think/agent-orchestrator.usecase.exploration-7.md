---
type: exploration-report
source: agent-orchestrator.usecase.md
explored: 2026-04-02
---

## Exploration Report

**Perspectives explored:** 5
**UC candidates found:** 8

### Usage Environment
- **Mobile:** not applicable
  - This is a CLI-based tool running in terminal sessions. Mobile usage is not a realistic context.
- **PC/Desktop:** applicable
  - Existing UCs adequately cover the desktop/terminal workflow. The multi-terminal model (main session + child sessions in separate terminals) is inherently desktop-oriented. No gaps found.
- **Tablet:** not applicable
  - Same reasoning as mobile — CLI terminal tool.

### User Proficiency
- **First-time user:**
  - The system has no onboarding or guided discovery flow. UC-1 establishes conversation-first behavior, but a brand-new user wouldn't know what sessions, skills, or child sessions are, or when to use them. → UC candidate: **"Discover available skills"** — User wants to see what structured dialogue modes are available before spawning a child session, so they can choose the right one without prior knowledge.
  - A first-time user wouldn't know the session naming conventions or what kinds of sub-problems warrant child sessions. → UC candidate: **"Get guided session suggestions"** — User wants the main session to suggest when a sub-problem would benefit from a dedicated child session, rather than having to recognize the opportunity themselves.
- **Regular user:**
  - No UC covers repeated patterns or shortcuts. A regular user who frequently spawns the same type of child session (e.g., always starts with "requirements" skill) has no way to streamline this. → UC candidate: **"Reuse session configuration"** — User wants to quickly spawn a child session using a previously used combination of skill and context, without re-specifying everything each time.
- **Returning after absence:**
  - UC-11 covers resuming an interrupted session, but doesn't address the scenario where the user returns days later and wants to understand the state of multiple past sessions. → UC candidate: **"Review past session landscape"** — User wants to see an overview of all previous sessions (completed, interrupted, failed) and their outcomes to re-orient after time away.

### Collaboration Patterns
- **Handoff:** not applicable
  - This is explicitly a single-user system. The main-to-child session delegation is covered by UC-2 and UC-14, which is internal orchestration rather than multi-person collaboration.
- **Concurrent work:** not applicable
  - Single-user system. Multiple child sessions can run concurrently, but this is covered by the existing session lifecycle UCs (UC-2, UC-3, UC-12).
- **Sharing and visibility:** not applicable
  - Single-user system with no sharing requirements stated.

### Error and Exception Handling
- **Action failure:**
  - UC-12 covers child session failure, and UC-2 covers skill validation failure. However, no UC addresses what happens when the main session itself encounters an error (e.g., hook script fails, session registry becomes corrupted, or a FileChanged event is missed). → UC candidate: **"Recover from hook failure"** — Main Session wants to detect and recover when a hook script fails silently, so that session coordination doesn't break without the user noticing.
- **Recovery:**
  - UC-11 covers session resume after interruption. However, no UC addresses undoing or rolling back a child session's work product. If a child session produces incorrect results that get delivered to main (UC-10), there's no flow for the user to reject or retract those results. → UC candidate: **"Retract delivered results"** — User wants to remove or unmark previously delivered child session results from the main session's available resources when they turn out to be incorrect.
- **Edge cases:**
  - UC-2 handles skill validation before spawning, but no UC covers the scenario where a child session is spawned with the same name as an existing active session. The naming collision is not addressed. → UC candidate: **"Handle session name collision"** — Main Session wants to prevent or resolve naming conflicts when spawning a child session with a name already in use by an active session.
  - No UC covers what happens when the user asks to investigate (UC-5) or resume (UC-11) a session whose transcript or session files have been deleted or are inaccessible. The Risk note on UC-5 acknowledges this dependency but doesn't provide a user-facing flow for when it fails.

### Security and Privacy
- **Authorization:** not applicable
  - Single-user system with no multi-user access control requirements.
- **Data control:**
  - Session transcripts, file change logs, and status files accumulate over time. No UC addresses the user's ability to clean up, archive, or delete session history. → UC candidate: **"Clean up session history"** — User wants to remove old session records, transcripts, and file change logs to manage storage and keep the session registry manageable.
- **Safeguards:**
  - No UC covers confirmation before destructive session operations. For example, if the user requests to resume a session (UC-11) that would overwrite current session state, or if a child session's delivered results would overwrite files the main session has modified. These conflicts are not surfaced to the user for confirmation.

### Summary
- **Total UC candidates:** 8
- **Top candidates:**
  1. **"Discover available skills"** — High impact for onboarding; without this, first-time users can't effectively use UC-7 (skill injection)
  2. **"Review past session landscape"** — Fills the gap between UC-11 (resume one session) and UC-5 (investigate one session) by providing a birds-eye view of all sessions
  3. **"Recover from hook failure"** — Hooks are central to the architecture (status reporting, file tracking, event notification); silent hook failures could undermine the entire system without the user knowing
  4. **"Handle session name collision"** — Naming is a key identifier throughout the system (UC-3, UC-4, UC-5, UC-12 all reference sessions by name); collisions could cause data corruption
  5. **"Reuse session configuration"** — Natural efficiency gain for regular users who repeatedly spawn similar sessions
