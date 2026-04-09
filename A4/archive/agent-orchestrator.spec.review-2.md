## Spec Review Report -- Architecture Phase

**Scope:** Architecture
**Sections reviewed:** Architecture (External Dependencies, Component Overview, Components, Sequence Diagrams)
**Cross-checked against:** Functional Requirements (FR-1 through FR-7), Domain Model, Technology Stack
**Criteria applied:** #1 Behavior Coverage (component mapping, sequence diagrams), #4 Ownership, #6 Technical Claim Verification, #7 Consistency
**Total items reviewed:** 7 FRs, 9 components, 2 external dependencies, 4 sequence diagrams

**Verdict:** NEEDS REVISION

---

### 1. Behavior Coverage

#### FR-1 -> SpawnOrchestrator, ChatSkill, SessionStartHook, iTerm2Launcher: Child session spawn with context handoff
- Component mapping: OK -- FR-1 steps are clearly distributed across ChatSkill (gather input), SpawnOrchestrator (orchestrate spawn), SessionStartHook (bootstrap), iTerm2Launcher (terminal).
- Sequence diagram: OK -- spawn flow diagram covers steps 1-7 of FR-1 processing.
- GAP -- FR-1 step 8 (main session confirms child reached `active` within 30s) has no sequence diagram coverage. The confirmation is delegated to FR-7 (SessionMonitorHook), but the spawn sequence diagram ends at `SO --> CS: child_id, topic, tree_path` without showing how the main session learns the child is active. A developer would have to piece together that a separate FileChanged hook fires asynchronously. Suggest: add a note in the spawn sequence diagram referencing FR-7 for the handshake confirmation step.

#### FR-2 -> SessionEndHook, SessionMonitorHook: Control session termination
- Component mapping: OK -- SessionEndHook handles step 5, SessionMonitorHook handles step 6.
- Sequence diagram: GAP -- No sequence diagram exists for the termination flow. FR-2 steps 1-4 are LLM-driven (orchestrator prompt instruction), but steps 5-6 involve concrete component interactions (SessionEndHook writes status, FileChanged triggers SessionMonitorHook, main session is notified). A developer implementing SessionEndHook and SessionMonitorHook would benefit from seeing how these components interact for the termination path. Suggest: add a sequence diagram for the termination notification flow (SessionEndHook -> SessionTreeStore -> SessionMonitorHook -> main session).

#### FR-3 -> RegisterResultCommand, SessionMonitorHook: Result file registration and delivery
- Component mapping: OK -- RegisterResultCommand handles steps 1-3, SessionMonitorHook handles step 4.
- Sequence diagram: GAP -- No sequence diagram for the registration flow. The component descriptions cover this, but a developer implementing RegisterResultCommand has to infer the interaction pattern from prose. Suggest: add a brief sequence diagram showing RegisterResultCommand -> SessionTreeStore -> (FileChanged trigger) -> SessionMonitorHook.

#### FR-4 -> SpawnOrchestrator, SessionStartHook, iTerm2Launcher: Resume child session
- Component mapping: OK -- SpawnOrchestrator resume flow dispatch table covers all status combinations.
- Sequence diagram: GAP -- No sequence diagram for the resume flow. The dispatch table in SpawnOrchestrator is good, but the SessionStartHook behavior on resume (status==terminated/crashed branch) is only shown in the SessionStartHook sequence diagram. The end-to-end resume flow from user request through SpawnOrchestrator to iTerm2Launcher to SessionStartHook is not diagrammed. Suggest: add a sequence diagram or note that the SessionStartHook diagram's `resume` branch covers this.

#### FR-5 -> SessionListCommand: List child sessions
- Component mapping: OK
- Sequence diagram: not needed (simple read-and-format)

#### FR-6 -> ContextDriftHook: Detect context drift
- Component mapping: OK
- Sequence diagram: not needed (simple read-compare-notify)

#### FR-7 -> SessionMonitorHook: Monitor session-tree changes
- Component mapping: OK
- Sequence diagram: not needed (detection logic is tabular, well-defined)

#### External Dependencies
- iTerm2 (`it2` CLI + `iterm2` Python API): OK -- purpose stated (terminal pane creation, session activation), used by FR-1 and FR-4.
- Claude Code CLI: OK -- flags specified (`--session-id`, `--resume`, `--append-system-prompt-file`).
- GAP -- No fallback behavior specified for either dependency. What happens if `it2` is not installed (vs iTerm2 not running, which FR-1 handles)? What happens if `claude` CLI is not found? These are different from "iTerm2 not running." Suggest: add error handling for missing CLI tools.

#### Authorization
- OK -- Single-user system with one actor (User). No authorization matrix needed.

---

### 4. Ownership

#### SessionTreeStore
- OK -- Responsibility clear: data access layer with atomic read-modify-write. API table defines exactly what each operation does and who calls it.

#### SpawnOrchestrator
- OK -- Responsibility clear: child session creation + resume dispatch. File path specified. CLI args interface defined.
- UNCLEAR -- The `generate_prompt()` function reads persona from `prompts/<persona>.txt` and appends "orchestrator instructions." The orchestrator instructions content is listed as an open item ("Exact prompt text not written"). A developer implementing this function needs to know at minimum the structure/sections of the orchestrator instructions, even if exact wording is TBD. Currently the only guidance is scattered across FR-2 and FR-3 orchestrator prompt instruction boxes. Suggest: consolidate the orchestrator instruction requirements into a single section or template that `generate_prompt()` can use.

#### iTerm2Launcher
- OK -- Two functions with clear signatures. `launch_pane` handles both new and resume. `activate_pane` handles tab switching for already-running sessions.

#### SessionStartHook
- OK -- Sequence diagram clearly shows both new-session and resume branches.

#### SessionEndHook
- OK -- Simple and well-defined.

#### SessionMonitorHook
- OK -- Detection table is comprehensive. Snapshot mechanism is well-specified.

#### ContextDriftHook
- OK -- Processing steps are clear. Main session exclusion logic is well-explained.
- UNCLEAR -- Matcher configuration: the spec says "Broad matcher (e.g., `.`)" but the hook configuration JSON format is not shown. A developer needs to know how to configure the FileChanged hook matcher in `plugin.json` or the hooks configuration. The SessionMonitorHook matcher (`session-tree.json`) is also not shown in configuration format. Suggest: show the hooks JSON configuration for both FileChanged hooks (or reference existing config).

#### RegisterResultCommand
- OK -- SKILL.md content shown. Script interface defined. Error handling specified.

#### SessionListCommand
- OK -- SKILL.md content shown. Script interface defined.

#### ChatSkill
- UNCLEAR -- Described as "Multi-step conversational flow" with "Spec changes from current code" listed, but the actual SKILL.md content is not shown. The current `/chat` skill presumably has step-by-step instructions for the LLM. A developer needs to know what the SKILL.md content should say after applying the spec changes (persona instead of skill, no result patterns, nesting guard, bootstrap-prompt-snippet instead of additional-context). Suggest: show the updated SKILL.md content or at minimum the updated step list.

#### Unowned behavior
- GAP -- FR-4 step 3 says "If session is `active` or `resumed` (still running) -> inform user the session is already running and activate its existing iTerm2 session." The SpawnOrchestrator resume dispatch table covers `active/resumed + pid alive -> activate_pane(topic)`. But there is also `active/resumed + pid NOT alive -> launch_pane(resume=True)`. This second case means the status is stale (actually crashed). After launching with resume, should SessionStartHook update status from `active` to `resumed`? The SessionStartHook sequence diagram only handles `status == pending` (new) and `status == terminated | crashed` (resume). It does not handle `status == active` or `status == resumed` when the hook fires during a resume. Suggest: clarify what SessionStartHook does when it receives a session that has status `active` (stale) -- should it transition to `resumed` and increment `resumeCount`?

---

### 6. Technical Claim Verification

#### SUSPECT -- FileChanged hooks cannot inject additionalContext

The spec's overview states: "Hook scripts output JSON to stdout with a `hookSpecificOutput.additionalContext` field. Claude Code renders stdout output as injected context in the session's conversation."

This mechanism is fundamental to FR-6 (ContextDriftHook) and FR-7 (SessionMonitorHook), both of which are FileChanged hooks that rely on stdout `additionalContext` to notify the user.

**According to official Claude Code hooks documentation** (https://code.claude.com/docs/en/hooks), the decision control table shows:

| Hook Event | additionalContext Support |
|---|---|
| SessionStart | Yes |
| UserPromptSubmit | Yes |
| PreToolUse | Yes |
| PostToolUse | Yes |
| Notification | Yes |
| **FileChanged** | **No -- "Shows stderr to user only"** |

FileChanged hooks are documented as fire-and-forget: stdout is not processed for context injection, and stderr is only shown to the user (not to Claude). This means:

- **FR-6 (ContextDriftHook):** The "stdout notification" mechanism described will not inject context into the child session's conversation. The user sees nothing; Claude sees nothing.
- **FR-7 (SessionMonitorHook):** The "stdout notification" mechanism will not inject context into the main session's conversation. Status change notifications will not reach the main session LLM.

**Note:** The existing codebase (`plugins/spawn/hooks/session_monitor.py` line 143) already uses `{"additionalContext": body}` in a FileChanged hook. This suggests either (a) the existing code has the same bug and notifications do not actually work, or (b) Claude Code has undocumented behavior that processes FileChanged stdout. The spec should verify empirically whether this works and document the finding.

**Impact:** If FileChanged hooks truly cannot inject context, the entire notification architecture (FR-6 and FR-7) needs redesign. Possible alternatives:
1. Use `Notification` hook event type instead (supports additionalContext)
2. Use a polling approach via UserPromptSubmit hook that checks session-tree.json on each user message
3. Write notifications to a file that a UserPromptSubmit hook reads

Suggest: verify empirically whether FileChanged stdout is injected into Claude's context, then either (a) document the verified behavior with a test case reference, or (b) redesign the notification mechanism.

#### CONFIRMED -- `--append-system-prompt-file` flag exists
Verified in Claude Code CLI reference (https://code.claude.com/docs/en/cli-reference). The flag appends content to the end of the base system prompt from a file. Only one file can be specified per invocation (consistent with spec's interview note about combining persona + orchestrator into one file).

#### CONFIRMED -- `--session-id` and `--resume` flags exist
Verified in Claude Code CLI reference and session management documentation. `--session-id` starts a new session with a specific ID. `--resume` resumes a previous session by ID.

#### CONFIRMED -- `${CLAUDE_SESSION_ID}` skill template variable exists
Verified in official skills documentation (https://code.claude.com/docs/en/skills). Listed in the "Available string substitutions" table.

#### UNVERIFIED -- `${CLAUDE_PLUGIN_ROOT}` in skill shell injection
The RegisterResultCommand SKILL.md uses `${CLAUDE_PLUGIN_ROOT}` in a shell injection line: `!`uv run ${CLAUDE_PLUGIN_ROOT}/skills/register-result/scripts/register_result.py ...`. There is a known issue (https://github.com/anthropics/claude-code/issues/9354) that `${CLAUDE_PLUGIN_ROOT}` works in JSON configurations (hooks, MCP servers) but may not work in command/skill markdown files. The official skills documentation lists `${CLAUDE_SKILL_DIR}` as the supported variable for referencing files relative to the skill directory. Suggest: verify that `${CLAUDE_PLUGIN_ROOT}` resolves in shell injection within SKILL.md, or use `${CLAUDE_SKILL_DIR}/../register-result/scripts/register_result.py` or restructure to use `${CLAUDE_SKILL_DIR}/scripts/register_result.py` (which is more conventional).

#### CONFIRMED -- `fcntl.flock()` for file locking
Standard Python library on macOS/Linux. Already used in existing `session_tree.py`.

#### CONFIRMED -- iTerm2 `it2` CLI and `iterm2` Python API
`it2` CLI is a third-party tool for controlling iTerm2 (https://github.com/mkusaka/it2). Supports session creation, split, and management. The `iterm2` Python API is the official iTerm2 scripting API. Both are already used in the existing codebase.

#### UNVERIFIED -- FileChanged hook matcher format for broad matching
The spec says ContextDriftHook uses a "Broad matcher (e.g., `.`)" for FileChanged. The official docs say the matcher field is "a pipe-separated list of basenames" (e.g., `.envrc|.env`). A single `.` as a matcher may not work as expected -- it could match only files literally named `.`, not "any file." The matcher does not appear to support regex patterns. Suggest: verify the exact matcher syntax for "match all files" in FileChanged hooks. If basenames are literal, a broad matcher may need to be a long pipe-separated list of common extensions, or a different approach entirely.

---

### 7. Consistency

#### FR-7 <-> SessionMonitorHook: Crash detection scope
- CONFLICT -- FR-7 Processing step 3 says "Scans all `active` and `resumed` entries" for crash detection. The SessionMonitorHook detections table also says "`active`/`resumed` + pid dead -> `crashed`." However, the existing code (`session_monitor.py` line 82) only checks `child.status == "active"`, not `resumed`. The spec's "Spec changes from current code" section notes "Crash detection: add `resumed` status (not just `active`)" but the existing code has not been updated. This is a known delta, not a contradiction -- but it should be flagged so the developer knows to implement the `resumed` check.

#### FR-7 <-> SessionMonitorHook: Deliverable notification
- CONFLICT (minor) -- FR-7 Processing step 6 says "Detects `resultUpdatedAt` change." The SessionMonitorHook detections table says "`resultUpdatedAt` changed." However, the existing code (line 111) checks `child.status == "active"` and compares `result_files` sets. The spec's "Spec changes from current code" section notes this: "Deliverable notification: detect via `resultUpdatedAt` change (not just active status + resultFiles diff)." Again, a known delta. But the existing `ChildEntry` dataclass does not have `resultUpdatedAt` -- the developer must add it to the schema.

#### Domain Model <-> Architecture: All domain concepts housed in components
- OK -- MainSession, ChildSession, SessionTree -> SessionTreeStore. Persona -> SpawnOrchestrator reads persona files. SessionSystemPrompt -> SpawnOrchestrator generates prompt files.

#### FR-1 <-> SpawnOrchestrator: Nesting guard
- OK -- FR-1 error handling mentions "Spawn attempted from a child session -> reject." SpawnOrchestrator spawn flow sequence diagram shows "nesting guard ($SESSION_TREE set + not main?)."

#### Domain Model state transitions <-> SessionStartHook: Resume from which states
- CONFLICT -- State transition diagram shows `terminated -> resumed` and `crashed -> resumed`. SessionStartHook sequence diagram shows `alt` branch for `status == terminated | crashed`. But `failed_to_start` is a final state per the domain model (no outgoing transition). SpawnOrchestrator resume dispatch table confirms: `failed_to_start -> Resume not possible`. This is consistent. However, the state diagram does NOT show a transition for `active -> resumed` or `resumed -> resumed` (re-resume). SpawnOrchestrator dispatch table shows `active/resumed + pid NOT alive -> launch_pane(resume=True)`, which would trigger SessionStartHook. But SessionStartHook's alt branch only handles `terminated | crashed`. If the stale `active` or `resumed` session is launched with `--resume`, SessionStartHook will not match either branch and will be a no-op -- the status will remain `active`/`resumed` but `pid` won't be updated. Suggest: add `active | resumed` to the SessionStartHook resume branch (for stale status recovery), or have SpawnOrchestrator update the status to `crashed` before launching the resume.

#### Architecture Component Diagram <-> Sequence Diagrams: Participant alignment
- OK -- All sequence diagram participants (ChatSkill, SpawnOrchestrator, SessionTreeStore, iTerm2Launcher, SessionStartHook) appear in the component diagram.

#### session-tree.json Schema <-> SessionTreeStore existing code
- OK (expected delta) -- The spec explicitly documents schema changes: `skill` -> `persona`, `resultPatterns` removed, `resumeCount`/`resultUpdatedAt`/`bootstrapPromptSnippet` added, `additionalContext` -> `bootstrapPromptSnippet`. These are intentional changes from the current code.

---

### Summary

- **Technology stack:** OK (reviewed in this context; confirmed key claims)
- **Behavior gaps:** FR-2 (no termination sequence diagram), FR-3 (no registration sequence diagram), FR-4 (no end-to-end resume sequence diagram), FR-1 step 8 (handshake confirmation not shown in spawn diagram)
- **Undeclared external dependencies:** None
- **Authorization issues:** None (single-user system)
- **Imprecise language:** None significant
- **Unhandled errors/edges:** Missing CLI tool (`it2`, `claude`) not-installed error handling; SessionStartHook does not handle stale `active`/`resumed` status on resume
- **Unclear ownership:** ChatSkill updated content not shown; orchestrator instruction template not consolidated; hook configuration JSON not shown
- **Missing interface contracts:** N/A (status: draft)
- **UI grouping issues:** N/A (non-UI)
- **Unverified/suspect technical claims:** FileChanged hooks cannot inject additionalContext (SUSPECT -- breaks FR-6 and FR-7); `${CLAUDE_PLUGIN_ROOT}` in SKILL.md shell injection (UNVERIFIED); FileChanged broad matcher syntax (UNVERIFIED)
- **Cross-section conflicts:** SessionStartHook does not handle stale `active`/`resumed` status (state diagram vs architecture gap)

### Top Priority Fixes

1. **FileChanged hooks and additionalContext (SUSPECT).** The entire notification architecture for FR-6 and FR-7 depends on FileChanged hooks injecting context via stdout. Official documentation says FileChanged hooks do not support `additionalContext`. If this is confirmed, both hooks need a fundamentally different notification mechanism. Verify empirically whether the existing `session_monitor.py` FileChanged hook's stdout output actually reaches Claude's context, then either document the verified behavior or redesign.

2. **SessionStartHook stale status gap.** When SpawnOrchestrator dispatches `active/resumed + pid NOT alive -> launch_pane(resume=True)`, the SessionStartHook only handles `pending`, `terminated`, and `crashed` branches. A session with stale `active` or `resumed` status will not have its status updated or `pid` refreshed. Either add these states to the SessionStartHook resume branch, or have SpawnOrchestrator mark the entry as `crashed` before launching.

3. **FileChanged matcher syntax for ContextDriftHook.** The spec says "Broad matcher (e.g., `.`)" but the official docs describe matchers as "pipe-separated list of basenames." A `.` matcher may only match files literally named `.`. Verify the matcher syntax and document how to achieve "match all files" for context drift detection.
