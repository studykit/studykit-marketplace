# Abstraction Level Guards

Per-phase rules on what level of detail is appropriate in the specification.

## Requirements
- Capture **what the software should do**, not how to implement it
- No technology choices, no data schemas, no API endpoint designs

## Domain Model
- "What exists and how it connects" = confirmed, "how to build it" = not decided
- No implementation types (VARCHAR, INT) in class diagrams
- No API endpoints or serialization formats

## Architecture
- **First iteration**: "What components exist and what information they exchange" — sequence diagrams at information level, no interface contracts yet
- **Subsequent iterations**: progressively add interface contracts — communication method, operations, request/response schemas. This is expected and necessary for coding agents.
- DB schemas define entities and relationships, not implementation details (no index strategies)
- **Always off-limits**: internal implementation of each component (algorithms, library choices within a component, internal data structures)
