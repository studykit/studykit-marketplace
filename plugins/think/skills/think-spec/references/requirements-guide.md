# Requirements Guide

Detailed procedures for Phase 1 sub-steps: question techniques, UI screen grouping, mock generation, authorization rules, and non-functional requirements.

## Question Techniques (Step 1.1)

### What to clarify per use case

**For UI use cases:**
- Where does this happen? (which screen/view)
- What does the user see? (elements, information, initial state)
- What does the user do? (interactions, step-by-step flow)
- What changes? (state transitions, feedback, result)
- What can go wrong? (error states, validation, edge cases)

**For Non-UI use cases:**
- What triggers this? (command, API call, event, schedule)
- What goes in? (input format, parameters, validation)
- What comes out? (output format, success response)
- What are the rules? (business logic, conditions, ordering)
- What can go wrong? (error cases, invalid input, failure modes)

### Techniques

- Ask about **concrete scenarios**: "If a user does X in this situation, what should happen?"
- Ask about **edge cases**: "What if the input is empty? What if there are 10,000 items?"
- Ask about **boundaries**: "Is there a limit? What's the maximum/minimum?"
- When the user is unsure, offer 2-3 concrete options.

## UI Screen Grouping (Step 1.2)

After all use cases have been specified as FRs, group the UI FRs by screen or view:

1. **Propose screen groups** — analyze UI FRs and group them by the screen/view where they occur. Present the grouping to the user:

   > Here's how I'd group the UI requirements by screen:
   >
   > | Screen | FRs |
   > |--------|-----|
   > | Dashboard | FR-1, FR-3, FR-7 |
   > | Settings | FR-4, FR-9 |
   > | Detail View | FR-2, FR-5 |
   >
   > Does this grouping make sense? Any adjustments?

2. **Confirm with the user** — the user may merge, split, or rename screen groups.
3. **Define screen navigation** — after screen groups are confirmed, map how users move between screens. Present as a PlantUML activity diagram:

   > Here's the navigation flow between screens:
   >
   > ```plantuml
   > @startuml
   > (*) --> Dashboard
   > Dashboard --> "Detail View" : clicks item
   > Dashboard --> Settings : clicks settings icon
   > "Detail View" --> Dashboard : clicks back
   > Settings --> Dashboard : clicks done
   > @enduml
   > ```
   >
   > Does this capture the navigation? Any missing transitions?

4. **Confirm navigation with the user** — the user may add, remove, or relabel transitions.
5. **Update the output file** — record the screen grouping and navigation in the Functional Requirements section.

## Mock Generation (Step 1.3)

For each confirmed screen group, create a mock UI:

1. **Use the mock-html-generator agent** to create an HTML mock. Save to `A4/mock/<topic-slug>/`.
2. **Present the mock** and gather feedback — the mock should reflect all FRs in the group.
3. **Iterate if needed** — refine the mock based on feedback.
4. **Refine FRs** — use the mock feedback to fill gaps, clarify interactions, and update the FRs.
5. **Record the mock file path** in each FR that belongs to the group.

Move to the next screen group only when the user confirms.

## Authorization Rules (Step 1.4)

After all FRs are specified, analyze the Actors table from the source use case file:

1. **Check for role differentiation** — do actors have different privilege levels? (e.g., "User" vs "Admin", or "Viewer" vs "Editor")
2. **If no differentiation** — skip this step, no section created.
3. **If roles differ** — build an authorization matrix mapping actors to FRs:

   > Based on the actors, here's how I'd map access:
   >
   > | FR | Admin | User | System |
   > |----|-------|------|--------|
   > | FR-1. Create item | write | write | — |
   > | FR-2. Delete all items | write | — | — |
   > | FR-3. View dashboard | read | read | — |
   > | FR-4. Cleanup expired sessions | — | — | execute |
   >
   > Does this capture the access rules? Any adjustments?

4. **Confirm with the user** — walk through each FR and verify the access level per actor.
5. **Update the output file** — record the Authorization Rules section.

## Non-Functional Requirements Nudge (Step 1.5)

After all FRs are specified, ask the user once:

> "Are there non-functional requirements that should constrain the implementation? For example: performance targets, security requirements, scalability needs, accessibility standards, or compliance rules. If not, we can skip this."

- If yes → capture each NFR with: description, affected FRs, measurable criteria
- If no → move on, no section created

## Platform Capability Audit (Step 1.6)

After all UC-derived FRs and any platform FRs from Step 1.0 are confirmed, perform a final audit for implicit platform capabilities — shared behaviors that multiple FRs assume but no FR defines.

1. **Scan all FR flows** — identify user actions or system behaviors that appear across 3+ FRs but aren't themselves covered by any FR.

   Common patterns to check:
   - **Input mechanisms** — message input, form submission, command entry, search box
   - **Display mechanisms** — conversation display, list views, real-time response streaming, status indicators
   - **Navigation infrastructure** — view routing, tab management, sidebar, breadcrumbs
   - **State lifecycle** — session restore on launch, data persistence across restarts, undo/redo

2. **Present findings** to the user:

   > These capabilities are assumed by multiple FRs but not yet defined:
   >
   > | Assumed Capability | Referenced By | Example FR Text |
   > |-------------------|---------------|-----------------|
   > | Message input and sending | FR-1, FR-7, FR-8, FR-15 | "user types a question" |
   > | Conversation display with streaming | FR-1, FR-2, FR-3 | "response displays inline" |
   >
   > Should I create FRs for these?

3. **Create FRs** for confirmed gaps. These FRs reference the Overview rather than a specific UC:
   ```
   > Use Case: (platform capability — implicit across [list dependent FRs])
   ```

4. If Step 1.0 already created platform FRs from Excluded Ideas, check whether they cover the gaps found here. Only create new FRs for gaps not already addressed.

5. If no gaps are found, skip silently.
