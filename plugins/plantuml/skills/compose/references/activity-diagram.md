> Source: https://plantuml.com/activity-diagram-beta

# PlantUML Activity Diagram Reference

## Simple Action

Activities are defined with `:` and terminated with `;`. Supports Creole/HTML formatting.

```plantuml
@startuml
:Hello world;
:This is defined on
several **lines**;
@enduml
```

## Start / Stop / End

Use `start` to begin a diagram. Use `stop` or `end` to terminate.

```plantuml
@startuml
start
:Hello world;
stop
@enduml
```

## Conditional (if / then / else / endif)

```plantuml
@startuml
start
if (Graphviz installed?) then (yes)
  :process all\ndiagrams;
else (no)
  :process only
  __sequence__ and __activity__ diagrams;
endif
stop
@enduml
```

### Multiple Conditions (elseif)

```plantuml
@startuml
start
if (condition A) then (yes)
  :Text 1;
elseif (condition B) then (yes)
  :Text 2;
  stop
elseif (condition C) then (yes)
  :Text 3;
else (nothing)
  :Text else;
endif
stop
@enduml
```

Vertical mode: `!pragma useVerticalIf on`

### Switch / Case

```plantuml
@startuml
start
switch (test?)
case ( condition A )
  :Text 1;
case ( condition B )
  :Text 2;
case ( condition C )
  :Text 3;
endswitch
stop
@enduml
```

### Stop, Kill, and Detach

`stop` ends with a terminator. `kill` terminates with a cross. `detach` removes the arrow entirely.

## Repeat Loop

```plantuml
@startuml
start
repeat :foo as starting label;
  :read data;
  :generate diagrams;
backward:This is backward;
repeat while (more data?) is (yes) ->no;
stop
@enduml
```

`break` exits a repeat loop.

## While Loop

```plantuml
@startuml
while (check filesize ?) is (not empty)
  :read file;
  backward:log;
endwhile (empty)
:close file;
@enduml
```

## Parallel Processing (fork)

```plantuml
@startuml
start
fork
  :action 1;
fork again
  :action 2;
end fork
stop
@enduml
```

- `end merge` — merges without synchronization bar
- `end fork {or}` / `end fork {and}` — join conditions

## Split Processing

```plantuml
@startuml
start
split
   :A;
split again
   :B;
split again
   :C;
end split
:D;
end
@enduml
```

## Notes

```plantuml
@startuml
start
:foo1;
floating note left: This is a note
:foo2;
note right
  This note is on several
  //lines// and can
  contain <b>HTML</b>
end note
stop
@enduml
```

## Colors on Activities

Add `<<#color>>` **after** the closing `;` to color an activity.

```plantuml
@startuml
start
:starting progress;
:reading configuration files\nThese files should be edited at this point!; <<#HotPink>>
:ending of the process; <<#AAAAAA>>
@enduml
```

> **Deprecated:** The older `#color:text;` prefix syntax (e.g., `#HotPink:reading files;`) still works but emits a deprecation warning. Always use the `<<#color>>` suffix form instead.

## Arrows

Use `->` with text to label arrows. Arrow styles: `dashed`, `dotted`, `bold`, `hidden`. Colors with `#colorname`.

```plantuml
@startuml
:foo1;
-> You can put text on arrows;
if (test) then
  -[#blue]->
  :foo2;
  -[#green,dashed]-> The text can
  also be on several lines;
  :foo3;
else
  -[#black,dotted]->
  :foo4;
endif
-[#gray,bold]->
:foo5;
@enduml
```

## Grouping: Group, Partition, Package, Rectangle, Card

```plantuml
@startuml
start
partition #lightGreen "Input Interface" {
    :read config file;
    :init internal variable;
}
partition Running {
    :wait for user interaction;
    :print information;
}
stop
@enduml
```

## Swimlanes

Swimlanes are defined with `|Name|`. Optional background color and alias supported.

```plantuml
@startuml
|Swimlane1|
start
:foo1;
|#AntiqueWhite|Swimlane2|
:foo2;
:foo3;
|Swimlane1|
:foo4;
|Swimlane2|
:foo5;
stop
@enduml
```

### Swimlanes with alias

```plantuml
@startuml
|#palegreen|f| fisherman
|c| cook
|#gold|e| eater
|f|
start
:go fish;
|c|
:fry fish;
|e|
:eat fish;
stop
@enduml
```

## Additional Resources

For SDL/UML shapes, goto/label, connectors, condition/end styles, `<style>` blocks, Creole formatting examples, and complete examples:
- **`activity-diagram-advanced.md`** — Advanced activity diagram features and styling
