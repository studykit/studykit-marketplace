# Architecture Output Template

## File Path

`A4/co-think/<YYYY-MM-DD-HHmm>-<topic-slug>.architecture.md`

## Frontmatter

```yaml
---
type: architecture
pipeline: co-think
topic: "<topic>"
date: <YYYY-MM-DD>
status: final
source:
  - "[[<story-file-name>]]"
  - "[[<requirement-file-name>]]"
  - "[[<domain-model-file-name>]]"
tags: []
---
```

**`source` field rules:**
- Use wikilinks (filename only, no path) to all input files.
- List story, requirement, and domain model files.

## Template

```markdown
# Architecture: <topic>

## Overview
<High-level architecture summary — what components exist, how they relate, key design decisions made during the session.>

## Technology Choices
<Decisions made during the session with brief rationale. Only present if choices were made.>

| Choice | Decision | Rationale |
|--------|----------|-----------|
| Database | PostgreSQL | Relational data, team experience |

## Component Diagram

```plantuml
@startuml
component [ComponentA] as A
component [ComponentB] as B
A --> B : sends user info
@enduml
```

<Text explanation of components and their responsibilities.>

## Components

### <Component Name>

**Responsibility:** <what this component does>
**Data store:** Yes / No

#### DB Schema

```plantuml
@startuml
entity "EntityName" as e1 {
  *id : number <<PK>>
  --
  *name : text
  description : text
}
@enduml
```

<Text explanation of entities and relationships.>

#### Information Flow

##### Story: <story reference>

```plantuml
@startuml
participant "ComponentA" as A
participant "ComponentB" as B
A -> B : user information
B --> A : confirmation
@enduml
```

<Text explanation of the flow for this story.>

## Consistency Check
<Results of the consistency check against domain model and stories. Any gaps identified and how they were resolved.>

## Interview Transcript
<details>
<summary>Full Q&A</summary>

### Round 1
**Q:** <question>
**A:** <answer>

...
</details>
```

## Required Sections

- Overview
- Component Diagram
- Components (with per-component details)
- Consistency Check
- Interview Transcript

## Conditional Sections

- Technology Choices — only if choices were made during the session

## Diagram References

- **Component diagram**: [PlantUML Component Diagram](https://plantuml.com/component-diagram)
- **Sequence diagram**: [PlantUML Sequence Diagram](https://plantuml.com/sequence-diagram)
- **IE diagram (DB schema)**: [PlantUML IE Diagram](https://plantuml.com/ie-diagram)
