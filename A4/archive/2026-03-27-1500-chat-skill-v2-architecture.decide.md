---
type: decide
pipeline: spark
topic: "Chat Skill v2 - Team-free interactive session architecture"
date: 2026-03-27
status: draft
framework: ""
decision: ""
tags: [chat-skill, token-optimization, session-management]
---
# Decision Record: Chat Skill v2 Architecture
> Source: [interactive-subagent-design.md](./interactive-subagent-design.md), [interactive-subagent-implementation.md](./interactive-subagent-implementation.md)

## Context

The current `/chat` skill uses Agent Teams (TeamCreate → Agent teammate → SendMessage → TeamDelete). The team lead must stay alive waiting for `[SHUTDOWN_REQUEST]`, accumulating `idle_notification` messages in its context window. This wastes tokens proportional to conversation duration, even though the lead does nothing during the conversation.

## Problem

| Aspect | Current (Team-based) | Impact |
|--------|---------------------|--------|
| Lead waits for `[SHUTDOWN_REQUEST]` | Accumulates `idle_notification` in context | Token cost ∝ conversation length |
| TeamCreate/TeamDelete lifecycle | Complex shutdown protocol | Fragile (ghost processes on Ctrl+D) |
| Experimental API dependency | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | Stability risk |

## Success Criteria

1. **Simplicity** — Remove Team API, shutdown protocol, idle_notification handling
2. **Data accessibility** — Main session can richly access chat session info after termination

## Confirmed Design Decisions

### 1. Core Architecture: CLI Session in New Pane

Replace Teams with a standalone `claude` CLI session spawned in a new terminal pane.

```
Main Session                        New Pane (tmux/iTerm2)
─────────────                       ──────────────────────
/chat --agent debugger login bug
  ├─ parse args
  ├─ generate chat-session UUID
  ├─ prepare output dir + system prompt
  ├─ open pane with `claude` command
  └─ return immediately ← DONE       claude session starts
                                        ├─ user converses freely
                                        ├─ user: "exit"
                                        ├─ claude writes summary.md
                                        └─ session ends
                                      SessionEnd hook fires
                                        └─ writes session.json
  (user returns to main pane)
  └─ reads summary.md + session.json
```

**Token savings**: Main session consumption goes from O(conversation_length) to zero.

### 2. Pane Creation

| Terminal | Method |
|----------|--------|
| tmux | `tmux split-window -h '{command}'` |
| iTerm2 | `it2 session split -v` → `it2 session run '{command}'` |
| Neither | Warn user, offer current-pane fallback |

### 3. Session ID Management

| ID | How to obtain |
|----|---------------|
| **Main session ID** | SessionStart hook → `$CLAUDE_ENV_FILE` → `$CLAUDE_CODE_SESSION_ID` |
| **Chat session ID** | Skill generates UUID via `uuidgen` → passed to `claude --session-id <uuid>` |

**Main session ID capture** (SessionStart hook):
```bash
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo "export CLAUDE_CODE_SESSION_ID=\"$SESSION_ID\"" >> "$CLAUDE_ENV_FILE"
fi
```

After this, skill reads `$CLAUDE_CODE_SESSION_ID` via Bash tool.

### 4. Directory Structure

```
$CLAUDE_PROJECT_DIR/.interactive/
└── <main-session-id>/
    ├── session.json              # main session metadata
    ├── <chat-session-1>/
    │   ├── summary.md            # written by chat claude (Write tool)
    │   └── session.json          # written by SessionEnd hook
    ├── <chat-session-2>/
    │   ├── summary.md
    │   └── session.json
    └── ...
```

- **Parent-child relationship**: expressed by directory nesting (no explicit child list needed)
- **Main session.json**: main session metadata (session_id, started_at, etc.)
- **Chat session.json**: written by SessionEnd hook (session_id, transcript_path, reason, ended_at, etc.)
- **summary.md**: written by chat claude when user says "exit/done/bye"
- Multiple chat sessions per main session supported
- Main session can list/reference any child by scanning its directory

### 5. Claude CLI Command Construction

```bash
claude \
  --append-system-prompt-file <output-dir>/system-prompt.txt \
  --agent <name>              # if --agent specified
  --session-id <chat-uuid> \
  --name "chat: <topic>" \
  --settings '{"hooks":{"SessionEnd":[{"hooks":[{"type":"command","command":"CHAT_OUTPUT_DIR=<output-dir> bash ~/.claude/hooks/chat-session-end.sh","timeout":10}]}]}}'
```

Key flags:
- `--append-system-prompt-file`: interactive rules + topic + summary path
- `--agent`: agent personality (passed through from skill)
- `--session-id`: pre-generated UUID for the chat session
- `--name`: discoverable via `/resume`
- `--settings`: scoped SessionEnd hook (does not affect user's global settings)

### 6. Summary Generation

- Prompt template instructs chat claude to write summary to `<output-dir>/summary.md` using Write tool when user signals end
- Replaces current SendMessage + `[SHUTDOWN_REQUEST]` protocol
- If user Ctrl+D's without summary: SessionEnd hook still writes session.json with session_id → main can suggest `claude --resume <chat-session-id>`

### 7. Key Reference: $CLAUDE_ENV_FILE

- Hook writes `export` statements → Claude Code auto-sources before every Bash tool execution
- Available in: SessionStart, CwdChanged, FileChanged hooks only
- Per-session scope, destroyed on session end
- Always use `>>` (append), never `>`

## Open Questions

1. **Main session.json creation** — SessionStart hook에서 생성? 첫 `/chat` 실행 시 생성?
2. **Chat session.json fields** — session_id, topic, ended_at 외에 추가 필드?
3. **Ctrl+D fallback** — summary 없이 session.json만 남을 때 main에서의 처리 방식?
4. **--agent, --skill flag 전달** — `--append-system-prompt-file`에 포함? `--agent`는 CLI flag로 직접 전달?

## Files to Change

| File | Action |
|------|--------|
| `global/skills/chat/SKILL.md` | Rewrite execution steps |
| `global/skills/chat/references/prompt-template.md` | SendMessage → Write to file |
| `global/hooks/chat-session-end.sh` | **New**: SessionEnd hook for chat session metadata |
| SessionStart hook (location TBD) | **New**: Capture main session ID to `$CLAUDE_ENV_FILE` |

`global/install.sh` already copies `hooks/` to `~/.claude/hooks/` — no change needed.

## Rejected Alternatives

### Agent Teams (current approach)
- Lead accumulates idle_notification tokens while waiting
- Complex shutdown protocol ([SHUTDOWN_REQUEST] + SendMessage + shutdown_request + TeamDelete)
- Ghost processes on Ctrl+D
- Requires experimental API flag

### Agent Tool (subagent)
- Returns after 1 response — cannot loop for multi-turn conversation
- Confirmed in design doc testing (A4/interactive-subagent-design.md)

### Hook-based cleanup of Teams
- Considered using hooks to reduce lead's work, but Teams still require lead to be alive for TeamDelete
- Circular dependency: teammate can't self-terminate, needs lead's shutdown_request
