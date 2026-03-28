---
type: story
pipeline: co-think
topic: "interactive agent/prompt use cases"
date: 2026-03-27
status: final
revision: 0
tags: []
---
# Job Stories: interactive agent/prompt use cases

## Original Idea
When should the interactive agent and prompt be used? Discover the core value and usage scenarios to refine the file contents.

## Context
- Core problem: LLMs tend to jump to answers before fully understanding the request
- Purpose: ensure sufficient conversation to eliminate ambiguity before taking action
- Usage: loaded via `--system-prompt-file`, `--append-system-prompt-file` (prompt) or `--agent` (agent)
- Role: scaffold for conversational prompts — specific dialogue methods are filled in by skills like co-think-*, spark-*
- Architecture: main session (orchestrator) + child sessions (dedicated conversations via tmux/iTerm2)
- Direction: strip out code execution flow (Explore/plan mode), focus purely on conversational attitude
- Child sessions freely create files, generate code, run mock-html — but session termination is always user-decided
- Main session can view child session list, access result files, and investigate child conversation history via sub-agents
- Skill injection happens at child session startup via system prompt; otherwise users invoke skills directly within the session
- **Scope split**: Story #7 defines the interactive prompt's conversational attitude (standalone behavioral layer). Stories #8–#15 define the **agent orchestrator** — the main session's ability to spawn, manage, and collect results from child sessions.

## Job Stories

### #7. Conversation-first attitude at session start
**When** I start a Claude session (via `--append-system-prompt-file` or `--agent`) to explore an idea or discuss a topic,
**I want to** load a system prompt that instructs the LLM to ask clarifying questions before acting,
**so I can** get results that actually match what I meant, not what the LLM assumed.
[status:: final]

### #8. Spawn & manage child sessions *(parent)*
#### #9. Spawn a dedicated child session
**When** the main session encounters a sub-problem (e.g., a design question or an ambiguous requirement) that warrants a dedicated conversation,
**I want to** spawn a child session (via tmux/iTerm2) with the interactive prompt loaded,
**so I can** have specialized conversations happen in a dedicated session without cluttering the main session.
[status:: final]

#### #10. Automated information exchange between sessions
**When** a child session is running alongside the main session,
**I want to** have hooks automatically exchange information (status, file paths) between the two sessions,
**so I can** keep the main session aware of child session progress without manual copy-pasting.
[status:: final]

### #11. Child session results *(parent)*
#### #12. Child session result file accessible to main session
**When** I finish a child session,
**I want to** have the session's result file path automatically registered with the main session,
**so I can** reference the output file directly from the main session without searching for it.
[status:: final]

#### #13. Child session conversation history investigation
**When** I want to review what happened in a past child session,
**I want to** have the main session read that child session's conversation history via a sub-agent,
**so I can** understand the reasoning behind a child session's output without re-reading the full transcript myself.
[status:: final]

### #14. User controls session termination
**When** I'm in a child session conversation,
**I want to** have the LLM suggest wrapping up when appropriate, while leaving the final decision to end the session entirely to me,
**so I can** keep exploring as long as I need while still getting a nudge when things seem complete.
[status:: final]

### #15. Skill injection at child session startup
**When** I create a child session with a specific skill, or the main session selects one based on context,
**I want to** have that skill's content injected into the child session's system prompt at startup,
**so I can** start the child session already in the right structured dialogue mode.
[status:: final]

## Story Relationships

### Dependencies
- **#9 → #10**: Spawning a child session (#9) must exist before information exchange (#10) is meaningful
- **#9 → #12**: Spawning (#9) is a prerequisite for result file registration (#12)
- **#9 → #13**: Spawning (#9) is a prerequisite for history investigation (#13)
- **#9 → #15**: Spawning (#9) is a prerequisite for skill injection (#15)

### Reinforcement
- **#7 + #14**: Conversation-first attitude (#7) and user-controlled termination (#14) together ensure the LLM never rushes — neither at the start nor at the end
- **#12 + #13**: File access (#12) and history investigation (#13) together give the main session full visibility into child session outputs
- **#10 + #12**: Hook-based exchange (#10) enables automatic result registration (#12)

### Groups
- **Conversational attitude**: #7, #14 — define how the LLM behaves within a session (interactive prompt scope)
- **Agent orchestrator – session lifecycle**: #9, #10, #15 — define how sessions are created and configured
- **Agent orchestrator – session results**: #12, #13 — define how outputs flow back to the main session

## Topics for Next Phase (beyond Job Story scope)
- Session metadata file structure — what fields, format, and location for tracking child sessions
- Hook event design — which events trigger information exchange between sessions
- Child session list storage — how the main session discovers and enumerates past/active child sessions

## Open Questions
*No unresolved questions at this time.*
