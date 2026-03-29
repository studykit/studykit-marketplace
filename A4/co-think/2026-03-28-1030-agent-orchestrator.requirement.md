---
type: requirement
pipeline: co-think
topic: "interactive agent/prompt use cases"
date: 2026-03-28
status: final
revision: 3
last_revised: 2026-03-29
covers:
  - non-ui
tags: []
---
# Functional Specification: interactive agent/prompt use cases
> Source: [2026-03-27-1500-agent-orchestrator.story.md](./2026-03-27-1500-agent-orchestrator.story.md)

## Overview
Two layers for Claude Code's interactive agent system. First, a thin behavioral layer (conversation-first attitude) that sets the LLM's conversational stance when loaded as a system prompt. Second, an agent orchestrator that enables the main session to spawn, manage, and collect results from child sessions — each a dedicated interactive conversation running in a separate iTerm2 tab. Child sessions are user-facing interactive sessions, not background automation.

## Job Stories Reference
1. **[STORY-7]. Conversation-first attitude at session start** — When I start a Claude session to explore an idea or discuss a topic, I want to load a system prompt that instructs the LLM to ask clarifying questions before acting, so I can get results that actually match what I meant, not what the LLM assumed.
2. **[STORY-9]. Spawn a dedicated child session** — When the main session encounters a sub-problem, I want to spawn a child session with the interactive prompt loaded, so I can have specialized conversations in a dedicated session.
3. **[STORY-10]. Automated information exchange between sessions** — When a child session is running, I want hooks to automatically exchange information between sessions, so I can keep the main session aware of child session progress.
4. **[STORY-12]. Child session result file accessible to main session** — When I finish a child session, I want the result file path automatically registered with the main session, so I can reference the output directly.
5. **[STORY-13]. Child session conversation history investigation** — When I want to review a past child session, I want the main session to read that session's history via a sub-agent, so I can understand the reasoning behind the output.
6. **[STORY-14]. User controls session termination** — When I'm in a child session, I want the LLM to suggest wrapping up when appropriate while leaving the final decision to me, so I can keep exploring as long as I need. *(Already covered by [FR-16] — conversation-first behavioral layer includes session termination rules.)*
7. **[STORY-15]. Skill injection at child session startup** — When I create a child session with a specific skill, I want that skill injected at startup, so I can start in the right structured dialogue mode.

## Implementation
- [x] [FR-16]. Conversation-first behavioral layer — [92c7b8a]
- [x] [FR-17]. Child session spawn
- [x] [FR-18]. Child session result delivery on termination
- [x] [FR-19]. Child session conversation history investigation

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
      "modifiedFiles": ["<all file paths modified by Write/Edit, recorded by PostToolUse hook>"],
      "resultFiles": ["<key deliverable paths, registered by LLM nudge + user approval or user directive>"],
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
[FR-16]: https://github.com/studykit/studykit-plugins/issues/16
[FR-17]: https://github.com/studykit/studykit-plugins/issues/17
[FR-18]: https://github.com/studykit/studykit-plugins/issues/18
[FR-19]: https://github.com/studykit/studykit-plugins/issues/19
[92c7b8a]: https://github.com/studykit/studykit-plugins/commit/92c7b8a
