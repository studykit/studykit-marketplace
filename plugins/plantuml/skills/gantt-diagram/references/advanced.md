# Gantt Diagram — Advanced Reference

> Source: https://plantuml.com/gantt-diagram

## Task Completion Status

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

## Milestone Linked to Multiple Tasks

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

## Display on Same Row

```plantuml
@startgantt
Project starts 2020-09-01
[taskA] starts 2020-09-01 and requires 3 days
[taskB] starts 2020-09-10 and requires 3 days
[taskB] displays on same row as [taskA]
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

## Comprehensive Style Definition

```plantuml
@startgantt
<style>
ganttDiagram {
  task {
    FontName Helvetica
    FontColor red
    FontSize 18
    FontStyle bold
    BackGroundColor GreenYellow
    LineColor blue
  }
  milestone {
    FontColor blue
    FontSize 25
    FontStyle italic
    BackGroundColor yellow
    LineColor red
  }
  note {
    FontColor DarkGreen
    FontSize 10
    LineColor OrangeRed
  }
  arrow {
    FontName Helvetica
    FontColor red
    FontSize 18
    FontStyle bold
    BackGroundColor GreenYellow
    LineColor blue
    LineStyle 8.0;13.0
    LineThickness 3.0
  }
  separator {
    LineColor red
    BackGroundColor green
    FontSize 16
    FontStyle bold
    FontColor purple
    Margin 5
    Padding 20
  }
  timeline {
    BackgroundColor Bisque
  }
  closed {
    BackgroundColor pink
    FontColor red
  }
}
</style>
Project starts the 2020-12-01
[Task1] requires 10 days
sunday are closed
then [Task2] requires 4 days
-- Phase Two --
then [Task3] requires 5 days
[milestone] happens at [Task3]'s end
note bottom
  a]note for task3
end note
@endgantt
```

### Hidden Timeline Style

```plantuml
@startgantt
<style>
ganttDiagram {
  timeline {
    LineColor transparent
    FontColor transparent
  }
}
</style>
hide footbox
[Test prototype] requires 7 days
[Prototype completed] happens at [Test prototype]'s end
then [Setup assembly line] requires 12 days
@endgantt
```

## Full Complex Example

```plantuml
@startgantt
Project starts 2020-09-01
saturday are closed
sunday are closed

[taskA] starts 2020-09-01 and requires 3 days
[taskB] starts 2020-09-10 and requires 3 days
[taskB] displays on same row as [taskA]

[task01] on {Alice} starts 2020-09-05 and requires 4 days
then [task02] on {Bob} requires 8 days
note bottom
  note for task02
  more notes
end note
then [task03] on {Alice:25%} requires 7 days
note bottom
  note for task03
end note

-- separator --

[taskC] starts 2020-09-02 and requires 5 days
[taskD] starts 2020-09-09 and requires 5 days
[taskD] displays on same row as [taskC]

[milestone01] happens at [task03]'s end
@endgantt
```
