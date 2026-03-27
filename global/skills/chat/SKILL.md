---
name: chat
description: This skill should be used when the user asks to "chat", "let's talk", "have a conversation", "discuss", "brainstorm together", wants to explore a topic interactively, or needs collaborative problem-solving in a split pane. Conversation summary is returned to the main session on exit.
argument-hint: [agent] [topic]
version: 0.1.0
---

Start an interactive sub-agent conversation session.

## Argument Parsing

Parse `$ARGUMENTS` with these rules:

1. Extract the first word.
2. Check if a matching agent exists with that name.
3. **If a match is found**: Use that agent as `subagent_type`, treat the rest as the conversation topic.
4. **If no match is found**: Analyze the topic context and, if a suitable agent exists, recommend it to the user via AskUserQuestion. The user can accept the recommendation or choose to proceed without a specific agent. If no suitable agent is identified, skip the recommendation and omit `subagent_type`. Treat the entire `$ARGUMENTS` as the conversation topic.

Examples:
- `/chat debugger login bug` → agent: `debugger` (explicit), topic: `login bug`
- `/chat review the auth module` → recommend `code-reviewer` via AskUserQuestion → user accepts or declines
- `/chat what should we do today` → no suitable agent → agent: (none), topic: `what should we do today`
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
