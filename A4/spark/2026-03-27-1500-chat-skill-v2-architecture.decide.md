---
type: decide
pipeline: spark
topic: "Chat Skill v2 - Team-free interactive session architecture"
date: 2026-03-27
status: draft
source:
  - "[[interactive-subagent-design]]"
  - "[[interactive-subagent-implementation]]"
framework: ""
decision: ""
tags: [chat-skill, token-optimization, session-management]
---
# Decision Record: Chat Skill v2 Architecture

## Context
The current `/chat` skill uses Agent Teams (TeamCreate → Agent teammate → SendMessage → TeamDelete). The team lead must stay alive waiting for `[SHUTDOWN_REQUEST]`, accumulating `idle_notification` messages in its context window. This wastes tokens proportional to conversation duration, even though the lead does nothing during the conversation.

The proposal is to replace Teams with a standalone `claude` CLI session spawned in a new terminal pane (tmux/iTerm2), eliminating the lead's token consumption entirely.

### Key constraints from prior discussion
- Agent tool cannot loop (returns after 1 response) — confirmed in design doc testing
- Team-based approach is the only way to get persistent multi-turn conversation with split-pane UI in current Claude Code
- New approach: spawn `claude` CLI directly in a new pane, with SessionEnd hook for metadata capture
- Session info should be stored at `$CLAUDE_PROJECT_DIR/.interactive/<main-session>/<chat-session>/`
- iTerm2 pane splitting should use `it2` CLI (not osascript)

## Success Criteria
*To be confirmed with user.*

## Options Considered
*Options will appear here as they are confirmed.*

## Research Findings
*Findings will appear here as research is conducted.*

## Evaluation
*Evaluation will appear here after research is complete.*

## Decision
*Will be filled when the decision is made.*

## Rejected Alternatives
*Will be filled when the decision is made.*

## Next Steps
*Will be filled at the end of the session.*
