# Sequence Diagram — Advanced Reference

> Source: https://plantuml.com/sequence-diagram

## Autonumbering

### Basic, Start, and Increment

```plantuml
@startuml
autonumber
Bob -> Alice : Authentication Request
Bob <- Alice : Authentication Response

autonumber 15
Bob -> Alice : Another authentication Request
Bob <- Alice : Another authentication Response

autonumber 40 10
Bob -> Alice : Yet another authentication Request
Bob <- Alice : Yet another authentication Response
@enduml
```

### Formatting with Double Quotes

Use Java `DecimalFormat` patterns (`0`, `#`, `.`) inside double-quoted strings.

```plantuml
@startuml
autonumber "<b>[000]"
Bob -> Alice : Authentication Request
Bob <- Alice : Authentication Response

autonumber 15 "<b>(<u>##</u>)"
Bob -> Alice : Another authentication Request
Bob <- Alice : Another authentication Response

autonumber 40 10 "<font color=red><b>Message 0  "
Bob -> Alice : Yet another authentication Request
Bob <- Alice : Yet another authentication Response
@enduml
```

### Stop and Resume

```plantuml
@startuml
autonumber 10 10 "<b>[000]"
Bob -> Alice : Authentication Request
Bob <- Alice : Authentication Response

autonumber stop
Bob -> Alice : dummy

autonumber resume "<font color=red><b>Message 0  "
Bob -> Alice : Yet another authentication Request
Bob <- Alice : Yet another authentication Response

autonumber stop
Bob -> Alice : dummy

autonumber resume 1 "<font color=blue><b>Message 0  "
Bob -> Alice : Yet another authentication Request
Bob <- Alice : Yet another authentication Response
@enduml
```

### Hierarchical Autonumber

```plantuml
@startuml
autonumber 1.1.1
Alice -> Bob: message 1
Alice -> Bob: message 2

autonumber inc A
Alice -> Bob: message 3

autonumber inc B
Alice -> Bob: message 4
Alice -> Bob: message 5

autonumber inc A
Alice -> Bob: message 6
Alice -> Bob: message 7
@enduml
```

### Autonumber Variable

Use `%autonumber%` to reference the current value inside messages.

```plantuml
@startuml
autonumber 10
Alice -> Bob
note right
    the <U+0025>autonumber<U+0025> works everywhere.
    Here, its value is **%autonumber%**
end note
Bob --> Alice: //This is the response %autonumber%//
@enduml
```

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

## Special Arrow Types

```plantuml
@startuml
Bob ->x Alice : lost message
Bob ->> Alice : thin arrow
Bob -\ Alice : half arrow (top)
Bob \\- Alice : half arrow (bottom)
Bob //-- Alice : dotted thin arrow
Bob ->o Alice : arrow with circle head
Bob o\\-- Alice : reversed circle dotted
Bob <-> Alice : bidirectional
Bob <->o Alice : bidirectional with circle
@enduml
```

## Incoming and Outgoing Messages

Use `[` and `]` for messages from/to outside the diagram.

```plantuml
@startuml
[-> A: DoWork
activate A
A -> A: Internal call
A ->] : << createRequest >>
A <--] : RequestCreated
[<- A: Done
deactivate A
@enduml
```

### Short Arrows with `?`

```plantuml
@startuml
?-> Alice  : ""?->""\n**short** to actor
[-> Alice  : ""[->""\n**from start** to actor
Alice ->]  : ""->]""\nfrom actor **to end**
Alice ->?  : ""->?""\nfrom actor **short**
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

## Note Shapes

`hnote` for hexagonal, `rnote` for rectangular notes.

```plantuml
@startuml
caller -> server : conReq
hnote over caller : idle
caller <- server : worklist
rnote over server
    "r]" as rectangle
    "h]" as hexagon
end rnote
@enduml
```

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
