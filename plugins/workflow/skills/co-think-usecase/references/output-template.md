# Use Case Output Format

```markdown
---
type: usecase
pipeline: co-think
topic: "<topic>"
created: <YYYY-MM-DD HH:mm>
revised: <YYYY-MM-DD HH:mm>
revision: 0
status: final
tags: []
---
# Use Cases: <topic>
> Source: [<brainstorm-file-name>](./<brainstorm-file-name>)

## Original Idea
<The original input, as-is.>

## Context
<Brief summary of the problem space, who's involved, and why this matters. Derived from the interview.>

## Actors

| Actor | Description |
|-------|-------------|
| <name> | <who this person/system is and what they're trying to do> |

## Use Case Diagram

```plantuml
@startuml
left to right direction

actor "Meeting Organizer" as organizer
actor "Team Member" as member

rectangle "System" {
  usecase "Share meeting summary" as UC1 : Generate and send\nsummary to team
  usecase "Review weekly report" as UC2 : View aggregated\nweekly activity
  usecase "Generate summary" as UC3 : Extract key decisions\nand action items
}

organizer --> UC1
organizer --> UC2
member --> UC2
UC1 ..> UC3 : <<include>>

note right of UC1
  Triggered after meetings
end note
@enduml
```

## Use Cases

### [UC-1]. <short title>
- **Actor:** <actor name from Actors table>
- **Goal:** <what the actor is trying to achieve>
- **Situation:** <context/trigger — when and why this happens>
- **Flow:**
  1. <user-level action step>
  2. <user-level action step>
  3. ...
- **Expected Outcome:** <what's different after the flow completes — observable/measurable>

### [UC-2]. <short title>
- **Actor:** <actor name>
- **Goal:** <goal>
- **Situation:** <situation>
- **Flow:**
  1. ...
- **Expected Outcome:** <outcome>

### [UC-3]. <short title> *(split from original)*
#### [UC-3a]. <short title>
- **Actor:** <actor name>
- **Goal:** <goal>
- **Situation:** <situation>
- **Flow:**
  1. ...
- **Expected Outcome:** <outcome>

#### [UC-3b]. <short title>
- **Actor:** <actor name>
- **Goal:** <goal>
- **Situation:** <situation>
- **Flow:**
  1. ...
- **Expected Outcome:** <outcome>

...

## Use Case Relationships

### Dependencies
- **[UC-1] → [UC-2]**: <reason>

### Reinforcements
- **[UC-1] → [UC-2], [UC-3]**: <reason>

### Use Case Groups
| Group | Use Cases | Description |
|-------|-----------|-------------|
| <name> | [UC-1], [UC-2], ... | <description> |

## Open Questions
<Questions that came up but weren't resolved. Topics to revisit.>
- ...

## Interview Transcript
<details>
<summary>Full Q&A</summary>

### Round 1
**Q:** <question>
**A:** <answer>

...
</details>
```

**Source rules:**
- Place source references as a blockquote directly under the title heading.
- Use relative path links for references within the same repo. Use full GitHub URLs only in issue bodies.
- If the idea came from a spark-brainstorm output file, add relative path links.
- If the idea came from multiple sources, list them comma-separated on one line.
- If the user provided a raw idea with no prior file, omit the source line entirely.

**Heading ID convention:**
- Use cases use `UC-N` IDs (UC-1, UC-2...) as canonical identifiers throughout the document.
- These IDs are assigned during the interview and remain unchanged at finalization.

**Use Case Diagram rules:**
- Use PlantUML use case diagram syntax.
- Show all actors and use cases with relationships (include/extend).
- Use PlantUML's inline description syntax (`: description`) to show each use case's purpose at a glance.
- Add notes for additional context where helpful.
- Update the diagram each time a new use case is confirmed.

**Abstraction rule:**
- Flow steps must describe user-level actions only. No implementation terms (API, database, webhook, cache, queue, etc.).

**Issue reference links:** See [issue-links.md](../../references/issue-links.md).

**Required sections**: Original Idea, Context, Actors, Use Case Diagram, Use Cases, Use Case Relationships, Interview Transcript.
**Conditionally required:**
- **Open Questions** — if unresolved topics remain
