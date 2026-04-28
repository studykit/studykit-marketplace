# Phase 3: State Transition Analysis

Populate `<state-transitions>` in `a4/domain.md` only when at least one concept has state changes across UCs.

## Procedure

1. **Identify stateful concepts** — those whose UCs change their state implicitly or explicitly (created → published → archived; pending → confirmed → cancelled).

2. **For each stateful concept**, with the user:
   - Enumerate states.
   - Map transitions: source → target, with trigger and condition.
   - Distinguish reversible from terminal transitions.

3. **Write a PlantUML state diagram** per stateful concept under a `### <Concept>` subsection.

4. **Add text explanation** under each diagram naming default state, terminal states, and any constraints not visible in the diagram.

## When to skip

Stateless concepts (pure value/data) have no state diagram. Skip the section entirely if no concept is stateful.
