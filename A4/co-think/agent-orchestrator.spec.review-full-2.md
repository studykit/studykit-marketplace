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

- FR-6 Processing step 1: IMPRECISE -- "matcher omitted or `"*"`" -- the spec says this is "regex on basename" but `"*"` is invalid regex (quantifier without preceding element). The correct regex for "match all files" would be `".*"`. The official docs confirm FileChanged matchers support regex patterns. Suggest: change to `".*"` or document that omitting the matcher achieves the same effect.

- ContextDriftHook component description: Same issue repeated -- "Omitted or `"*"` (regex on basename -- matches all files)" should be `".*"`.

- NotificationRelayHook: OK -- Processing steps are precise with clear queue file path derivation for both main and child sessions.

- FR-7 "Notification queue format" listed as Open Item (Low priority): IMPRECISE -- The `notifications.jsonl` schema is undefined. SessionMonitorHook writes to it, ContextDriftHook writes to it, NotificationRelayHook reads from it. A developer implementing any of these three components would have to guess the JSONL entry format. Suggest: define a minimal schema (e.g., `{"timestamp": "ISO8601", "type": "crash|termination|deliverable|context_drift", "topic": "...", "message": "..."}`).

---

### 3. Error & Edge

#### FR-1: Child session spawn
- Error handling: OK -- Six error cases explicitly handled (iTerm2 not running, conversation ID unavailable, persona not found, topic collision, 30s timeout, nesting guard).
- Boundary: OK -- Topic uniqueness scoped to non-terminated sessions.

#### FR-2: Control session termination
- Error handling: OK -- Ctrl+D mid-conversation case addressed with recovery path via FR-4.
- Edge: UNHANDLED -- What happens if the user closes the iTerm2 tab entirely (not Ctrl+D but the terminal pane itself)? Does SessionEndHook still fire? The Claude Code `SessionEnd` hook fires on session termination, but closing the terminal may kill the process before the hook runs. If the hook doesn't fire, the status remains `active` and is only caught by FR-7's crash detection (pid dead). This should be documented as expected behavior.

#### FR-3: Result file registration
- Error handling: OK -- No arguments, file doesn't exist, write failure, context compaction all addressed.
- Boundary: UNHANDLED -- What happens if the same file is registered twice? The spec says "deduplicated" but doesn't specify whether the `resultUpdatedAt` is updated on a no-op dedup. If it is, SessionMonitorHook would fire a "new deliverables" notification for a file that was already registered. Suggest: clarify whether dedup skips the `resultUpdatedAt` update.

#### FR-4: Resume child session
- Error handling: OK -- Four cases (not found, already active, transcript missing, prompt file missing).
- Edge: OK -- `failed_to_start` now offers new session creation instead of blocking.

#### FR-5: List child sessions
- Error handling: OK

#### FR-6: Detect context drift
- Error handling: OK -- session-tree.json unreadable and empty referenceFiles both handled.
- Edge: UNHANDLED -- What happens if a reference file is deleted (not modified)? FileChanged fires on deletion. The hook compares `file_path` against `referenceFiles`. If the deleted file matches, the notification says "Referenced file X has been modified externally" -- but "modified" is misleading for deletion. Suggest: either distinguish modification from deletion in the notification message, or document that "modified" covers all change types including deletion.

#### FR-7: Monitor session-tree changes
- Error handling: OK -- Lazy detection caveat documented. PID reuse risk acknowledged.
- Edge: OK -- Handshake timeout limitation (requires subsequent session-tree.json write) documented.

#### Domain: Child Session state transitions
- OK -- All states have outgoing transitions except `failed_to_start` (intentionally terminal). The `resumed` state now has both `terminated` and `crashed` outgoing transitions.

---

### 4. Ownership

#### SessionTreeStore
- OK -- Clear responsibility with public API table. All callers identified.

#### SpawnOrchestrator
- OK -- Clear responsibility for spawn and resume. Resume dispatch table is well-structured.
- UNCLEAR -- `generate_prompt()` content requirements. The orchestrator instructions are scattered across FR-2 and FR-3's "Orchestrator prompt instruction" boxes. A developer implementing this function would need to consolidate these into a single prompt. The spec should either consolidate these into a single section or explicitly say "generate_prompt() concatenates the instructions from FR-2 and FR-3."
- **Previous review status:** Previously flagged. Still unresolved.

#### iTerm2Launcher
- OK -- Two functions with clear signatures and behavior.

#### SessionStartHook
- OK -- Sequence diagram covers both new-session and resume branches. The `else resume (status != pending)` branch now covers terminated, crashed, and stale active/resumed cases.
- **Previous review status:** Previously flagged (stale active/resumed gap). Now resolved -- the diagram note says "covers terminated, crashed, and stale active/resumed."

#### SessionEndHook
- OK

#### SessionMonitorHook
- OK -- Detection table is comprehensive. Notification delivery updated to queue + systemMessage pattern.

#### ContextDriftHook
- OK -- Processing steps clear. Main session exclusion well-explained.

#### NotificationRelayHook
- OK -- New component with clear responsibility, trigger, processing, and error handling. Queue file path derivation logic is explicit for both main and child sessions.

#### RegisterResultCommand
- UNCLEAR -- SKILL.md uses `${CLAUDE_PLUGIN_ROOT}` in shell injection: `!`uv run ${CLAUDE_PLUGIN_ROOT}/skills/register-result/scripts/register_result.py ...``. The official skills documentation lists only `${CLAUDE_SKILL_DIR}` and `${CLAUDE_SESSION_ID}` as available string substitutions in SKILL.md. `${CLAUDE_PLUGIN_ROOT}` is an environment variable available in hook commands and MCP/LSP server configs, but there is a known bug ([#9354](https://github.com/anthropics/claude-code/issues/9354)) where it does not work in command/skill markdown files. Suggest: use `${CLAUDE_SKILL_DIR}/../register-result/scripts/register_result.py` or restructure so the script is in the same skill directory and use `${CLAUDE_SKILL_DIR}/scripts/register_result.py`.
- **Previous review status:** Previously flagged as UNVERIFIED. Confirmed as a real issue per GitHub issue #9354.

#### SessionListCommand
- Same issue as RegisterResultCommand -- uses `${CLAUDE_PLUGIN_ROOT}` in SKILL.md shell injection.

#### ChatSkill
- UNCLEAR -- The actual SKILL.md content is not shown. Only "Spec changes from current code" is listed (4 bullet points). A developer implementing the updated `/chat` skill would need to know the full step list after applying these changes. Suggest: show the updated SKILL.md content or at minimum the updated step-by-step flow.
- **Previous review status:** Previously flagged. Still unresolved.

#### Unowned behavior
- OK (resolved) -- SessionStartHook now handles stale `active`/`resumed` status via the `else resume (status != pending)` branch. The note "covers terminated, crashed, and stale active/resumed" clarifies this.

---

### 5. UI Screen Grouping

- N/A -- Non-UI specification.

---

### 6. Technical Claim Verification

#### CONFIRMED -- Notification architecture redesign (FileChanged cannot inject additionalContext)

The previous review flagged this as SUSPECT: "FileChanged hooks cannot inject additionalContext." The spec has been redesigned with a two-stage notification pipeline:
1. FileChanged hooks write to `notifications.jsonl` + output `systemMessage` (universal field)
2. NotificationRelayHook (UserPromptSubmit) reads queue and injects `additionalContext`

This is consistent with official Claude Code hooks documentation:
- FileChanged hooks have "No decision control" and cannot use `additionalContext`
- `systemMessage` is listed as a universal field available to all hooks (described as "Warning message shown to the user")
- UserPromptSubmit hooks DO support `additionalContext`

**Remaining concern:** The official docs describe `systemMessage` as "Warning message shown to the user" but the decision control table says FileChanged "Shows stderr to user only." It is ambiguous whether `systemMessage` from a FileChanged hook is actually displayed. The spec should verify empirically that `systemMessage` output from a FileChanged hook is shown to the user. If it is not, the "immediate user visibility" claim in the notification mechanism description is incorrect, and the user would only see notifications on the next interaction (via NotificationRelayHook).

Source: [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks), [Automate workflows with hooks](https://code.claude.com/docs/en/hooks-guide)

#### SUSPECT -- FileChanged matcher `"*"` (regex on basename)

The spec says ContextDriftHook uses matcher `"*"` and describes it as "regex on basename." In regex, `*` is a quantifier that requires a preceding element. The regex `*` alone is invalid or matches nothing. The correct pattern would be `".*"` (dot-star: any character, zero or more times).

Official docs confirm matchers support regex patterns. Examples use patterns like `mcp__.*__delete.*` (with dot-star, not bare star). The FileChanged matcher filters on "filename (basename of the changed file)."

Suggest: change `"*"` to `".*"` throughout the spec, or document that omitting the matcher entirely achieves the same "match all files" behavior if that is supported.

Source: [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks), [Automate workflows with hooks](https://code.claude.com/docs/en/hooks-guide)

#### SUSPECT -- `${CLAUDE_PLUGIN_ROOT}` in SKILL.md shell injection

RegisterResultCommand and SessionListCommand SKILL.md files use `${CLAUDE_PLUGIN_ROOT}` in shell injection (`` !`uv run ${CLAUDE_PLUGIN_ROOT}/...` ``). The official skills documentation lists only two available string substitutions: `${CLAUDE_SESSION_ID}` and `${CLAUDE_SKILL_DIR}`. `${CLAUDE_PLUGIN_ROOT}` is documented as an environment variable for hooks and MCP/LSP configs, but GitHub issue [#9354](https://github.com/anthropics/claude-code/issues/9354) confirms it does not work in command/skill markdown files.

Suggest: use `${CLAUDE_SKILL_DIR}/scripts/register_result.py` (restructure so scripts are under each skill's own directory) or use a relative path from `${CLAUDE_SKILL_DIR}`.

Source: [Extend Claude with skills](https://code.claude.com/docs/en/skills), [GitHub issue #9354](https://github.com/anthropics/claude-code/issues/9354)

#### CONFIRMED -- `--append-system-prompt-file`, `--session-id`, `--resume` flags
Verified in Claude Code CLI reference. Consistent with spec.

#### CONFIRMED -- `${CLAUDE_SESSION_ID}` skill template variable
Verified in official skills documentation. Listed in "Available string substitutions."

Source: [Extend Claude with skills](https://code.claude.com/docs/en/skills)

#### CONFIRMED -- `fcntl.flock()` for file locking
Standard Python library on macOS/Linux.

#### CONFIRMED -- iTerm2 `it2` CLI and `iterm2` Python API
Already in use in existing codebase.

---

### 7. Consistency

#### FR-2 <-> SessionEndHook: Terminal close behavior
- OK -- FR-2 says "User closes terminal without graceful flow -> SessionEnd hook still fires." This is consistent with SessionEndHook's responsibility. However, as noted in Error & Edge, closing the iTerm2 tab (killing the process) may not trigger SessionEnd. The spec is internally consistent but may not match runtime behavior.

#### FR-6 <-> ContextDriftHook: Matcher specification
- CONFLICT (minor) -- FR-6 Processing step 1 says `"*"` while ContextDriftHook component says `"*"`. Both are consistently wrong. The regex should be `".*"`. Not a cross-section conflict, but a shared error.

#### Domain Model state transitions <-> SessionStartHook: Resume from stale states
- OK (resolved) -- The previous review flagged that SessionStartHook did not handle stale `active`/`resumed` status. The SessionStartHook sequence diagram now uses `else resume (status != pending)` which covers all non-pending states including stale active/resumed. The note "covers terminated, crashed, and stale active/resumed" makes this explicit.
- **Previous review status:** Previously flagged as CONFLICT. Now resolved.

#### FR-7 <-> SessionMonitorHook: Crash detection scope
- OK (resolved) -- Both FR-7 and SessionMonitorHook detections table say `active`/`resumed` + pid dead. The "Spec changes from current code" section notes this is a change from current code (which only checks `active`).

#### FR-7 <-> SessionMonitorHook: Notification delivery
- OK (resolved) -- Both FR-7 and SessionMonitorHook now describe the same notification mechanism: write to queue file + output `systemMessage`. The previous review flagged the `additionalContext` approach; the redesigned pipeline is internally consistent.

#### SpawnOrchestrator dispatch <-> SessionStartHook: failed_to_start resume
- OK -- SpawnOrchestrator says `failed_to_start -> Resume not possible, offer new session`. State diagram shows `failed_to_start` as terminal. Consistent.

#### Architecture Component Diagram <-> Sequence Diagrams: Participant alignment
- OK -- All sequence diagram participants appear in the component diagram. NotificationRelayHook is in the component diagram but not in any sequence diagram (acceptable since its behavior is simple: read queue, output, clear).

#### session-tree.json Schema <-> SessionTreeStore
- OK -- Schema changes documented explicitly in "Spec changes from current code."

#### Overview notification mechanism <-> FR-6/FR-7 <-> Component descriptions
- OK -- The Overview section describes the two-stage pipeline (FileChanged -> queue + systemMessage, UserPromptSubmit -> additionalContext). FR-6, FR-7, SessionMonitorHook, ContextDriftHook, and NotificationRelayHook all reference this same pattern consistently.

---

### Summary

- **Technology stack:** OK
- **Behavior gaps:** FR-2 (no termination sequence diagram), FR-3 (no registration sequence diagram), FR-4 (no end-to-end resume sequence diagram)
- **Undeclared external dependencies:** Missing fallback for `it2` and `claude` CLI not installed
- **Authorization issues:** None (single-user system)
- **Imprecise language:** Orchestrator instruction content undefined (Open Item), notification queue JSONL schema undefined (Open Item), FileChanged matcher `"*"` should be `".*"`
- **Unhandled errors/edges:** iTerm2 tab close vs Ctrl+D behavior, dedup no-op resultUpdatedAt, reference file deletion vs modification notification text
- **Unclear ownership:** ChatSkill updated SKILL.md content not shown, orchestrator instruction template not consolidated, `${CLAUDE_PLUGIN_ROOT}` in SKILL.md does not work
- **Missing interface contracts:** N/A (status: draft)
- **UI grouping issues:** N/A (non-UI)
- **Unverified/suspect technical claims:** FileChanged `systemMessage` user visibility unverified empirically, `"*"` matcher is invalid regex, `${CLAUDE_PLUGIN_ROOT}` in SKILL.md confirmed broken
- **Cross-section conflicts:** None remaining (previous conflicts resolved)

### Previously Flagged Issues -- Resolution Status

| Issue | Previous Verdict | Current Status |
|-------|-----------------|----------------|
| FileChanged hooks cannot inject additionalContext | SUSPECT | **Resolved** -- notification architecture redesigned with two-stage pipeline |
| SessionStartHook stale active/resumed gap | CONFLICT | **Resolved** -- `else resume (status != pending)` covers all non-pending states |
| FileChanged matcher syntax for broad matching | UNVERIFIED | **Partially resolved** -- spec says `"*"` but should be `".*"` |
| `${CLAUDE_PLUGIN_ROOT}` in SKILL.md | UNVERIFIED | **Confirmed broken** -- needs fix |
| SpawnOrchestrator failed_to_start handling | (implicit) | **Resolved** -- offers new session creation |
| No termination sequence diagram (FR-2) | GAP | **Still open** |
| No registration sequence diagram (FR-3) | GAP | **Still open** |
| No resume sequence diagram (FR-4) | GAP | **Partially addressed** (SessionStartHook diagram covers resume branch) |
| External dependency fallback behavior | GAP | **Still open** |
| ChatSkill updated content not shown | UNCLEAR | **Still open** |
| Orchestrator instruction template not consolidated | UNCLEAR | **Still open** |

### Top Priority Fixes

1. **`${CLAUDE_PLUGIN_ROOT}` in SKILL.md shell injection (SUSPECT -- confirmed broken).** RegisterResultCommand and SessionListCommand both use `${CLAUDE_PLUGIN_ROOT}` in shell injection, which does not work in SKILL.md per GitHub issue #9354. These are core commands -- if shell injection fails, `/register-result` and `/sessions` are non-functional. Fix: restructure to use `${CLAUDE_SKILL_DIR}/scripts/...` or place scripts within each skill's own directory.

2. **FileChanged matcher `"*"` is invalid regex (SUSPECT).** The ContextDriftHook matcher is specified as `"*"` in both FR-6 and the component description. In regex, `*` without a preceding element is invalid. Should be `".*"` to match all basenames. If the hook is deployed with `"*"`, it may fail to register as a FileChanged watcher or match nothing, silently disabling context drift detection.

3. **Notification queue JSONL schema undefined (IMPRECISE).** Three components write to or read from `notifications.jsonl` (SessionMonitorHook writes, ContextDriftHook writes, NotificationRelayHook reads), but no schema is defined. A developer implementing any of these components independently would have to guess the entry format and hope it matches the others. Define a minimal schema.
