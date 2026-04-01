---
name: sequence-diagram
disable-model-invocation: true
description: This skill provides PlantUML sequence diagram syntax reference. Use when writing, creating, or debugging PlantUML sequence diagrams. Applies when users mention "sequence diagram", "message flow", "interaction diagram", "lifeline", or need to diagram request-response patterns, API calls, or message exchanges in PlantUML.
---

> Source: https://plantuml.com/sequence-diagram

# PlantUML Sequence Diagram Reference

## Basic Syntax

Use `->` to draw a message between two participants. Participants do not have to be explicitly declared.

```plantuml
@startuml
Alice -> Bob: Authentication Request
Bob --> Alice: Authentication Response
Alice -> Bob: Another authentication Request
Alice <-- Bob: Another authentication Response
@enduml
```

## Declaring Participants

Use `participant` or shape keywords: `actor`, `boundary`, `control`, `entity`, `database`, `collections`, `queue`.

```plantuml
@startuml
participant Participant as Foo
actor Actor as Foo1
boundary Boundary as Foo2
control Control as Foo3
entity Entity as Foo4
database Database as Foo5
collections Collections as Foo6
queue Queue as Foo7

Foo -> Foo1 : To actor
Foo -> Foo5 : To database
Foo -> Foo7 : To queue
@enduml
```

### Background Colors and Ordering

```plantuml
@startuml
actor Bob #red
participant "I have a really\nlong name" as L #99FF99
participant Last order 30
participant First order 10
@enduml
```

## Arrow Styles

| Syntax | Description |
|--------|-------------|
| `->` | Solid line with arrowhead |
| `-->` | Dotted line with arrowhead |
| `<-` | Reverse solid arrow |
| `<--` | Reverse dotted arrow |
| `-[#red]>` | Colored arrow |

## Message Grouping

Keywords: `alt`/`else`, `opt`, `loop`, `par`/`and`, `break`, `critical`, `group`. Close with `end`.

```plantuml
@startuml
Alice -> Bob: Authentication Request
alt successful case
    Bob -> Alice: Authentication Accepted
else some kind of failure
    Bob -> Alice: Authentication Failure
    group My own label
        Alice -> Log : Log attack start
        loop 1000 times
            Alice -> Bob: DNS Attack
        end
        Alice -> Log : Log attack end
    end
else Another type of failure
    Bob -> Alice: Please repeat
end
@enduml
```

### Secondary Group Labels and Colors

```plantuml
@startuml
alt#Gold #LightBlue Successful case
    Bob -> Alice: Authentication Accepted
else #Pink Failure
    Bob -> Alice: Authentication Failure
end
@enduml
```

## Notes

```plantuml
@startuml
participant Alice
participant Bob

note left of Alice #aqua
    This is displayed
    left of Alice.
end note

note right of Alice: This is displayed right of Alice.
note over Alice: This is displayed over Alice.
note over Alice, Bob #FFAAAA: This is displayed\nover Bob and Alice.
note across: This note is across all participants
@enduml
```

## Divider / Separator

```plantuml
@startuml
== Initialization ==
Alice -> Bob: Authentication Request
Bob --> Alice: Authentication Response

== Repetition ==
Alice -> Bob: Another authentication Request
@enduml
```

## Reference

```plantuml
@startuml
ref over Alice, Bob : init
Alice -> Bob : hello
ref over Bob
    This can be on
    several lines
end ref
@enduml
```

## Delay and Spacing

```plantuml
@startuml
Alice -> Bob: Authentication Request
...
Bob --> Alice: Authentication Response
...5 minutes later...
Bob --> Alice: Good Bye !
|||
Alice -> Bob: message
||45||
Alice -> Bob: another message
@enduml
```

## Lifeline Activation and Deactivation

```plantuml
@startuml
participant User

User -> A: DoWork
activate A

A -> B: << createRequest >>
activate B

B -> C: DoWork
activate C
C --> B: WorkDone
destroy C

B --> A: RequestCreated
deactivate B

A -> User: Done
deactivate A
@enduml
```

### Shortcut Syntax

| Shortcut | Meaning |
|----------|---------|
| `++` | Activate target (optionally with `#color`) |
| `--` | Deactivate source |
| `**` | Create target |
| `!!` | Destroy target |

```plantuml
@startuml
alice -> bob ++ : hello
bob -> bob ++ : self call
bob -> babe **  ++ : create
return done
return rc
bob -> george ** : create
bob -> george !! : delete
return success
@enduml
```

## Return

Use `return` to generate a return message back to the last activated participant.

## Participant Creation

Use `create` to show instantiation at a specific point.

## Box Around Participants

```plantuml
@startuml
box "Internal Service" #LightBlue
    participant Alice
    participant Bob
end box
participant Other

Alice -> Bob : hello
Bob -> Other : hello
@enduml
```

## Mainframe

```plantuml
@startuml
mainframe This is a **mainframe**
Alice -> Bob : hello
Bob -> Alice : ok
@enduml
```

## Page Title, Header, Footer

```plantuml
@startuml
header Page Header
footer Page %page% of %lastpage%
title Example Title
Alice -> Bob : message 1
@enduml
```

## Splitting Diagrams

Use `newpage` to split into multiple pages. `ignore newpage` renders as single image.

## Additional Resources

For autonumbering (basic, hierarchical, formatting), actor styles, special arrow types, incoming/outgoing messages, Teoz anchors/durations, stereotypes, partition, message span, and skinparam customization:
- **`references/advanced.md`** — Advanced sequence diagram features and styling
