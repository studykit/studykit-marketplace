# Class Diagram — Advanced Reference

> Source: https://plantuml.com/class-diagram

## Bracketed Relationship Styles

Customize line style, color, and thickness on arrows.

**Line styles:** `[bold]`, `[dashed]`, `[dotted]`, `[hidden]`, `[plain]`

```plantuml
@startuml
class foo
foo --> bar : normal
foo -[bold]-> bar1 : bold
foo -[dashed]-> bar2 : dashed
foo -[dotted]-> bar3 : dotted
foo -[hidden]-> bar4 : hidden
foo -[plain]-> bar5 : plain
@enduml
```

**Line color:**

```plantuml
@startuml
class foo
foo -[#red]-> bar1 : red
foo -[#green]-> bar2 : green
foo -[#blue]-> bar3 : blue
@enduml
```

**Line thickness:**

```plantuml
@startuml
class foo
foo -[thickness=1]-> bar1 : 1
foo -[thickness=4]-> bar2 : 4
foo -[thickness=16]-> bar3 : 16
@enduml
```

**Combined:**

```plantuml
@startuml
class foo
foo -[#red,dashed,thickness=2]-> bar2
foo -[#green,dotted,thickness=4]-> bar3
foo -[#blue,plain,thickness=8]-> bar4
@enduml
```

## Association Classes

```plantuml
@startuml
class Student {
  Name
}
class Course {
  Name
}

Student "0..*" - "1..*" Course
(Student, Course) .. Enrollment

class Enrollment {
  drop()
  cancel()
}
@enduml
```

## Same-Class Associations (Diamond)

```plantuml
@startuml
class Station {
  +name: string
}
class StationCrossing {
  +cost: TimeInterval
}
<> diamond
StationCrossing . diamond
diamond - "from 0..*" Station
diamond - "to 0..*" Station
@enduml
```

## Lollipop Interface

```plantuml
@startuml
class foo
bar ()- foo
foo -() baz
@enduml
```

## Hiding and Removing Members

### Hide Empty Members

```plantuml
@startuml
hide empty members
class Dummy
class Foo {
  +method()
}
@enduml
```

### Scoped Hiding

Options: class name, interface, enum, `<<stereotype>>`, visibility level.

```plantuml
@startuml
interface List
class Dummy

hide interface fields
hide interface methods
hide Dummy fields

class Foo {
  -privateField
  #protectedField
  +publicMethod()
}

hide private members
hide protected members
@enduml
```

### Hide/Show Circle and Stereotype

```plantuml
@startuml
hide circle
hide stereotype
class Foo
interface Bar
@enduml
```

## Hiding and Removing Classes

```plantuml
@startuml
class C1
class C2
class C3
C1 -- C2
hide @unlinked
@enduml
```

## Tagged Elements

```plantuml
@startuml
class C1 $tag1
class C2 $tag2
class C3 $tag1
C1 -- C2
remove $tag1
@enduml
```

Restore specific: `remove *` then `restore $tag1`

## Layout Helpers

### Together Grouping

```plantuml
@startuml
together {
  class Together1
  class Together2
  class Together3
}
class Bar1
Together1 - Together2
Together2 - Together3
Together2 -[hidden]--> Bar1
@enduml
```

### Hidden Links

Use `[hidden]` to influence layout without visible arrows.

## Notes on Links

```plantuml
@startuml
class Dummy
Dummy --> Foo : A link
note on link #red: note that is red

Dummy --> Foo2 : Another link
note right on link #blue
  this is my note on right link
end note
@enduml
```

## Skinparam Customization

### Class Colors

```plantuml
@startuml
skinparam class {
  BackgroundColor PaleGreen
  ArrowColor SeaGreen
  BorderColor SpringGreen
}
skinparam stereotypeCBackgroundColor YellowGreen
Class01 "1" *-- "many" Class02 : contains
@enduml
```

### Stereotype-Specific Styling

```plantuml
@startuml
skinparam class {
  BackgroundColor<<Foo>> Wheat
  BorderColor<<Foo>> Tomato
}
class Foo <<Foo>>
class Bar
@enduml
```

### Color Gradients

Gradient symbols: `|` (vertical), `/` (diagonal), `\` (reverse diagonal), `-` (horizontal).

```plantuml
@startuml
skinparam classBackgroundColor Wheat|CornflowerBlue
class Foo #red-green
class Bar #blue\9932CC
@enduml
```

## Splitting Large Diagrams

```plantuml
@startuml
page 2x2
skinparam pageMargin 10
skinparam pageExternalColor gray
skinparam pageBorderColor black

class BaseClass

namespace net.hierarchical #DDDDDD {
  .BaseClass <|-- Move
  .Move <|-- RookMove
}
@enduml
```
