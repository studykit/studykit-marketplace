## Spec Review Report

**Scope:** Full
**Sections reviewed:** Technology Stack, Functional Requirements, Domain Model, Architecture
**Cross-checked against:** 10 Use Cases (UC-2, UC-6, UC-8, UC-9, UC-10, UC-11, UC-14, UC-19, UC-20, UC-21)
**Total items reviewed:** 7 FRs, 5 domain concepts, 10 components, 2 external dependencies, 2 sequence diagrams
**Previous review:** `agent-orchestrator.spec.review-2.md` (Architecture Phase)
**Verdict:** NEEDS REVISION

---

### 0. Technology Stack

- OK -- Language (Python), runtime (uv), session management (Claude Code CLI), terminal (iTerm2), file locking (fcntl.flock) all specified with rationale and verification notes.

---

### 1. Behavior Coverage

#### UC-2, UC-14 -> FR-1: Child session spawn with context handoff
- FR behavior steps: OK -- All 9 processing steps cover the spawn flow from ID generation through SessionStart hook to active confirmation.
- Sequence diagram: OK -- Spawn flow diagram covers steps 1-7. Step 8 (handshake timeout) is covered by FR-7's detection table.
- Component mapping: OK -- ChatSkill, SpawnOrchestrator, SessionTreeStore, iTerm2Launcher, SessionStartHook all have clear roles.

#### UC-6 -> FR-2: Control session termination
- FR behavior steps: OK -- Steps 1-6 cover LLM-guided wrap-up through SessionEnd hook and FR-7 notification.
- Sequence diagram: GAP -- No sequence diagram for the termination flow. Steps 5-6 involve concrete component interactions (SessionEndHook writes status, FileChanged triggers SessionMonitorHook, SessionMonitorHook writes to notification queue, NotificationRelayHook injects on next user message). A developer would have to mentally trace the notification pipeline across four components. Suggest: add a brief sequence diagram for SessionEndHook -> SessionTreeStore -> SessionMonitorHook -> notification queue -> NotificationRelayHook -> main session.
- **Previous review status:** Previously flagged. Still unresolved.

#### UC-8, UC-9, UC-10 -> FR-3: Result file registration and delivery
- FR behavior steps: OK -- The intentional deviation from UC-8's "no file change missed" is documented with rationale.
- Sequence diagram: GAP -- No sequence diagram for the registration flow. RegisterResultCommand -> SessionTreeStore -> (FileChanged trigger) -> SessionMonitorHook -> notification queue -> NotificationRelayHook is undocumented as a visual flow.
- Component mapping: OK -- RegisterResultCommand and SessionMonitorHook roles are clear.
- **Previous review status:** Previously flagged. Still unresolved.

#### UC-11 -> FR-4: Resume child session
- FR behavior steps: OK -- Processing steps cover all cases (not found, active, multiple matches, launch).
- Sequence diagram: GAP -- No end-to-end resume sequence diagram. The SpawnOrchestrator dispatch table is well-structured, but the flow from user request through SpawnOrchestrator to iTerm2Launcher to SessionStartHook is not diagrammed. The SessionStartHook sequence diagram does cover the resume branch (status != pending), which partially addresses this.
- Component mapping: OK
- **Previous review status:** Previously flagged. Partially addressed (SessionStartHook diagram now covers stale active/resumed), but end-to-end flow still missing.

#### UC-19 -> FR-5: List child sessions
- FR behavior steps: OK
- Component mapping: OK

#### UC-20 -> FR-6: Detect context drift
- FR behavior steps: OK -- 6 processing steps cover the full detection flow.
- Component mapping: OK -- ContextDriftHook with clear responsibility.

#### UC-21 -> FR-7: Monitor session-tree changes
- FR behavior steps: OK -- 7 processing steps with detection table covering crash, timeout, termination, and deliverable notification.
- Component mapping: OK -- SessionMonitorHook as the notification hub.

#### External Dependencies
- iTerm2: GAP -- No fallback behavior specified for `it2` CLI not installed. FR-1 handles "iTerm2 not running" but not "it2 binary not found." A developer would have to guess: does the spawn silently fail, raise a Python exception, or show a specific error message?
- Claude Code CLI: GAP -- No fallback for `claude` binary not found. Same ambiguity.
- **Previous review status:** Previously flagged. Still unresolved.

#### Authorization
- OK -- Single-user system with one actor (User). No authorization matrix needed.

---

### 2. Precision

- FR-1 Processing step 4: IMPRECISE -- "Orchestrator instructions (result delivery behavior: identify deliverables before ending, notify user of key outputs)" -- the parenthetical is helpful but the actual orchestrator instruction content is listed as an Open Item. A developer implementing `generate_prompt()` would not know what to write in the orchestrator instructions section of the Session System Prompt. The spec acknowledges this ("Exact prompt text not written") but it remains a gap for implementation. Suggest: at minimum, provide a structured outline of the orchestrator instructions (sections, key directives, tone constraints).

- FR-1 step 6 vs iTerm2Launcher: IMPRECISE -- FR-1 says "Launch a new Claude Code session in a new iTerm2 tab" but iTerm2Launcher says `launch_pane()` "Creates vertical split pane." A tab and a vertical split pane are different iTerm2 concepts. The developer would implement different iTerm2 API calls depending on which is intended. Suggest: choose one term ("tab" or "vertical split pane") and use it consistently across all FRs and components.

- FR-6 Processing step 1 / ContextDriftHook matcher: IMPRECISE -- The spec says matcher `".*"` (regex on basename). This appears twice (FR-6 and ContextDriftHook component). The spec hedges with "omitted or `".*"`" -- the developer needs a definitive choice. Suggest: pick one approach and state it as the requirement.

- FR-7 snapshot file location: IMPRECISE -- "Hook maintains a snapshot file (`session-tree.last`) alongside session-tree.json." The word "alongside" is ambiguous. Given session-tree.json is at `.claude/sessions/<main-id>/session-tree.json`, "alongside" presumably means `.claude/sessions/<main-id>/session-tree.last`, but this should be stated explicitly.

---

### 3. Error & Edge

#### FR-1: Child session spawn
- Error handling: OK -- Six error cases explicitly handled (iTerm2 not running, conversation ID unavailable, persona not found, topic collision, 30s timeout, nesting guard).
- Boundary: UNHANDLED -- What happens if `session-tree.json` is corrupted (invalid JSON)? SessionTreeStore's `st_read()` "returns empty SessionTree if file absent" but does not address corruption. A developer must decide: treat corrupt file as empty (lose data) or error out? Suggest: document the behavior for invalid JSON.

#### FR-2: Control session termination
- Error handling: OK -- Ctrl+D mid-conversation case addressed with recovery path via FR-4.
- Edge: UNHANDLED -- What happens if the user closes the iTerm2 tab entirely (not Ctrl+D but the terminal window/pane itself)? Does SessionEndHook still fire? Closing the terminal may kill the process before the hook runs. If the hook doesn't fire, the status remains `active` and is only caught by FR-7's crash detection (pid dead). This behavior should be documented as the expected degradation path.

#### FR-3: Result file registration
- Error handling: OK -- No arguments, file doesn't exist, write failure, context compaction all addressed.
- Boundary: UNHANDLED -- What happens if the same file is registered twice? The spec says "deduplicated" but doesn't specify whether `resultUpdatedAt` is updated on a no-op dedup. If it is, SessionMonitorHook would fire a "new deliverables" notification for already-registered files. Suggest: clarify whether dedup skips the `resultUpdatedAt` update.

#### FR-4: Resume child session
- Error handling: OK -- Four cases (not found, already active, transcript missing, prompt file missing).
- Edge: UNHANDLED -- What happens if the user tries to resume a `pending` session? The resume flow dispatch table covers `active/resumed`, `terminated/crashed`, and `failed_to_start`, but `pending` is missing. A session could theoretically be `pending` if the user requests resume immediately after spawn (before SessionStart hook completes). Suggest: add `pending` to the dispatch table (e.g., "inform user session is still starting, wait").

#### FR-5: List child sessions
- Error handling: OK

#### FR-6: Detect context drift
- Error handling: OK -- session-tree.json unreadable and empty referenceFiles both handled.
- Edge: UNHANDLED -- What happens if a reference file is deleted (not modified)? FileChanged fires on deletion. The notification says "Referenced file X has been modified externally" -- but "modified" is misleading for deletion. Suggest: document that "modified" covers all change types, or distinguish modification from deletion.

#### FR-7: Monitor session-tree changes
- Error handling: OK -- Lazy detection caveat documented. PID reuse risk acknowledged.
- Edge: UNHANDLED -- What happens if `session-tree.last` (snapshot file) is missing or corrupt? Presumably it should be treated as "no previous snapshot" (notify for all current state), but this is not stated. Suggest: document the behavior.

#### Domain: Child Session state transitions
- OK -- All states have appropriate transitions. `failed_to_start` is terminal. `terminated` and `crashed` can transition to `resumed`.

---

### 4. Ownership

#### SessionTreeStore
- OK -- Clear responsibility with public API table. All callers identified.

#### SpawnOrchestrator
- OK -- Clear responsibility for spawn and resume. Resume dispatch table is well-structured.
- UNCLEAR -- `generate_prompt()` content requirements. The orchestrator instructions are scattered across FR-2 and FR-3's "Orchestrator prompt instruction" boxes. A developer implementing this function would need to consolidate these into a single prompt file. The spec should either consolidate these into a single section or explicitly say "generate_prompt() concatenates the persona content with orchestrator instructions that cover: [list from FR-2 box] and [list from FR-3 box]."
- **Previous review status:** Previously flagged. Still unresolved.

#### iTerm2Launcher
- OK -- Two functions with clear signatures and behavior.

#### SessionStartHook
- OK -- Sequence diagram covers both new-session and resume branches. The `else resume (status != pending)` branch covers terminated, crashed, and stale active/resumed cases.
- **Previous review status:** Previously flagged (stale active/resumed gap). Now resolved.

#### SessionEndHook
- OK

#### SessionMonitorHook
- OK -- Detection table is comprehensive. Notification delivery uses queue + systemMessage pattern consistently.

#### ContextDriftHook
- OK -- Processing steps clear. Main session exclusion well-explained.

#### NotificationRelayHook
- OK -- New component with clear responsibility, trigger, processing, and error handling. Queue file paths explicitly documented for both main and child sessions.

#### RegisterResultCommand
- OK -- SKILL.md shown with `${CLAUDE_SKILL_DIR}` and `${CLAUDE_SESSION_ID}` substitutions. Script interface is clear.

#### SessionListCommand
- OK -- SKILL.md shown with `${CLAUDE_SKILL_DIR}` and `${CLAUDE_SESSION_ID}` substitutions.

#### ChatSkill
- UNCLEAR -- The actual SKILL.md content is not shown. Only "Spec changes from current code" is listed (4 bullet points). A developer implementing the updated `/chat` skill would need to know the full step list after applying these changes. Suggest: show the updated SKILL.md content or at minimum the updated step-by-step flow.
- **Previous review status:** Previously flagged. Still unresolved.

#### Hook Configuration
- UNCLEAR -- The spec defines 5 hooks with their triggers and matchers, but never shows the actual hook configuration (the JSON entries for `.claude/settings.json` hooks section or equivalent). A developer needs to know: what goes in the hooks configuration, which matchers to use, and whether each hook runs only in main sessions, only in child sessions, or both. The script-side guards (`$SESSION_TREE` checks) handle scoping, but the developer still needs to write the configuration file. Suggest: show the hook configuration entries, even as a summary table mapping hook name -> event -> matcher -> scope.

---

### 5. UI Screen Grouping

- N/A -- Non-UI specification.

---

### 6. Technical Claim Verification

#### CONFIRMED -- `--append-system-prompt-file`, `--session-id`, `--resume` flags
Verified in Claude Code CLI reference. All three flags exist with the described behavior:
- `--append-system-prompt-file`: "Load additional system prompt text from a file and append to the default prompt"
- `--session-id`: "Use a specific session ID for the conversation (must be a valid UUID)"
- `--resume`: "Resume a specific session by ID or name"

Source: [CLI reference - Claude Code Docs](https://code.claude.com/docs/en/cli-reference)

#### CONFIRMED -- FileChanged hooks do NOT support `additionalContext`
The official hooks documentation lists FileChanged under events with "No decision control" -- used for side effects like logging or cleanup. It is NOT in the list of events supporting `additionalContext`. The spec's two-stage notification pipeline (queue file + NotificationRelayHook) is correctly motivated by this constraint.

Source: [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)

#### CONFIRMED -- SessionStart and UserPromptSubmit support `additionalContext`
Both are listed in the events supporting `additionalContext`. This validates the spec's design: SessionStartHook injects initial context, NotificationRelayHook (UserPromptSubmit) injects accumulated notifications.

Source: [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)

#### CONFIRMED -- `${CLAUDE_SESSION_ID}` skill template variable
Listed in "Available string substitutions" in the official skills documentation: "The current session ID. Useful for logging, creating session-specific files, or correlating skill output with sessions."

Source: [Extend Claude with skills - Claude Code Docs](https://code.claude.com/docs/en/skills)

#### CONFIRMED -- `fcntl.flock()` for file locking
Standard Python library on macOS/Linux.

#### UNVERIFIED -- FileChanged `systemMessage` user visibility
The spec claims FileChanged hooks output `systemMessage` for "immediate user visibility." The official docs list `systemMessage` as a universal field available to all hooks. However, the decision control table says FileChanged "Shows stderr to user only." It is ambiguous whether `systemMessage` from a FileChanged hook's JSON stdout is actually displayed to the user, or only stderr output is shown. If `systemMessage` does not work for FileChanged hooks, the "immediate user visibility" claim is incorrect and notifications would only reach the user on the next interaction (via NotificationRelayHook). Suggest: verify empirically.

Source: [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)

#### CONFIRMED -- iTerm2 `it2` CLI and `iterm2` Python API
Noted as "verified: used in existing `iterm2_launcher.py`" -- already in use in the codebase.

---

### 7. Consistency

#### FR-1 "iTerm2 tab" vs iTerm2Launcher "vertical split pane"
- CONFLICT -- FR-1 step 6 says "Launch a new Claude Code session in a new iTerm2 tab" but iTerm2Launcher says `launch_pane()` "Creates vertical split pane." A tab and a vertical split pane are different iTerm2 concepts with different API calls. FR-4 compounds this by saying "activate its existing iTerm2 session (tab or pane, via iTerm2 Python API)." The developer would implement different code depending on which is correct. Suggest: unify the terminology.

#### FR-4 "multiple terminated matches" vs FR-1 uniqueness check
- OK (after analysis) -- FR-4 step 4 says "If multiple terminated matches -> disambiguation list." This is possible because FR-1's uniqueness check only blocks `active`, `resumed`, and `pending` sessions -- terminated entries don't block the topic name. So a user can spawn "design-review", terminate it, spawn another "design-review", terminate it, then try to resume "design-review" and get two matches. The logic is consistent, though a brief note in FR-4 explaining why multiple matches can exist would help the developer.

#### Notification mechanism consistency across all sections
- OK -- The Overview describes the two-stage pipeline. FR-6, FR-7, SessionMonitorHook, ContextDriftHook, and NotificationRelayHook all reference the same pattern (write to queue + systemMessage, inject via additionalContext on UserPromptSubmit). Notification queue schemas are fully defined with JSONL examples.

#### Domain Model state transitions vs FR behavior
- OK -- All state transitions map correctly to FR processing steps and hook responsibilities.

#### Component diagram vs sequence diagrams
- OK -- All sequence diagram participants appear in the component diagram. No orphan components.

#### session-tree.json schema vs component usage
- OK -- All fields referenced by components (status, pid, resultFiles, resultUpdatedAt, referenceFiles, bootstrapPromptSnippet, resumeCount, transcriptPath) are in the schema.

---

### Summary

- **Technology stack:** OK
- **Behavior gaps:** FR-2 (no termination sequence diagram), FR-3 (no registration sequence diagram), FR-4 (no end-to-end resume sequence diagram)
- **Undeclared external dependencies:** Missing fallback for `it2` and `claude` binary not found
- **Authorization issues:** None (single-user system)
- **Imprecise language:** Orchestrator instruction content undefined (Open Item), "tab" vs "pane" inconsistency, FileChanged matcher choice not definitive, snapshot file path not explicit
- **Unhandled errors/edges:** Corrupted session-tree.json, iTerm2 tab close behavior, dedup resultUpdatedAt, pending state in resume dispatch, reference file deletion, missing snapshot file
- **Unclear ownership:** ChatSkill updated SKILL.md content not shown, orchestrator instructions scattered across FRs, hook configuration entries not shown
- **Missing interface contracts:** N/A (status: draft)
- **UI grouping issues:** N/A (non-UI)
- **Unverified/suspect technical claims:** FileChanged `systemMessage` user visibility
- **Cross-section conflicts:** "tab" vs "pane" (FR-1 vs iTerm2Launcher)

### Previously Flagged Issues -- Resolution Status

| Issue | Previous Verdict | Current Status |
|-------|-----------------|----------------|
| FileChanged hooks cannot inject additionalContext | SUSPECT | **Resolved** -- notification architecture redesigned with two-stage pipeline |
| SessionStartHook stale active/resumed gap | CONFLICT | **Resolved** -- `else resume (status != pending)` covers all non-pending states |
| FileChanged matcher `"*"` syntax | SUSPECT | **Resolved** -- spec now uses `".*"` throughout |
| `${CLAUDE_PLUGIN_ROOT}` in SKILL.md | SUSPECT (confirmed broken) | **Resolved** -- SKILL.md now uses `${CLAUDE_SKILL_DIR}` |
| SpawnOrchestrator failed_to_start handling | (implicit) | **Resolved** -- offers new session creation |
| Notification queue JSONL schema undefined | IMPRECISE | **Resolved** -- full schemas defined for main and child session queues with examples |
| No termination sequence diagram (FR-2) | GAP | **Still open** |
| No registration sequence diagram (FR-3) | GAP | **Still open** |
| No resume sequence diagram (FR-4) | GAP | **Partially addressed** (SessionStartHook diagram covers resume branch) |
| External dependency fallback behavior | GAP | **Still open** |
| ChatSkill updated content not shown | UNCLEAR | **Still open** |
| Orchestrator instruction template not consolidated | UNCLEAR | **Still open** |

### Top Priority Fixes

1. **"Tab" vs "pane" inconsistency (CONFLICT).** FR-1 says "new iTerm2 tab" but iTerm2Launcher says "creates vertical split pane." These are different iTerm2 concepts requiring different API calls (`create_tab()` vs `split_pane()`). A developer cannot implement iTerm2Launcher without knowing which one is intended. This also affects FR-4's `activate_pane` -- finding an existing "tab" vs "pane" requires different iteration logic. Fix: choose one and update all references.

2. **Orchestrator instruction content undefined (IMPRECISE).** FR-1's `generate_prompt()` produces the Session System Prompt, which combines persona content with orchestrator instructions. The orchestrator instructions govern FR-2's wrap-up behavior and FR-3's deliverable identification -- core behaviors that the child session LLM depends on. The "Orchestrator prompt instruction" boxes in FR-2 and FR-3 provide bullet-point summaries, but the developer implementing `generate_prompt()` must write actual prompt text that produces reliable LLM behavior. At minimum, consolidate the instruction requirements into one place and provide a structured template.

3. **Hook configuration entries not shown (UNCLEAR).** The spec defines 5 hooks with triggers, matchers, and processing logic, but never shows the hook configuration that registers them with Claude Code. A developer needs to create the hooks configuration (JSON entries specifying event, matcher, command, timeout) for each hook. The spec provides enough information to derive most entries, but the matcher values, timeout settings, and the distinction between main-session-only vs all-session hooks should be explicit. Fix: add a summary table or JSON snippet showing the hook configuration.
