# Domain Model Guide

Detailed procedures for extracting domain concepts from use cases. The Domain Model produces the shared vocabulary that architecture and implementation will use.

## Topic 1: Concept Extraction

- Read all UCs horizontally — identify concepts (entities) that appear across multiple UCs
- Present the initial concept list to the user
- For each concept, through interview confirm: name, definition, 1-2 key attributes
- Track which UCs reference each concept

## Topic 2: Relationship Mapping

- Identify relationships between concepts
- Present as PlantUML class diagram (concept name + key attributes only, NO implementation types)
- Accompanied by text explanation of each relationship
- Show multiplicity (1..*, 0..1, etc.) where relevant

## Topic 3: State Transition Analysis

- Identify which concepts have state changes across UCs
- For each stateful concept, map states, transitions, conditions, triggers
- Present as PlantUML state diagram
- Accompanied by text explanation

## Abstraction Level

- "What exists and how it connects" = confirmed
- "How to build it" = not decided
- No implementation types (VARCHAR, INT, string) in class diagrams
- No API endpoints or serialization formats
- No component assignments — that is architecture's concern
