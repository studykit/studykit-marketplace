---
name: gantt-diagram
disable-model-invocation: true
description: This skill provides PlantUML Gantt diagram syntax reference. Use when writing, creating, or debugging PlantUML Gantt charts. Applies when users mention "Gantt chart", "Gantt diagram", "project timeline", "task schedule", "milestone", "project plan", or need to diagram project schedules, task dependencies, or timelines in PlantUML.
---

> Source: https://plantuml.com/gantt-diagram

# PlantUML Gantt Diagram Reference

## Declaring Tasks

Tasks are defined using square brackets. Use `requires`, `lasts`, or start/end dates.

```plantuml
@startgantt
[Prototype design] requires 15 days
[Test prototype] requires 10 days
@endgantt
```

## Task Start and End Dates

```plantuml
@startgantt
Project starts 2020-07-01
[Prototype design] starts 2020-07-01 and ends 2020-07-15
[Test prototype] starts 2020-07-16 and requires 10 days
@endgantt
```

### Relative Start Date

```plantuml
@startgantt
[Prototype design] starts D+0
[Test prototype] starts D+15
@endgantt
```

## Short Names (Aliases)

```plantuml
@startgantt
[Prototype design] as [D] requires 15 days
[Test prototype] as [T] requires 10 days
[T] starts at [D]'s end
@endgantt
```

## Task Dependencies

### Using `starts at ... end`

```plantuml
@startgantt
[Prototype design] requires 10 days
[Code prototype] requires 10 days
[Write tests] requires 5 days
[Code prototype] starts at [Prototype design]'s end
[Write tests] starts at [Code prototype]'s start
@endgantt
```

### Using `then` Keyword

```plantuml
@startgantt
[Prototype design] requires 14 days
then [Test prototype] requires 4 days
then [Deploy prototype] requires 6 days
@endgantt
```

### Using Arrow Notation

```plantuml
@startgantt
[Prototype design] requires 14 days
[Build prototype] requires 4 days
[Prototype design] -> [Build prototype]
@endgantt
```

### Delayed Constraints

```plantuml
@startgantt
[Test prototype] requires 10 days
[Setup assembly line] requires 12 days
[Setup assembly line] starts 3 days after [Test prototype]'s end
@endgantt
```

## Task Completion Status

```plantuml
@startgantt
[foo] requires 21 days
[foo] is 40% completed
[bar] requires 30 days and is 10% complete
@endgantt
```

## Milestones

```plantuml
@startgantt
[Test prototype] requires 10 days
[Prototype completed] happens at [Test prototype]'s end
[Setup assembly line] requires 12 days
[Setup assembly line] starts at [Test prototype]'s end
@endgantt
```

### Milestone at Fixed Date

```plantuml
@startgantt
Project starts 2020-07-01
[Test prototype] requires 10 days
[Prototype completed] happens 2020-07-10
@endgantt
```

## Task Coloring

```plantuml
@startgantt
[Prototype design] requires 13 days
and is colored in Fuchsia/FireBrick
[Test prototype] requires 4 days
and is colored in GreenYellow/Green
[Test prototype] starts at [Prototype design]'s end
@endgantt
```

## Closed Days (Non-Working Days)

```plantuml
@startgantt
project starts the 2018/04/09
saturday are closed
sunday are closed
2018/05/01 is closed
2018/04/17 to 2018/04/19 is closed
[Prototype design] requires 14 days
[Test prototype] requires 4 days
[Prototype design] -> [Test prototype]
@endgantt
```

Re-open with: `2020-07-13 is open`

## Coloring Specific Days

```plantuml
@startgantt
Project starts the 2020/09/01
2020/09/07 is colored in salmon
2020/09/13 to 2020/09/16 are colored in lightblue
[TASK1] requires 22 days
@endgantt
```

## Title, Header, Footer, Hide Footbox

```plantuml
@startgantt
header My Header
footer My Footer
title My Gantt Diagram
hide footbox

[Task1] requires 10 days
then [Task2] requires 4 days
@endgantt
```

## Language

Set day/month names: `language en`, `language ko`, `language ja`, etc.

## Comments

Single-line: `' comment`
Multi-line: `/' comment '/`

## Additional Resources

For completion styling, multi-task milestones, working days, print scale (daily/weekly/monthly/quarterly/yearly), zoom, date range filtering, week numbering, resource management, separators, same-row display, notes, today indicator, and `<style>` blocks:
- **`references/advanced.md`** — Advanced Gantt diagram features and styling
