# Use Case Output Format

```markdown
---
type: usecase
pipeline: co-think
topic: "<topic>"
created: <YYYY-MM-DD HH:mm>
revised: <YYYY-MM-DD HH:mm>
revision: 0
status: draft | final
sources: []              # only when input is a file; omit for raw ideas
tags: []
reflected_files: []
last_step: ""
---
# Use Cases: <topic>
> Source: [<brainstorm-file-name>](./<brainstorm-file-name>)

## Original Idea
<The original input, as-is.>

## Context
<Brief summary of the problem space, who's involved, and why this matters. Derived from the interview.>

## Actors

| Actor | Type | Role | Description |
|-------|------|------|-------------|
| <name> | person / system | <privilege level, e.g., admin, editor, viewer, — for system> | <who this person/system is and what they're trying to do> |

## Use Case Diagram

```plantuml
@startuml
left to right direction

actor "Meeting Organizer" as organizer
actor "Team Member" as member

rectangle "System" {
  package "Meeting Summary" {
    usecase UC1 as "Share meeting summary
    --
    Generate and send
    summary to team"
    usecase UC3 as "Generate summary
    --
    Extract key decisions
    and action items"
  }

  package "Reporting" {
    usecase UC2 as "Review weekly report
    --
    View aggregated
    weekly activity"
  }
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
- **Source:** <input | research — <which systems> | implicit> *(include when research was performed; omit otherwise)*

### [UC-2]. <short title>
- **Actor:** <actor name>
- **Goal:** <goal>
- **Situation:** <situation>
- **Flow:**
  1. ...
- **Expected Outcome:** <outcome>
- **Source:** <source> *(include when research was performed)*

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

*Not enough use cases for relationship analysis yet.*

### Dependencies
- **[UC-1] → [UC-2]**: <reason>

### Reinforcements
- **[UC-1] → [UC-2], [UC-3]**: <reason>

### Use Case Groups
| Group | Use Cases | Description |
|-------|-----------|-------------|
| <name> | [UC-1], [UC-2], ... | <description> |

## Similar Systems Research
*(include when research was performed; omit otherwise)*

<Brief summary of similar products researched and common feature patterns discovered.>

- **Similar systems:** <name — key features described as user goals> (up to 5 systems)
- **High-value UC candidates:** <features/goals appearing in 3+ systems>
- **Niche UC candidates:** <features found in only 1 system>
- **User-requested features:** <from reviews/forums>

## Excluded Ideas
*(Include when research was performed and candidates were excluded. Omit if nothing was excluded.)*

| UC Candidate | Source | Exclusion Reason | Usage Frequency | User Reach | Core Goal Contribution |
|-------------|--------|-----------------|-----------------|------------|----------------------|
| <candidate title> | input / research | <reason: outside system scope / overlaps UC-N / low practical value> | Routine / Rare | Majority / Subset | Direct / Tangential |

## Open Questions
<Questions that came up but weren't resolved. Topics to revisit.>
- ...

## Open Items

| Section | Item | What's Missing | Priority |
|---------|------|---------------|----------|
| <section> | <item reference> | <specific gap description> | High / Medium / Low |

## Next Steps
- <suggested work items for next iteration, derived from Open Items>
```

**Source rules:**
- Place source references as a blockquote directly under the title heading.
- Use relative path links for references within the same repo. Use full GitHub URLs only in issue bodies.
- If the idea came from a spark-brainstorm output file, add relative path links and record in frontmatter `sources` with `sha` (via `git hash-object`):
  ```yaml
  sources:
    - file: <brainstorm-file-name>
      sha: <git hash-object output>
  ```
- If the idea came from multiple sources, list them comma-separated on one line. Record each file in `sources`.
- If the user provided a raw idea with no prior file, omit the source line and `sources` field entirely.

**Heading ID convention:**
- Use cases use `UC-N` IDs (UC-1, UC-2...) as canonical identifiers throughout the document.
- These IDs are assigned during the interview and remain unchanged at finalization.

**Use Case Diagram rules:**
- Use PlantUML use case diagram syntax.
- Show all actors and use cases with relationships (include/extend).
- Use PlantUML's multiline description syntax (`usecase UC1 as "Title\n--\nDescription"`) to show each use case's purpose at a glance.
- Group related use cases using `package "Group Name" { ... }` blocks inside the system `rectangle`. Derive groups from Use Case Groups in the relationship analysis. Before relationship analysis is done (< 5 UCs), use a single flat rectangle without packages.
- Add notes for additional context where helpful.
- Update the diagram each time a new use case is confirmed.

**Abstraction rule:**
- Flow steps must describe user-level actions only. No implementation terms (API, database, webhook, cache, queue, etc.).

**Issue reference links:** Read `${SKILL_DIR}/../../references/issue-links.md` for GitHub issue link formatting rules.

**Required sections (both skills)**: Original Idea, Context, Actors, Use Case Diagram, Use Cases, Use Case Relationships.
**Additional required (think-usecase)**: Open Items, Next Steps.
**Additional required (auto-usecase)**: Similar Systems Research, Open Questions, Open Items, Next Steps.
**Conditionally required:**
- **Similar Systems Research** — always in auto-usecase; in think-usecase only when research was performed
- **Source field** (per UC) — always in auto-usecase; in think-usecase only when research was performed
- **Open Questions** — if unresolved topics remain (think-usecase); always required (auto-usecase)
- **Excluded Ideas** — when research was performed and candidates were excluded; omit if nothing was excluded
