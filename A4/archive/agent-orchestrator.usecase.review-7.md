---
type: review-report
source: agent-orchestrator.usecase.md
revision: 7
reviewed: 2026-04-02
---

## Use Case Review Report

**Total use cases reviewed:** 13
**UCs passed:** 3 / 13
**Actors with issues:** 1
**System completeness:** INCOMPLETE

### Actors Review

- User: INCOMPLETE ACTOR — missing Role. Person actors require a Role even in single-user systems. Suggest: `owner` (the user has full control over all sessions and decisions).
- Main Session: OK
- Child Session: OK

### Cross-UC Findings

#1: MISSING RELATIONSHIP IN DIAGRAM — Dependency [UC-2] -> [UC-8] is documented in the Dependencies section ("Spawning a child session creates a context in which file changes are tracked") but has no corresponding arrow in the PlantUML diagram. Add `UC8 ..> UC2 : <<extend>>`.

#2: DEPENDENCY/DIAGRAM MISMATCH — Dependency [UC-2] -> [UC-6] is documented ("Spawning a child session is a prerequisite for child session termination") but has no diagram arrow. The revision 6 changelog explains the `<<extend>>` was intentionally removed because UC-6 applies to both main and child sessions. Either remove the dependency from the text (since UC-6 is broader than child sessions) or add a note to the dependency clarifying it is partial.

#3: SYSTEMIC IMPLEMENTATION LEAK — 10 of 13 use cases reference hook mechanics, status files, FileChanged events, session registry, or transcript file paths in their flow steps. While the Context section establishes hooks as central to the architecture, flow steps should describe observable behavior from the actor's perspective, not the underlying mechanism. A consistent rewriting pass is recommended:
  - "Child session writes to the status file" -> "Child session publishes a status update"
  - "FileChanged hook detects the update" -> "Main session receives the update notification"
  - "Retrieves from the session registry" -> "Looks up by session name"
  - "Hook records metadata" -> "Session metadata is recorded"
  - "Hook validates skill exists" -> "The system verifies the skill exists"
  - "Inserted into the system prompt" -> "Loaded into the session's configuration"
  This preserves the behavior without exposing mechanism. Implementation details belong in Notes fields or the Context section.

### Use Case Review

#### UC-1: Start conversation-first session
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: OK
- Outcome: OK
- Overlap: OK
- Cross-UC: —
- **UC Verdict: PASS**

#### UC-2: Spawn child session
- Size: OK — 8 steps is long but all serve the single goal of creating a child session
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: IMPLEMENTATION LEAK — Step 3: "a hook validates that the skill exists before proceeding" -> suggest: "the system verifies the skill exists before proceeding." Step 6: "A hook records the child session metadata (session name, session ID, transcript file path) to the session registry" -> suggest: "Session metadata (name, ID) is recorded for future reference."
- Outcome: OK
- Overlap: OK
- Cross-UC: #2, #3
- **UC Verdict: NEEDS REVISION**

#### UC-3: Report child session status
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: IMPLEMENTATION LEAK — The entire flow is described in terms of mechanism rather than behavior. Step 1: "writes status updates and file paths to the session's status file" -> "publishes a status update with current progress and file paths." Step 2: "Main session's FileChanged hook detects the status file update" -> "Main session receives the status update notification."
- Abstraction: IMPLEMENTATION LEAK — Steps 1-2 reference "status file" and "FileChanged hook." These are implementation mechanisms; the flow should describe what happens (status is published, notification is received) not how (file write, hook detection).
- Outcome: WEAK — "event-driven notification" is an implementation term in the outcome. Suggest: "The main session has current visibility into child session progress; user can see child status at a glance"
- Overlap: OK
- Cross-UC: #3
- **UC Verdict: NEEDS REVISION**

#### UC-4: Access child result files
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: IMPLEMENTATION LEAK — Step 1: "via FileChanged hook on status update" -> suggest: "via completion notification." Step 3: "retrieves the file paths from the registry" -> suggest: "retrieves the file paths."
- Outcome: OK
- Overlap: OK
- Cross-UC: #3
- **UC Verdict: NEEDS REVISION**

#### UC-5: Investigate child session history
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: IMPLEMENTATION LEAK — Step 2: "transcript file path from the session registry by name" -> suggest: "looks up the child session's conversation history by name."
- Abstraction: IMPLEMENTATION LEAK — "transcript file path" and "session registry" are implementation details.
- Outcome: OK
- Overlap: OK
- Cross-UC: #3
- **UC Verdict: NEEDS REVISION**

#### UC-6: Control session termination
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: OK
- Outcome: OK
- Overlap: OK
- Cross-UC: —
- **UC Verdict: PASS**

#### UC-7: Inject skill at session startup
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: IMPLEMENTATION LEAK — Step 2: "A hook validates that the specified skill exists" -> suggest: "The system verifies the skill exists." Step 3: "retrieves the skill's content from the skill registry" -> suggest: "retrieves the skill's content." Step 4: "inserted into the child session's system prompt" -> suggest: "loaded into the child session's configuration."
- Outcome: OK
- Overlap: OK
- Cross-UC: #3
- **UC Verdict: NEEDS REVISION**

#### UC-8: Track file changes
- Size: OK
- Actor: OK
- Goal: OK
- Situation: IMPLEMENTATION LEAK — "hook-based background process with no user trigger" -> suggest: "Files are being created or modified during a child session's work (automatic background process with no user trigger)"
- Flow: IMPLEMENTATION LEAK — Step 2: "A hook script in the child session detects the change" -> suggest: "The child session detects the change automatically." Step 4: "session's file change log" -> suggest: "session's change record."
- Abstraction: IMPLEMENTATION LEAK — "hook script" and "file change log" are implementation terms.
- Outcome: OK
- Overlap: OK
- Cross-UC: #1, #3
- **UC Verdict: NEEDS REVISION**

#### UC-9: Identify result files
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK — Step 5 mentions "session registry" which is a minor implementation reference, but the step is otherwise clear.
- Abstraction: IMPLEMENTATION LEAK (minor) — Step 5: "marked as deliverables in the session registry" -> suggest: "marked as deliverables."
- Outcome: OK
- Overlap: OK
- Cross-UC: #3
- **UC Verdict: NEEDS REVISION**

#### UC-10: Deliver results to main session
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: IMPLEMENTATION LEAK — Step 1: "writes the deliverable notification to the session's status file" -> suggest: "publishes a deliverable notification." Step 2: "Main session's FileChanged hook detects the status file update" -> suggest: "Main session receives the deliverable notification."
- Abstraction: IMPLEMENTATION LEAK — Same pattern as UC-3: "status file" and "FileChanged hook" in steps 1-2.
- Outcome: IMPLEMENTATION LEAK (minor) — "via event-driven notification" -> suggest: "results flow automatically from child to main."
- Overlap: OK
- Cross-UC: #3
- **UC Verdict: NEEDS REVISION**

#### UC-11: Resume interrupted session
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: IMPLEMENTATION LEAK — Step 2: "retrieves the persisted session state from hook-recorded session files (conversation history, file change log, child session registry)" -> suggest: "retrieves the persisted session state (conversation history, file changes, child session information)."
- Abstraction: IMPLEMENTATION LEAK — "hook-recorded session files" and "child session registry" are implementation terms.
- Outcome: IMPLEMENTATION LEAK (minor) — "session state is fully restored from hook-persisted files" -> suggest: "session state is fully restored."
- Overlap: OK
- Cross-UC: #3
- **UC Verdict: NEEDS REVISION**

#### UC-12: Handle child session failure
- Size: OK
- Actor: OK
- Goal: OK
- Situation: IMPLEMENTATION LEAK (minor) — "including hook script failures such as file tracking" -> suggest: "including failures in background processes such as file tracking."
- Flow: IMPLEMENTATION LEAK — Step 1: "detected via FileChanged hook absence" -> suggest: "detected by the absence of expected status updates within the timeout period."
- Abstraction: IMPLEMENTATION LEAK — "FileChanged hook absence" is an implementation detail.
- Outcome: OK
- Overlap: OK
- Cross-UC: #3
- **UC Verdict: NEEDS REVISION**

#### UC-14: Hand off context to session
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK — Step 3 says "initial prompt" which is mildly implementation-adjacent, but acceptable as it describes the observable startup behavior.
- Abstraction: OK
- Outcome: OK
- Overlap: OK
- Cross-UC: —
- **UC Verdict: PASS**

### System Completeness

**Completeness: INCOMPLETE**

#### Gaps Found
- USABILITY GAP — No UC for listing or viewing all active/past child sessions at a glance. UC-3 provides individual status updates pushed to the main session, but there is no explicit way for the user to ask "show me all my sessions" with their current states. With multiple child sessions, this becomes essential.
- MISSING LIFECYCLE — No UC for explicitly cancelling or aborting a child session mid-work. UC-6 covers graceful termination (user says "let's finish"), and UC-12 covers failure recovery, but there is no path for "stop this child session immediately, I don't need it anymore." The user may want to abandon a session that is heading in the wrong direction without going through the summary/confirmation flow of UC-6.

#### UC Candidates
- "User views all session statuses" (from: USABILITY GAP) — User asks the main session to show a summary of all active and completed child sessions with their current status, key deliverables, and time since last update.
- "User cancels a child session" (from: MISSING LIFECYCLE) — User instructs the main session to immediately stop a child session; partial results are preserved but no summary/confirmation flow is required.

### Summary
- **UCs needing revision:** UC-2, UC-3, UC-4, UC-5, UC-7, UC-8, UC-9, UC-10, UC-11, UC-12
- **Actors needing attention:** User (INCOMPLETE — missing Role)
- **Cross-UC findings:** 3 (#1 missing diagram arrow, #2 dependency/diagram mismatch, #3 systemic implementation leak across 10 UCs)
- **System completeness:** INCOMPLETE — 2 gaps, 2 UC candidates
- **Primary recommendation:** Address cross-UC finding #3 first — a single rewriting pass to replace hook/file/registry references with actor-level descriptions will resolve the majority of individual UC issues simultaneously. The implementation details should move to Notes fields or remain in the Context section where they are already well-documented.
