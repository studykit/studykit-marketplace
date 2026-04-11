> Source: https://plantuml.com/use-case-diagram

# PlantUML Use Case Diagram Reference

## Defining Use Cases

Use cases are enclosed in parentheses. You can also use the `usecase` keyword. An alias can be assigned with the `as` keyword. Newlines can be inserted with `\n`.

```plantuml
@startuml
(First usecase)
(Another usecase) as (UC2)
usecase UC3
usecase (Last\nusecase) as UC4
@enduml
```

## Defining Actors

Actors are enclosed in colons. You can also use the `actor` keyword. An alias can be assigned with the `as` keyword.

```plantuml
@startuml
:First Actor:
:Another\nactor: as Man2
actor Woman3
actor :Last actor: as Person1
@enduml
```

## Actor Styles

You can change the actor rendering style using `skinparam actorStyle`.

**Default (stick man):**

```plantuml
@startuml
skinparam actorStyle default
:User: --> (Use)
@enduml
```

**Awesome man:**

```plantuml
@startuml
skinparam actorStyle awesome
:User: --> (Use)
@enduml
```

**Hollow man:**

```plantuml
@startuml
skinparam actorStyle hollow
:User: --> (Use)
@enduml
```

## Basic Use Case Example

Connect actors to use cases with arrows. Use `-->` for vertical arrows and `->` for horizontal arrows. You can add labels with `:`.

```plantuml
@startuml
User -> (Start)
User --> (Use the application) : A small label
:Main Admin: ---> (Use the application) : This is\nyet another\nlabel
@enduml
```

## Use Case Descriptions (Multiline)

You can define multi-line descriptions using the `as` keyword with double quotes. Separators like `--`, `==`, `..`, and `__` can be used inside descriptions.

```plantuml
@startuml
usecase UC1 as "You can use
several lines to define your usecase.
You can also use separators.
--
Several separators are possible.
==
And you can add titles:
..Conclusion..
This allows large description."
@enduml
```

## Arrows and Connections

### Basic Arrows

The number of dashes controls arrow length. More dashes means a longer arrow.

```plantuml
@startuml
:actor1: --> (usecase1)
:actor2: ---> (usecase2)
:actor3: ----> (usecase3)
@enduml
```

### Arrow Directions

You can use `-left->`, `-right->`, `-up->`, and `-down->` to control direction. Shortened forms like `-l->`, `-r->`, `-u->`, `-d->` also work.

```plantuml
@startuml
:user: -left-> (dummyLeft)
:user: -right-> (dummyRight)
:user: -up-> (dummyUp)
:user: -down-> (dummyDown)
@enduml
```

### Include and Extend Relationships

Use dotted arrows (`.>`) with labels for include and extend relationships.

```plantuml
@startuml
(checkout) .> (payment) : <<include>>
(help) .> (checkout) : <<extend>>
@enduml
```

### Inheritance (Generalization)

Use `<|--` for inheritance between actors or use cases.

```plantuml
@startuml
:User: <|-- :Admin:
(Start) <|-- (Use)
@enduml
```

### Reversed Arrows

Arrows can be reversed.

```plantuml
@startuml
(Use case 1) <.. :user:
(Use case 2) <- :user:
@enduml
```

## Grouping with Packages and Rectangles

### Package

```plantuml
@startuml
left to right direction

actor Guest as g
package Professional {
  actor Chef as c
  actor "Food Critic" as fc
}

package Restaurant {
  usecase "Eat Food" as UC1
  usecase "Pay for Food" as UC2
  usecase "Drink" as UC3
  usecase "Review" as UC4
}

fc --> UC4
g --> UC1
g --> UC2
g --> UC3
@enduml
```

### Rectangle

Use `rectangle` to define a system boundary.

```plantuml
@startuml
left to right direction
actor "Food Critic" as fc
rectangle Restaurant {
  usecase "Eat Food" as UC1
  usecase "Pay for Food" as UC2
  usecase "Drink" as UC3
}
fc --> UC1
fc --> UC2
fc --> UC3
@enduml
```

## Notes

Add notes to elements with `note left of`, `note right of`, `note top of`, or `note bottom of`. You can also create floating notes.

```plantuml
@startuml
:Main Admin: as Admin
(Use the application) as (Use)

User -> (Start)
User --> (Use)

Admin ---> (Use)

note right of Admin : This is an example.

note right of (Use)
  A note can also
  be on several lines
end note

note "This note is connected\nto several objects." as N2
(Start) .. N2
N2 .. (Use)
@enduml
```

## Stereotypes

Add stereotypes with `<< >>` after the element name.

```plantuml
@startuml
User << Human >>
:Main Database: as MySql << Application >>
(Start) << One Shot >>
(Use the application) as (Use) << Main >>

User -> (Start)
User --> (Use)
MySql --> (Use)
@enduml
```

## Diagram Direction

### Left to Right Direction

By default, diagrams flow top to bottom. Use `left to right direction` to change the layout.

```plantuml
@startuml
left to right direction
user1 --> (Usecase 1)
user2 --> (Usecase 2)
@enduml
```

### Top to Bottom (Default)

```plantuml
@startuml
top to bottom direction
user1 --> (Usecase 1)
user2 --> (Usecase 2)
@enduml
```

## Inline Colors and Styles

### Element Colors

You can set background color, line color, line style, and text color directly on elements.

```plantuml
@startuml
actor a
actor b #pink;line:red;line.bold;text:red
usecase c #palegreen;line:green;line.dashed;text:green
usecase d #aliceblue;line:blue;line.dotted;text:blue
@enduml
```

### Arrow Colors and Styles

```plantuml
@startuml
actor foo
foo --> (bar1) #line:red;line.bold;text:red  : red bold
foo --> (bar2) #green;line.dashed;text:green  : green dashed
foo --> (bar3) #blue;line.dotted;text:blue    : blue dotted
@enduml
```

## Skinparam Customization

Use `skinparam` to globally configure colors, fonts, and styles.

```plantuml
@startuml
skinparam handwritten true

skinparam usecase {
  BackgroundColor DarkSeaGreen
  BorderColor DarkSlateGray
  BackgroundColor<< Main >> YellowGreen
  ArrowColor Olive
  ActorBorderColor black
  ActorFontName Courier
  ActorBackgroundColor<< Human >> Gold
}

User << Human >>
:Main Database: as MySql << Application >>
(Start) << One Shot >>
(Use the application) as (Use) << Main >>

User -> (Start)
User --> (Use)
MySql --> (Use)
@enduml
```

## Business Use Cases and Business Actors

Add a `/` suffix to create business variants of use cases and actors.

```plantuml
@startuml
(First usecase)/
:First Actor:/

actor/ Woman3
usecase/ UC3
@enduml
```

## Splitting Diagrams Across Pages

Use `newpage` to split a diagram into multiple pages.

```plantuml
@startuml
:actor1: --> (Usecase1)
newpage
:actor2: --> (Usecase2)
@enduml
```

## Title, Header, Footer, Legend

```plantuml
@startuml
title My Use Case Diagram
header Page Header
footer Page %page% of %lastpage%

legend right
  Short description
endlegend

:actor1: --> (usecase1)
:actor2: --> (usecase2)
@enduml
```

## Complete Example

A comprehensive example combining multiple features.

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle

actor customer
actor clerk

rectangle checkout {
  customer -- (checkout)
  (checkout) .> (payment) : <<include>>
  (help) .> (checkout) : <<extend>>
  (checkout) -- clerk
}
@enduml
```

## Mixing with JSON/YAML (allowmixing)

You can embed JSON or YAML data alongside use case elements.

```plantuml
@startuml
allowmixing

actor Actor
usecase Usecase

json JSON {
  "fruit":"Apple",
  "size":"Large",
  "color": ["Red", "Green"]
}
@enduml
```
