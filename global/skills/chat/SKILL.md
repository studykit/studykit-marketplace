---
name: chat
description: This skill should be used when the user asks to "chat", "let's talk", "have a conversation", "discuss", "brainstorm together", wants to explore a topic interactively, or needs collaborative problem-solving in a split pane. Conversation summary is returned to the main session on exit.
argument-hint: [--agent [name]] [--skill <names>] [topic]
version: 0.1.0
---

Start an interactive sub-agent conversation session.

## Argument Parsing

Parse `$ARGUMENTS` by extracting flags and treating the remainder as the conversation topic.

### Flags

| Flag | Behavior |
|---|---|
| `--agent <name>` | Use the named agent as `subagent_type`. |
| `--agent` (no value) | Analyze the topic context and, if a suitable agent exists, recommend it to the user via AskUserQuestion. The user can accept or decline. If no suitable agent is identified, omit `subagent_type`. |
| *(no `--agent` flag)* | No agent — omit `subagent_type`. |
| `--skill <names>` | Preload the listed skills (comma-separated) into the chat agent's prompt so they are available during the conversation. |

Everything that is not a flag or flag value is the **topic**.

### Examples

- `/chat --agent debugger login bug` → agent: `debugger`, topic: `login bug`
- `/chat --agent review the auth module` → recommend a suitable agent (e.g., `code-reviewer`) via AskUserQuestion → user accepts or declines, topic: `review the auth module`
- `/chat what should we do today` → agent: (none), topic: `what should we do today`
- `/chat --skill commit,simplify refactor the utils` → agent: (none), skills: `commit`, `simplify` preloaded, topic: `refactor the utils`
- `/chat --agent executor --skill commit build the feature` → agent: `executor`, skills: `commit` preloaded, topic: `build the feature`
- `/chat` → agent: (none), topic: none

## Summary Format

Determine the summary format based on why the conversation was started.

- For a specific purpose (e.g., debugging, code review, planning), define a `summary_format` tailored to that purpose and pass it into the prompt template.
- For free conversation with no specific purpose, omit `summary_format` and the default format from the prompt template applies.

Always include an **Artifacts** section in the summary listing any files created or modified during the conversation, with paths and a brief description. If no files were changed, write "None".

## Execution Steps

1. Create a team with TeamCreate.
   - team_name: "interactive-chat"

2. Determine the `summary_format` based on the conversation intent. Leave it empty if there is no specific purpose.

3. Spawn a teammate with the Agent tool.
   - subagent_type: (parsed agent name, or omit if no agent was matched)
   - name: "chat-agent"
   - team_name: "interactive-chat"
   - prompt: Use the prompt template from **`references/prompt-template.md`**, injecting `summary_format` if provided.

4. Wait while the teammate converses directly with the user in a split pane.

5. On receiving a message containing the `[SHUTDOWN_REQUEST]` tag from the teammate:
   a. Record the conversation summary.
   b. Send a shutdown_request to the teammate.
   c. Once the teammate has shut down, clean up the team with TeamDelete.
   d. Display the conversation summary to the user.

## Important Notes

- Do NOT run TeamDelete before the teammate has shut down.
- If the user force-quits the teammate with Ctrl+D, no summary will be delivered. Still clean up the team in this case.
- Ignore idle_notification from the teammate — this is normal behavior. Keep waiting.
- `[SHUTDOWN_REQUEST]` is a custom tag, not an official protocol. It works around the limitation that teammates cannot self-terminate in Agent Teams. Replace with an official API if one becomes available.

## Additional Resources

### Reference Files

- **`references/prompt-template.md`** — Full interactive prompt template with conversation rules, termination format, and shutdown protocol.
