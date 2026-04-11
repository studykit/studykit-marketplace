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

### Percentage and Styling

```plantuml
@startgantt
<style>
ganttDiagram {
  task {
    BackGroundColor GreenYellow
    LineColor Green
    unstarted {
      BackGroundColor Fuchsia
      LineColor FireBrick
    }
  }
  undone {
    BackGroundColor red
  }
}
</style>
[foo] lasts 21 days
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

### Milestone Linked to Multiple Tasks

```plantuml
@startgantt
[Task1] requires 4 days
then [Task1.1] requires 4 days
[Task1.2] starts at [Task1]'s end and requires 7 days
[Task2] requires 5 days
then [Task2.1] requires 4 days
[MaxTaskEnd] happens at [Task1.1]'s end
[MaxTaskEnd] happens at [Task1.2]'s end
[MaxTaskEnd] happens at [Task2.1]'s end
then [Task3] requires 1 day
@endgantt
```

## Task Coloring

```plantuml
@startgantt
[Prototype design] requires 13 days
[Prototype design] is colored in Fuchsia/FireBrick
[Test prototype] requires 4 days
[Test prototype] is colored in GreenYellow/Green
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

## Working Days and Delays

```plantuml
@startgantt
saturday are closed
sunday are closed
2022-07-04 to 2022-07-15 is closed
Project starts 2022-06-27
[task1] starts at 2022-06-27 and requires 1 week
[task2] starts 2 working days after [task1]'s end and requires 3 days
@endgantt
```

## Coloring Specific Days

```plantuml
@startgantt
Project starts the 2020/09/01
2020/09/07 is colored in salmon
2020/09/13 to 2020/09/16 are colored in lightblue
[TASK1] requires 22 days
@endgantt
```

## Resource Management

### Assigning Tasks to Resources

```plantuml
@startgantt
[Task1] on {Alice} requires 10 days
[Task2] on {Bob:50%} requires 2 days
then [Task3] on {Alice:25%} requires 1 days
@endgantt
```

### Multiple Resources Per Task

```plantuml
@startgantt
[Task1] on {Alice} {Bob} requires 20 days
@endgantt
```

### Resource Time Off

```plantuml
@startgantt
project starts on 2020-06-19
[Task1] on {Alice} requires 10 days
{Alice} is off on 2020-06-24 to 2020-06-26
@endgantt
```

### Hide Resources

`hide resources names`, `hide resources footbox`

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

## Scale Configuration (Print Scale)

Options: `daily` (default), `weekly`, `monthly`, `quarterly`, `yearly`

```plantuml
@startgantt
printscale weekly
Project starts the 20th of september 2020
[Prototype design] as [TASK1] requires 130 days
[Testing] requires 20 days
[TASK1] -> [Testing]
@endgantt
```

### Zoom

Combine `zoom` with any scale to magnify.

```plantuml
@startgantt
printscale weekly
zoom 4
Project starts the 1st of january 2021
[Prototype design end] as [TASK1] requires 19 days
[Testing] requires 14 days
[TASK1] -> [Testing]
@endgantt
```

## Print Between (Date Range Filtering)

```plantuml
@startgantt
Print between 2021-01-12 and 2021-01-22
Project starts the 1st of january 2021
[Prototype design end] as [TASK1] requires 8 days
[Testing] requires 3 days
[TASK1] -> [Testing]
@endgantt
```

## Week Numbering in Headers

Options: `with week numbering from N`, `with calendar date`

```plantuml
@startgantt
printscale weekly with week numbering from 1
Project starts the 6th of July 2020
[Task1] on {Alice} requires 2 weeks
[Task2] on {Bob:50%} requires 2 weeks
@endgantt
```

### Custom Week Start Day

```plantuml
@startgantt
printscale weekly
weeks starts on Sunday and must have at least 4 days
friday are closed
saturday are closed
Project starts the 1st of january 2025
[Prototype design end] as [TASK1] requires 19 days
[Testing] requires 14 days
[TASK1] -> [Testing]
@endgantt
```

## Language

Set day/month names: `language en`, `language ko`, `language ja`, etc.

## Comments

Single-line: `' comment`
Multi-line: `/' comment '/`

## Separators

### Horizontal (Phase Dividers)

```plantuml
@startgantt
[Task1] requires 10 days
then [Task2] requires 4 days
-- Phase Two --
then [Task3] requires 5 days
then [Task4] requires 6 days
@endgantt
```

### Vertical

```plantuml
@startgantt
[task1] requires 1 week
[task2] starts 20 days after [task1]'s end and requires 3 days
Separator just at [task1]'s end
Separator just 2 days after [task1]'s end
@endgantt
```

## Notes

```plantuml
@startgantt
[task01] requires 15 days
note bottom
  memo1 ...
  memo2 ...
end note
[task01] -> [task02]
@endgantt
```

## Today Indicator

```plantuml
@startgantt
Project starts 2020-07-01
saturday are closed
sunday are closed
today is 2020-07-10
today is colored in #AAF
[Prototype design] requires 15 days
@endgantt
```

## Additional Resources

For same-row display, comprehensive `<style>` theming, and a full complex example:
- **`gantt-diagram-advanced.md`** — Less-common Gantt layout and styling patterns
