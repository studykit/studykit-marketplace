# Architecture Guide

Detailed procedures for Phase 3: designing system components from use cases and domain model.

## Topic 3.1: Component Identification

- Propose an initial set of components from the use cases and domain model
- Present the component list with responsibility descriptions
- Through interview, confirm: component name, responsibility, whether it has its own data store
- Present as PlantUML component diagram

## Topic 3.2: Per-Component Deep Dive

For each confirmed component:

- **DB schema** (if the component has its own data store):
  - Identify entities, attributes, and relationships
  - Present as PlantUML IE diagram
  - Not all components need a DB schema — ask before diving in

- **Information flow** (per use case):
  - For each use case involving this component, map the information flow between components
  - Present as PlantUML sequence diagram — one per use case
  - First iteration: "A sends user information to B" level is fine
  - Subsequent iterations: progressively refine to **interface contract** level — communication method (REST, event, function call), operation name, request/response schema
  - The goal by finalization: a coding agent can implement the interface without guessing

- **Interface contracts** (per component boundary):
  - Define how components communicate: API style, operations, request/response schemas
  - This is not required in the first iteration — it emerges as the arch matures
  - Present as a contract table per component pair:

    > | Operation | Direction | Request | Response | Notes |
    > |-----------|-----------|---------|----------|-------|
    > | createSession | Client → SessionService | { userId, title } | { sessionId, status } | |
    > | onSessionExpired | SessionService → NotificationService | { sessionId, reason } | — | event |

## Abstraction Level

- Components define **interfaces**, not internal implementation
- DB schemas define entities and relationships, not implementation details (no index strategies)
- Sequence diagrams show component interactions, not internal algorithms
- **Always off-limits**: internal implementation of each component (algorithms, library choices within a component, internal data structures)
