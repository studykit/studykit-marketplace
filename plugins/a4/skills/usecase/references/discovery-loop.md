# Discovery Loop

Uncover enough context to write concrete Use Cases by targeting four gaps:

- **What's happening now?** (current situation/trigger)
- **Who's involved?** (people → actors)
- **What should change?** (desired action → flow)
- **What does success look like?** (outcome)

Follow the conversation naturally, targeting whichever gap is most unclear.

## Actor discovery

When the conversation reveals a new person or system:

1. Confirm the actor with the user (name, type `person`/`system`, role — privilege level, short description).
2. If `a4/actors.md` does not exist, create it with frontmatter `type: actors` and a `## Roster` section containing an empty Actors table.
3. Add the confirmed actor to the table. Use a slug identifier (`meeting-organizer`, `team-member`) that UC frontmatter can reference in `actors: [...]`.
4. If the new actor justifies a wiki update (it usually does on first appearance), append a `## Change Logs` bullet with today's date and a markdown link to the causing UC.
