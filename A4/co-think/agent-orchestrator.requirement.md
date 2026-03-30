---
type: requirement
pipeline: co-think
topic: "interactive agent/prompt use cases"
created: 2026-03-28
revised: 2026-03-30
revision: 4
status: final
covers:
  - non-ui
tags: []
---
# Functional Specification: interactive agent/prompt use cases
> Source: [agent-orchestrator.story.md](./agent-orchestrator.story.md)

## Overview
Two layers for Claude Code's interactive agent system. First, a thin behavioral layer (conversation-first attitude) that sets the LLM's conversational stance when loaded as a system prompt. Second, an agent orchestrator that enables the main session to spawn, manage, and collect results from child sessions — each a dedicated interactive conversation running in a separate iTerm2 tab. Child sessions are user-facing interactive sessions, not background automation. Result file delivery uses per-session file tracking and LLM+user-driven registration — sessions do not read or modify session-tree.json directly but use skills to access session information.

## Job Stories Reference
1. **[STORY-7]. Conversation-first attitude at session start** — When I start a Claude session to explore an idea or discuss a topic, I want to load a system prompt that instructs the LLM to ask clarifying questions before acting, so I can get results that actually match what I meant, not what the LLM assumed.
2. **[STORY-9]. Spawn a dedicated child session** — When the main session encounters a sub-problem, I want to spawn a child session with the interactive prompt loaded, so I can have specialized conversations in a dedicated session.
3. **[STORY-10]. Automated information exchange between sessions** — When a child session is running, I want hooks to automatically exchange information between sessions, so I can keep the main session aware of child session progress.
4. **[STORY-12]. Child session result file accessible to main session** — When I finish a child session, I want the result file path automatically registered with the main session, so I can reference the output directly.
5. **[STORY-13]. Child session conversation history investigation** — When I want to review a past child session, I want the main session to read that session's history via a sub-agent, so I can understand the reasoning behind the output.
6. **[STORY-14]. User controls session termination** — When I'm in a child session, I want the LLM to suggest wrapping up when appropriate while leaving the final decision to me, so I can keep exploring as long as I need. *(Already covered by [FR-16] — conversation-first behavioral layer includes session termination rules.)*
7. **[STORY-15]. Skill injection at child session startup** — When I create a child session with a specific skill, I want that skill injected at startup, so I can start in the right structured dialogue mode.
8. **[STORY-16]. Session file change tracking** — When files are created or modified during a session, I want all file changes automatically recorded, so I can have a complete record of what the session produced.
9. **[STORY-17]. LLM-based result file identification** — When a child session has been working and producing files, I want the LLM to evaluate which files are key deliverables and suggest them to me, so I can register important outputs without manually tracking every file change.
10. **[STORY-18]. Result file delivery to main session** — When a file is approved as a key deliverable in a child session, I want the main session automatically notified, so I can access child session results from the main session without searching for them.

## Implementation
- [x] [FR-16]. Conversation-first behavioral layer — [92c7b8a]
- [x] [FR-17]. Child session spawn
- [x] [FR-18]. Child session result delivery on termination
- [x] [FR-19]. Child session conversation history investigation
- [ ] [FR-20]. Session file change tracking
- [ ] [FR-21]. LLM-based result file identification
- [ ] [FR-22]. Result file registration
- [ ] [FR-23]. Child session termination notification to main session

## Functional Requirements

### [FR-16]. Conversation-first behavioral layer

> Story: [STORY-7]

**Trigger:** Session start via `--append-system-prompt-file` (interactive.txt) or `--agent` (interactive.md)

**Input:** User messages throughout the session

**Processing:**

**1. Core principle — conversation first, action later**
- Default stance is **conversational**. Never jump to action unless the user explicitly directs it.
- **Action** (requires explicit user direction): any operation that creates, modifies, or deletes files, or executes commands with side effects.
- **Research** (allowed freely): read-only operations — file reads, grep/search, directory listing, web lookups.

**2. Intent-adaptive behavior**

Recognize user intent and adapt:

- **Question** (simple or complex) → Answer directly. Research if needed (read-only operations are OK). No clarification ceremony — do not preface with a summary of understanding or ask whether the user wants an answer.
- **Exploration/discussion** (brainstorm, learning, codebase understanding) → Ask follow-up questions, provide detailed explanations, offer related perspectives. Don't cut the conversation short. No action unless asked.
- **Task** (vague or clear, including direct commands) → Always do a lightweight confirmation before acting: summarize what you're about to do in 1-2 lines and wait for user OK. Then execute. No heavy ceremony — no prescribed mechanics like plan mode or sub-agent spawning.

**3. Session termination**

- The user decides when the conversation ends. The LLM never concludes, wraps up, or suggests ending the session on its own.
- The LLM may suggest next steps or note when a topic seems complete, but the decision to stop is always the user's.

**4. Relationship to skills**

- **Defer structured workflows to skills.** This prompt does not define dialogue methods, steps, or workflow logic. Skills (co-think-*, spark-*, etc.) handle those.
- **Skills override this prompt.** When a skill is loaded alongside this prompt and its instructions conflict, the skill's instructions take precedence. This prompt is a base layer.
- **No obligation to suggest skills.** Whether to suggest a relevant skill when none is loaded is left to the LLM's judgment.

**Output — delivery files:**

Two prompt files with shared core content (the behavioral rules above), split for main vs. child sessions:

1. `plugins/workflow/prompts/interactive.txt` — main session prompt (includes Session Manager instructions)
2. `plugins/workflow/prompts/interactive-child.txt` — child session prompt (same core content, without Session Manager section)

Both files are plain text, loaded via `--append-system-prompt-file`. Delivered as part of the `workflow` plugin.

**Error handling:** N/A (behavioral prompt, no failure modes)

### [FR-17]. Child session spawn

> Story: [STORY-9], [STORY-15]

**Trigger:**
1. User requests via natural language
2. Main session LLM suggests and user approves
3. User invokes via skill (slash command)

**Input:**
- Topic/purpose (required)
- Skill to inject (optional)
- Reference file paths and context summary — main session LLM compiles from current conversation

**Processing:**
1. Main session generates a child session ID and records initial session info (session ID, topic, reference file paths, context summary, skill) to `.claude/sessions/<main-conversation-id>/session-tree.json`
2. Launch a new Claude Code interactive session in a new iTerm2 tab via: `claude --session-id <uuid> --append-system-prompt-file <path-to-interactive-child.txt>`
3. Child session's `SessionStart` hook fires on startup:
   - Reads the child session's entry from `session-tree.json`, identifies its session ID, and outputs the context to stdout (including skill invocation if specified) → automatically injected into the conversation context
   - Updates `session-tree.json` with the child session's transcript path (`transcript_path`) and process ID (`pid`)
5. User interacts with the child session directly — an independent conversation separate from the main session

**Session directory:**
- Location: project root `.claude/sessions/<main-conversation-id>/`

**Proposed `session-tree.json` schema:**
```json
{
  "mainSession": {
    "id": "<main session's Claude session ID>",
    "name": "<user-assigned name for search/identification>"
  },
  "children": [
    {
      "id": "<child session's Claude session ID, generated at spawn and used as --session-id>",
      "topic": "<topic/purpose>",
      "status": "pending | active | terminated | crashed | failed_to_start",
      "createdAt": "<ISO 8601 timestamp>",
      "pid": "<Claude Code process ID, recorded by SessionStart hook>",
      "skill": "<injected skill name or null>",
      "transcriptPath": "<recorded by SessionStart hook>",
      "resultUpdatedAt": "<ISO 8601 timestamp, updated when resultFiles changes in Session Change Record>",
      "referenceFiles": ["<file paths>"],
      "additionalContext": "<context summary from main session>"
    }
  ]
}
```

**Output:** An interactive child session opens in a new iTerm2 tab. The main session continues without blocking.

**Error handling:**
- iTerm2 not running: error message to user
- Conversation ID unavailable: fallback handling required
- Specified skill not found: main session LLM or skill verifies the skill exists before spawning. If invalid, inform the user and ask whether to proceed without the skill or specify a different one

**Dependencies:** None (foundational FR)

### [FR-18]. Child session result delivery on termination

> Story: [STORY-10], [STORY-12]

> **⚠️ Plan Change:** The result file delivery mechanism in this FR has been redesigned. Some parts are deprecated and replaced by new FRs. See "FR-18 Plan Change" section below.
>
> **Deprecated:** `resultPatterns`-based automatic matching logic, `resultPatterns` field in session-tree.json
> **Extracted to [FR-23]:** SessionEnd hook (status → terminated), FileChanged hook (main session notification)
> **Replaced by:** [FR-20] (session file change tracking), [FR-21] (LLM-based result file identification), [FR-22] (result file registration), [FR-23] (child session termination notification)

**Trigger:** Child session terminates

**Input:** Child session's result file path(s), termination status

**Processing:**
1. Child session tracks and registers file changes to `session-tree.json` via two mechanisms:
   - **PostToolUse hook (tracking)**: On Write/Edit tool use, hook appends the file path to `children[].modifiedFiles`. No filtering — all file modifications are recorded.
   - **LLM nudge or user directive (deliverables)**: The child session LLM may suggest registering a file as a deliverable when it judges the file to be a key output of the session — not incidental edits. Upon user approval, or when the user directly instructs, the LLM writes the file path to `children[].resultFiles`.
2. Child session's `SessionEnd` hook fires on termination (including Ctrl+D):
   - Updates `children[].status` to `terminated` in `session-tree.json`
   - Triggered for all exit reasons: `prompt_input_exit`, `resume`, `clear`, `logout`, `other`
3. Main session's `FileChanged` hook detects `session-tree.json` modification (matcher: `session-tree.json`, async)
4. Hook reads updated `session-tree.json`, identifies the terminated child session, and returns JSON with `additionalContext` to inject termination info (child session topic, result file paths) into the main session's conversation context

**Output:** Main session automatically becomes aware of child session termination and can access result file path(s) from `session-tree.json`

**Error handling:**
- Child session terminates without result file: status updated to `terminated`, result file path left empty
- `FileChanged` hook fails to trigger: main session can still read `session-tree.json` manually on demand

**Dependencies:** [FR-17]

### [FR-19]. Child session conversation history investigation

> Story: [STORY-13]

**Trigger:** User asks about a past child session's conversation in the main session

**Input:** Child session identifier (topic from `children[].topic` or child session ID from `children[].id`)

**Processing:**
1. Main session locates the child session's transcript path and result file paths from `session-tree.json`
2. Main session LLM checks the transcript size. If the transcript is long, suggest using a sub-agent to read and summarize instead of reading directly — user decides
3. Based on user's choice: read directly or spawn a sub-agent (via Claude Code Agent tool or prompt instruction) to read and summarize the transcript and result files within the main session

**Output:** Answer or summary of the child session conversation

**Error handling:**
- Transcript file not found or deleted: inform user that history is unavailable

**Dependencies:** [FR-17] (session-tree.json with transcript_path)

### FR-18 Plan Change: Result File Delivery Redesign

FR-20/21/22/23 redesign the result file delivery mechanism from [FR-18] (Child session result delivery on termination).

**Deprecated from FR-18:**
- `resultPatterns`-based automatic matching logic (PostToolUse hook pattern matching → resultFiles registration)
- `resultPatterns` field in session-tree.json

**Retained from FR-18 (extracted to FR-23):**
- SessionEnd hook — updates child session status to `terminated`
- FileChanged hook — detects session-tree.json changes → notifies main session

**Replaced by FR-20/21/22:**
- modifiedFiles tracking → moved to per-session `<session-id>.json` file (FR-20)
- resultFiles registration → LLM judgment + user approval + `/register-result` skill (FR-21, FR-22)

### [FR-20]. Session file change tracking
> Story: [STORY-16]

**Trigger:** Write or Edit tool use in a session

**Input:** file_path used by the tool

**Processing:**
1. SessionStart hook records `CLAUDE_CODE_SESSION_ID` to `CLAUDE_ENV_FILE` to expose as environment variable (both main and child sessions)
2. On session start, create `<session-id>.json` with initial state `{"modifiedFiles": []}` (SessionStart hook)
3. On Write/Edit tool use, PostToolUse hook appends file_path to `modifiedFiles` in `<session-id>.json`
4. Duplicate paths are not added (unique file paths only)
5. On new file addition, inject a short filename-only notification into context (e.g., `File tracked: file.md (5 files tracked)`)
6. File changes from Bash tool are not tracked
7. Main session: no `SESSION_TREE` env var → record to `<main-id>.json`. Child session: `SESSION_TREE` env var present → record to `<child-id>.json`

**`<session-id>.json` schema:**
```json
{
  "modifiedFiles": ["path/to/file1.md", "path/to/file2.py"],
  "resultFiles": ["path/to/deliverable.md"]
}
```

**File location:** `.claude/sessions/<main-id>/<session-id>.json`

**Output:** List of unique file paths modified by the session

**Implementation note:** Rename and repurpose existing `post_tool_result_collector.py`. Remove resultPatterns matching logic, convert to modifiedFiles tracking in `<session-id>.json`.

**Error handling:**
- `<session-id>.json` write failure: ignore, no impact on session
- SESSION_TREE env var not set (main session): session directory path needs separate resolution

**Dependencies:** [FR-17] (child session spawn)

### [FR-21]. LLM-based result file identification
> Story: [STORY-17]

**Trigger:** LLM judges naturally in the child session conversation flow at these moments:
- Immediately after a skill writes a final output file
- When the user implies task completion
- When the user explicitly names a file as a deliverable

**Input:** Modified file list from `<child-id>.json` + conversation context

**LLM file access:** PostToolUse hook injects a short filename-only notification on new file addition. LLM reads `<child-id>.json` directly via Read tool when the full list is needed. `<child-id>.json` path is injected by SessionStart hook into the prompt.

**Processing:**
1. LLM evaluates key deliverables based on:
   - Files written by a skill as final output (e.g., requirement.md, architecture.md)
   - Files the user explicitly identifies as deliverables
   - Files the LLM judges as key deliverables from conversation context
2. When judged as a key deliverable, propose registration to the user via text (e.g., "Register this file as a key deliverable?")
3. Previously rejected files can be re-proposed if they are central to the session's main work or contain key content
4. Files not in `modifiedFiles` can also be registered if the user specifies them
5. Batch registration of multiple files is allowed
6. On user approval → proceeds to [FR-22]

**Output:** Registration proposal text to the user

**Implementation:** Add judgment criteria and nudge behavior directives to `interactive-child.txt` prompt

**Error handling:**
- `<child-id>.json` missing or read failure: do not nudge (no impact on session)

**Dependencies:** [FR-20] (session file change tracking)

### [FR-22]. Result file registration
> Story: [STORY-18]

**Trigger:** User approves result file registration or directly instructs it

**Input:** File path(s) to register

**Processing:**
1. SessionStart hook records `CLAUDE_CODE_SESSION_ID` to `CLAUDE_ENV_FILE` to expose as environment variable
2. On user approval or direct instruction, invoke `/register-result <file_path>` skill
3. Skill script uses `$CLAUDE_CODE_SESSION_ID` to append file path to `resultFiles` in Session Change Record (`<session-id>.json`)
4. If child session (`$SESSION_TREE` set): also updates `resultUpdatedAt` timestamp in the child entry of session-tree.json → existing `session_monitor.py` FileChanged hook notifies main session

**Implementation required:** `/register-result` skill — script that takes file path as argument, appends it to `resultFiles` in `<session-id>.json`, and updates `resultUpdatedAt` in session-tree.json (child session only)

**Output:** Session Change Record `resultFiles` updated; session-tree.json `resultUpdatedAt` updated (child session) → main session FileChanged hook notification

**Error handling:**
- `<session-id>.json` write failure: notify user of failure
- `CLAUDE_CODE_SESSION_ID` not set: registration not possible, notify user

**Dependencies:** [FR-20] (file change tracking), [FR-21] (LLM judgment and nudge), [FR-17] (child session spawn)

### [FR-23]. Child session termination notification to main session
> Story: [STORY-18]

**Trigger:** Child session terminates

**Processing:**
1. SessionEnd hook — updates the corresponding child entry status to `terminated` in `session-tree.json`
2. FileChanged hook — detects session-tree.json change → notifies main session with termination status; main session reads child's Session Change Record for resultFiles

**Output:** Child session termination info injected into main session context

**Implementation required:** `/session-status` skill — queries session status (child session list, status, etc.). Script reads session-tree.json via `$SESSION_TREE` and child Session Change Records for resultFiles.

**Error handling:**
- SessionEnd hook failure: main session can check child session status via `/session-status`

**Dependencies:** [FR-17] (child session spawn)

## Open Questions
- ~~iTerm2 scripting API details for session creation~~ — Resolved: iTerm2 Python API (`iterm2` package) via `iterm2_launcher.py`
- ~~Concurrent `session-tree.json` writes from multiple child sessions (race condition)~~ — Resolved: Python `fcntl.flock()` based shared/exclusive file locking in `session_tree.py`

<!-- references -->
[STORY-7]: https://github.com/studykit/studykit-plugins/issues/7
[STORY-9]: https://github.com/studykit/studykit-plugins/issues/9
[STORY-10]: https://github.com/studykit/studykit-plugins/issues/10
[STORY-12]: https://github.com/studykit/studykit-plugins/issues/12
[STORY-13]: https://github.com/studykit/studykit-plugins/issues/13
[STORY-14]: https://github.com/studykit/studykit-plugins/issues/14
[STORY-15]: https://github.com/studykit/studykit-plugins/issues/15
[STORY-16]: https://github.com/studykit/studykit-plugins/issues/20
[STORY-17]: https://github.com/studykit/studykit-plugins/issues/21
[STORY-18]: https://github.com/studykit/studykit-plugins/issues/22
[FR-16]: https://github.com/studykit/studykit-plugins/issues/16
[FR-17]: https://github.com/studykit/studykit-plugins/issues/17
[FR-18]: https://github.com/studykit/studykit-plugins/issues/18
[FR-19]: https://github.com/studykit/studykit-plugins/issues/19
[FR-20]: https://github.com/studykit/studykit-plugins/issues/23
[FR-21]: https://github.com/studykit/studykit-plugins/issues/24
[FR-22]: https://github.com/studykit/studykit-plugins/issues/25
[FR-23]: https://github.com/studykit/studykit-plugins/issues/26
[92c7b8a]: https://github.com/studykit/studykit-plugins/commit/92c7b8a
