---
type: review-report
source: agent-orchestrator.usecase.md
revision: 9
reviewed: 2026-04-04
---

## Use Case Review Report

**Total use cases reviewed:** 17
**UCs passed:** 7 / 17
**Actors with issues:** 0
**System completeness:** SUFFICIENT

### Actors Review
- User: OK
- Main Session: OK
- Child Session: OK

All actors are referenced by at least one UC. Types and roles are filled in. No orphan actors. No privilege splits (single-user system with `owner` role). System actors have automated triggers consistent with their type.

### Cross-UC Findings

#1: MISUSED RELATIONSHIP — `UC1 ..> UC6 : <<extend>>` in diagram. UC-1 (conversation-first) does not extend UC-6 (session termination) in the UML sense. They are independent behaviors in the same group that reinforce each other. The `<<extend>>` arrow should be removed; the reinforcement `[UC-1] -> [UC-6]` in the Relationships section is sufficient.

#2: MISSING UC in diagram — The dependency `[UC-2] -> [UC-15]` (dashboard shows child sessions; spawning creates entries) is documented in the Relationships section but has no corresponding arrow in the PlantUML diagram. Add `UC15 ..> UC2 : <<extend>>`.

#3: SYSTEMIC IMPLEMENTATION LEAK — 10 UCs contain implementation-level language in flow steps (UC-2, UC-7, UC-8, UC-9, UC-10, UC-11, UC-12, UC-14, UC-17, UC-18). This is the highest-impact finding and is detailed per-UC below. The pattern: flow steps describe system internals (metadata, change records, configuration, prompts) instead of observable actions or results.

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
- Size: OK — 9 steps is large but all serve the single goal of creating a named child session
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: IMPLEMENTATION LEAK — Step 7 "Session metadata (name, ID) is recorded for future reference" uses system jargon. Suggest: "The session name and identity are saved so the main session can find it later." Step 6 "in a separate terminal" references specific technology. Suggest: "in a separate workspace."
- Outcome: "session metadata is recorded for main session access" — same jargon. Suggest: "the main session can locate and communicate with the child session by name"
- Overlap: OK
- Cross-UC: —
- **UC Verdict: NEEDS REVISION**

#### UC-3: Report child session status
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK — "publishes" and "retrieves" are acceptable system-actor verbs describing observable inter-session communication
- Abstraction: OK
- Outcome: OK
- Overlap: OK
- Cross-UC: —
- **UC Verdict: PASS**

#### UC-4: Access child result files
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

#### UC-5: Investigate child session history
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

#### UC-6: Control session termination
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: OK
- Outcome: OK
- Overlap: OK
- Cross-UC: #1 (UC1 ..> UC6 extend arrow is semantically incorrect)
- **UC Verdict: PASS**

#### UC-7: Inject skill at session startup
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: INCOMPLETE — Step 3 "retrieves the skill's content" and step 4 "loaded into the child session's configuration" describe system internals. What the user observes is that the child session starts behaving according to the skill.
- Abstraction: IMPLEMENTATION LEAK — Step 4 "Skill content is loaded into the child session's configuration." Suggest: "The child session is set up with the skill active." Step 3 "Main session retrieves the skill's content." Suggest: "Main session prepares the skill for the child session."
- Outcome: OK
- Overlap: OK
- Cross-UC: —
- **UC Verdict: NEEDS REVISION**

#### UC-8: Track file changes
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: IMPLEMENTATION LEAK — Step 3 "File path, change type (created/modified/deleted), and timestamp are recorded" describes data schema. Suggest: "The change is recorded with enough detail to identify the file and what happened." Step 4 "stored in the session's change record" uses implementation term. Suggest: "The change is added to the session's running list of file activity."
- Outcome: OK
- Overlap: OK
- Cross-UC: —
- **UC Verdict: NEEDS REVISION**

#### UC-9: Identify result files
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: IMPLEMENTATION LEAK — Step 2 "reviews the file change log" uses implementation term. Suggest: "reviews which files were created or changed during the session."
- Outcome: OK
- Overlap: OK
- Cross-UC: —
- **UC Verdict: NEEDS REVISION**

#### UC-10: Deliver results to main session
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: IMPLEMENTATION LEAK — Step 3 "retrieves the deliverable file path and metadata" uses jargon. Suggest: "retrieves the deliverable file and its description." Step 4 "adds the file to its available resources" is vague system internal. Suggest: "makes the file accessible for use in the main conversation."
- Outcome: OK
- Overlap: OK
- Cross-UC: —
- **UC Verdict: NEEDS REVISION**

#### UC-11: Resume interrupted session
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: IMPLEMENTATION LEAK — Step 2 "retrieves the persisted session state (conversation history, file changes, child session information)" uses implementation language. Suggest: "retrieves the saved session information (what was discussed, what files were produced, which child sessions existed)." Step 3 "restores the session context" — suggest: "rebuilds the session so it matches where the user left off."
- Outcome: OK
- Overlap: OK
- Cross-UC: —
- **UC Verdict: NEEDS REVISION**

#### UC-12: Handle child session failure
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: IMPLEMENTATION LEAK — Step 1 "no status updates received within the configured timeout period" references system configuration. Suggest: "a child session has not responded for an unusually long time."
- Outcome: OK
- Overlap: OK
- Cross-UC: —
- **UC Verdict: NEEDS REVISION**

#### UC-14: Hand off context to session
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: IMPLEMENTATION LEAK — Step 3 "includes the context summary in the child session's initial prompt" references system internals. Suggest: "passes the context summary to the child session so it's available from the start."
- Outcome: OK
- Overlap: OK
- Cross-UC: —
- **UC Verdict: NEEDS REVISION**

#### UC-15: Monitor child session dashboard
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: OK
- Outcome: OK
- Overlap: OK
- Cross-UC: #2 (missing UC-2 → UC-15 arrow in diagram)
- **UC Verdict: PASS**

#### UC-16: Inspect child session details
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

#### UC-17: Cancel child session task
- Size: OK
- Actor: OK
- Goal: OK
- Situation: IMPLEMENTATION LEAK — "e.g., bash script" references specific technology. Suggest: "e.g., a long-running operation"
- Flow: OK
- Abstraction: OK (situation issue noted above)
- Outcome: OK
- Overlap: OK
- Cross-UC: —
- **UC Verdict: NEEDS REVISION**

#### UC-18: Force terminate child session
- Size: OK
- Actor: OK
- Goal: OK
- Situation: OK
- Flow: OK
- Abstraction: IMPLEMENTATION LEAK — Step 4 "Session metadata is updated to reflect terminated status." Suggest: "The session is marked as terminated so the dashboard and main session reflect the change."
- Outcome: OK
- Overlap: OK
- Cross-UC: —
- **UC Verdict: NEEDS REVISION**

### System Completeness

**Completeness: SUFFICIENT**

The 17 use cases cover session lifecycle end-to-end: creation (UC-2), configuration (UC-7, UC-14), monitoring (UC-3, UC-15, UC-16), result flow (UC-4, UC-5, UC-8, UC-9, UC-10), control (UC-6, UC-17, UC-18), recovery (UC-11, UC-12), and conversational quality (UC-1, UC-6).

**User journey continuity:** Each actor can accomplish their goals end-to-end. The user can create sessions, monitor them, inspect them, cancel or terminate them, and access results. Child sessions track files, identify deliverables, and deliver results. The main session monitors, collects, and recovers.

**Data entity coverage:**
- Sessions: Create (UC-2), Monitor (UC-3, UC-15, UC-16), Cancel (UC-17), Terminate (UC-18), Resume (UC-11) — complete
- Deliverables: Track (UC-8), Identify (UC-9), Deliver (UC-10), Access (UC-4) — complete
- Context: Hand off (UC-14), Investigate (UC-5) — complete

No critical gaps found. Excluded ideas (retract results, clean up history, discover skills) are reasonable deferrals with documented rationale.

### Summary
- **UCs needing revision:** UC-2, UC-7, UC-8, UC-9, UC-10, UC-11, UC-12, UC-14, UC-17, UC-18
- **Actors needing attention:** None
- **Cross-UC findings:** 3 (#1 misused extend, #2 missing diagram arrow, #3 systemic implementation leak across 10 UCs)
- **System completeness:** SUFFICIENT — no gaps requiring new UC candidates
