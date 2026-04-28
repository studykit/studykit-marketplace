# Platform Capabilities Audit

Run after all primary UCs are confirmed. Mark "Discovery: Use cases" as `completed` and "Platform capabilities audit" as `in_progress`.

Audit for implicit platform capabilities — shared behaviors that multiple UCs assume but no UC defines (message input, conversation display, navigation, session restore, etc.).

## Procedure

1. **Scan all UC flows** for user actions that appear across 3+ UCs but aren't themselves covered by any UC.
2. **Present findings** to the user as a table (Assumed Capability | Referenced By | Example flow text). Ask whether to create UCs.
3. **Create UCs** for confirmed gaps the same way as any other UC (allocate id, write `usecase/<id>-<slug>.md`). These UCs use `actors: [platform]` or a suitable system actor.
4. Skip silently if no gaps are found.
