# Gantt Diagram — Advanced Reference

> Source: https://plantuml.com/gantt-diagram

## Display on Same Row

```plantuml
@startgantt
Project starts 2020-09-01
[taskA] starts 2020-09-01 and requires 3 days
[taskB] starts 2020-09-10 and requires 3 days
[taskB] displays on same row as [taskA]
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
