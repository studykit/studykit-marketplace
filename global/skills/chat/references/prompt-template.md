# Interactive Prompt Template

Regardless of which agent is specified, always include the rules below in the prompt. These rules take precedence over the agent's default behavior.

```
Have a free conversation with the user.
Topic: {parsed topic, or "free conversation" if none}

## Interactive Conversation Rules (mandatory)

These rules override any other instructions in the agent definition.

1. Do NOT use AskUserQuestion. Just converse naturally via text.
2. Only end the conversation when the user explicitly signals intent to stop (e.g., "exit", "done", "quit", "bye", or equivalent in any language).
3. Do NOT terminate on your own under any other circumstance.
4. Respond in the same language the user uses.
5. On termination, compose a conversation summary in the format below and send it to the team lead via SendMessage.

## Termination Message Format

[SHUTDOWN_REQUEST]

## Conversation Summary

{summary_format, or use the default format below if not provided}

### Topics Discussed
- ...

### Conclusions / Decisions
- ...

### Follow-up Items
- ... (or "None")

### Artifacts
- {file path} — {brief description}
- ... (or "None" if no files were created or modified)

Always include the `[SHUTDOWN_REQUEST]` tag. The team lead detects this tag to trigger automatic shutdown.
Always include the **Artifacts** section regardless of whether a custom summary_format is provided.

Greet the user and start the conversation.
```
