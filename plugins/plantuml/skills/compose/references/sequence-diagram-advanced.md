# Sequence Diagram — Advanced Reference

> Source: https://plantuml.com/sequence-diagram

## Actor Style

Change with `skinparam actorStyle`: `stick` (default), `awesome`, `Hollow`.

```plantuml
@startuml
skinparam actorStyle awesome
actor Alice
actor Bob
Alice -> Bob: hello
@enduml
```

## Anchors and Duration (Teoz)

Use `!pragma teoz true` to enable. Use `{name}` for anchors and `<->` for duration arrows.

```plantuml
@startuml
!pragma teoz true

{start} Alice -> Bob : start doing things during duration
Bob -> Max : something
Max -> Bob : something else
{end} Bob -> Alice : finish

{start} <-> {end} : some time
@enduml
```

## Stereotypes and Custom Spots

```plantuml
@startuml
participant "Famous Bob" as Bob << Generated >>
participant Alice << (C,#ADD1B2) Testable >>

Bob -> Alice : First message
@enduml
```

Remove guillemets: `skinparam guillemet false`
Position: `skinparam stereotypePosition bottom`

## Aligned Notes (Same Level)

Use `/` prefix to place notes at the same level.

```plantuml
@startuml
note over Alice : initial state of Alice
/ note over Bob : initial state of Bob
Bob -> Alice : hello
@enduml
```

## Removing Participants

Use `hide`, `show`, or `remove` to control visibility.

```plantuml
@startuml
Alice -> Bob : hello
Bob -> Charlie : hello
remove Charlie
@enduml
```

## Partition (Teoz Full-Width Grouping)

```plantuml
@startuml
!pragma teoz true

partition p1
    b -> c : msg
end

partition p2
    a -> b : msg
end
@enduml
```

## Message Span (Teoz)

```plantuml
@startuml
!pragma teoz true
!pragma sequenceMessageSpan true

participant A
participant B
participant C

A -> C : long message spanning B
@enduml
```

## Common Skinparam Settings

```plantuml
@startuml
skinparam sequenceMessageAlign center
skinparam responseMessageBelowArrow true
skinparam maxMessageSize 50
skinparam actorStyle awesome
skinparam stereotypePosition top
skinparam guillemet false

skinparam sequence {
    ArrowColor DarkBlue
    ActorBorderColor DeepSkyBlue
    LifeLineBorderColor blue
    LifeLineBackgroundColor #A9DCDF

    ParticipantBorderColor DeepSkyBlue
    ParticipantBackgroundColor DodgerBlue
    ParticipantFontName Impact
    ParticipantFontSize 17
    ParticipantFontColor #A9DCDF

    ActorBackgroundColor aqua
    ActorFontColor DeepSkyBlue
    ActorFontSize 17
    ActorFontName Aapex
}

actor User
participant "First Class" as A
participant "Second Class" as B
participant "Last Class" as C

User -> A: DoWork
activate A

A -> B: Create Request
activate B

B -> C: DoWork
activate C
C --> B: WorkDone
destroy C

B --> A: Request Created
deactivate B

A --> User: Done
deactivate A
@enduml
```

### Padding

```plantuml
@startuml
skinparam ParticipantPadding 20
skinparam BoxPadding 10

box "Foo1"
participant Alice1
participant Alice2
end box
box "Foo2"
participant Bob1
participant Bob2
end box
Alice1 -> Bob1 : hello
Alice1 -> Alice2 : hello
@enduml
```
