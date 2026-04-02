---
name: component-diagram
disable-model-invocation: true
description: This skill provides PlantUML component diagram syntax reference. Use when writing, creating, or debugging PlantUML component diagrams. Applies when users mention "component diagram", "interface", "port", "connector", "package", "module", or need to diagram software architecture, system components, or service dependencies in PlantUML.
---

> Source: https://plantuml.com/component-diagram

# PlantUML Component Diagram Reference

## Components

Components are declared using square brackets `[ComponentName]` or the `component` keyword. Use `as` for aliasing and `\n` for line breaks within names.

```plantuml
@startuml
[First component]
[Another component] as Comp2
component Comp3
component [Last\ncomponent] as Comp4
@enduml
```

### Naming Exceptions

Component names starting with `$` can conflict with tag syntax in some contexts. A safer pattern is to use a quoted display name with a regular alias:

```plantuml
@startuml
component "$C1" as dollarC1
component "$C2" as dollarC2
dollarC1 --> dollarC2
@enduml
```

## Interfaces

Interfaces are declared using parentheses `()` or the `interface` keyword.

```plantuml
@startuml
() "First Interface"
() "Another interface" as Interf2
interface Interf3
interface "Last\ninterface" as Interf4

[component]
footer //Adding "component" to force diagram to be a **component diagram**//
@enduml
```

## Basic Example

Use `-` for solid lines and `..>` for dotted arrows. Add labels with `: label`.

```plantuml
@startuml
DataAccess - [First Component]
[First Component] ..> HTTP : use
@enduml
```

## Links and Arrows

### Line Styles

| Syntax | Description |
|--------|-------------|
| `--` | Solid line |
| `..` | Dotted line |
| `-->` | Solid arrow |
| `..>` | Dotted arrow |
| `-` | Short solid line |
| `->` | Short solid arrow |

### Arrow Length

More dashes make the arrow longer:

```plantuml
@startuml
[Component] --> Interface1
[Component] -> Interface2
@enduml
```

Reversed direction:

```plantuml
@startuml
Interface1 <-- [Component]
Interface2 <- [Component]
@enduml
```

### Arrow Direction

Control layout direction with `-left->`, `-right->`, `-up->`, `-down->` (abbreviations: `-l->`, `-r->`, `-u->`, `-d->`):

```plantuml
@startuml
[Component] -left-> left
[Component] -right-> right
[Component] -up-> up
[Component] -down-> down
@enduml
```

### Layout Direction

Use `left to right direction` to change the default top-to-bottom layout:

```plantuml
@startuml
left to right direction
[Component] -left-> left
[Component] -right-> right
[Component] -up-> up
[Component] -down-> down
@enduml
```

## Grouping Components

Use `package`, `node`, `cloud`, `database`, `folder`, or `frame` to group components. These containers can be nested.

```plantuml
@startuml
package "Some Group" {
  HTTP - [First Component]
  [Another Component]
}

node "Other Groups" {
  FTP - [Second Component]
  [First Component] --> FTP
}

cloud {
  [Example 1]
}

database "MySql" {
  folder "This is my folder" {
    [Folder 3]
  }
  frame "Foo" {
    [Frame 4]
  }
}

[Another Component] --> [Example 1]
[Example 1] --> [Folder 3]
[Folder 3] --> [Frame 4]
@enduml
```

## Notes

### Positioned Notes

Attach notes to components with `note top of`, `note bottom of`, `note left of`, `note right of`:

```plantuml
@startuml
[Component] as C

note top of C: A top note

note bottom of C
  A bottom note can also
  be on several lines
end note

note left of C
  A left note can also
  be on several lines
end note

note right of C: A right note
@enduml
```

### Floating Notes

Create a standalone note and link it:

```plantuml
@startuml
[Component] as C

note as N
  A floating note can also
  be on several lines
end note

C .. N
@enduml
```

### Notes on Links

```plantuml
@startuml
interface "Data Access" as DA

DA - [First Component]
[First Component] ..> HTTP : use

note left of HTTP : Web Service only

note right of [First Component]
  A note can also
  be on several lines
end note
@enduml
```

## Long Description

Use square brackets after a component declaration to provide multi-line descriptions:

```plantuml
@startuml
component comp1 [
  This component
  has a long comment
  on several lines
]
@enduml
```

## Individual Colors

Assign colors to components using `#ColorName` or `#HexCode`:

```plantuml
@startuml
component [Web Server] #Yellow
@enduml
```

## Component Style Notation

### UML2 (Default)

```plantuml
@startuml
skinparam componentStyle uml2
interface "Data Access" as DA
DA - [First Component]
[First Component] ..> HTTP : use
@enduml
```

### UML1

```plantuml
@startuml
skinparam componentStyle uml1
interface "Data Access" as DA
DA - [First Component]
[First Component] ..> HTTP : use
@enduml
```

### Rectangle

```plantuml
@startuml
skinparam componentStyle rectangle
interface "Data Access" as DA
DA - [First Component]
[First Component] ..> HTTP : use
@enduml
```

### Nested Components with UML2 vs Rectangle

UML2 style:

```plantuml
@startuml
skinparam BackgroundColor transparent
skinparam componentStyle uml2
package A {
   component "A.1"
   package A.44 {
      [A4.1]
   }
   component "A.2"
   [A.3]
   [A.5]
   [A.6]
}
[a]->[b]
@enduml
```

Rectangle style:

```plantuml
@startuml
skinparam BackgroundColor transparent
skinparam componentStyle rectangle
package A {
   component "A.1"
   package A.44 {
      [A4.1]
   }
   component "A.2"
   [A.3]
   [A.5]
   [A.6]
}
[a]->[b]
@enduml
```

## Using Sprites in Stereotypes

Define custom icons with `sprite` and apply them via stereotypes:

```plantuml
@startuml
sprite $businessProcess [16x16/16] {
FFFFFFFFFFFFFFFF
FFFFFFFFFFFFFFFF
FFFFFFFFFFFFFFFF
FFFFFFFFFFFFFFFF
FFFFFFFFFF0FFFFF
FFFFFFFFFF00FFFF
FF00000000000FFF
FF000000000000FF
FF00000000000FFF
FFFFFFFFFF00FFFF
FFFFFFFFFF0FFFFF
FFFFFFFFFFFFFFFF
FFFFFFFFFFFFFFFF
FFFFFFFFFFFFFFFF
FFFFFFFFFFFFFFFF
FFFFFFFFFFFFFFFF
}

rectangle " End to End\nbusiness process" <<$businessProcess>> {
  rectangle "inner process 1" <<$businessProcess>> as src
  rectangle "inner process 2" <<$businessProcess>> as tgt
  src -> tgt
}
@enduml
```

## Skinparam

### Interface and Component Styling

```plantuml
@startuml
skinparam interface {
  backgroundColor RosyBrown
  borderColor orange
}

skinparam component {
  FontSize 13
  BackgroundColor<<Apache>> Pink
  BorderColor<<Apache>> #FF6655
  FontName Courier
  BorderColor black
  BackgroundColor gold
  ArrowFontName Impact
  ArrowColor #FF6655
  ArrowFontColor #777777
}

() "Data Access" as DA
Component "Web Server" as WS << Apache >>

DA - [First Component]
[First Component] ..> () HTTP : use
HTTP - WS
@enduml
```

### Stereotype-Based Styling

```plantuml
@startuml
skinparam component {
  backgroundColor<<static lib>> DarkKhaki
  backgroundColor<<shared lib>> Green
}

skinparam node {
  borderColor Green
  backgroundColor Yellow
  backgroundColor<<shared_node>> Magenta
}

skinparam databaseBackgroundColor Aqua

[AA] <<static lib>>
[BB] <<shared lib>>
[CC] <<static lib>>

node node1
node node2 <<shared_node>>
database Production
@enduml
```

## Hide or Remove Unlinked Components

### Default (all shown)

```plantuml
@startuml
component C1
component C2
component C3
C1 -- C2
@enduml
```

### Hide Unlinked

```plantuml
@startuml
component C1
component C2
component C3
C1 -- C2

hide @unlinked
@enduml
```

### Remove Unlinked

```plantuml
@startuml
component C1
component C2
component C3
C1 -- C2

remove @unlinked
@enduml
```

## Hide, Remove, or Restore Tagged Components

Tag components with `$tagName` for selective visibility.

### Default (all shown)

```plantuml
@startuml
component C1 $tag13
component C2
component C3 $tag13
C1 -- C2
@enduml
```

### Hide by Tag

```plantuml
@startuml
component C1 $tag13
component C2
component C3 $tag13
C1 -- C2

hide $tag13
@enduml
```

### Remove by Tag

```plantuml
@startuml
component C1 $tag13
component C2
component C3 $tag13
C1 -- C2

remove $tag13
@enduml
```

### Remove Tag then Restore Specific Tag

```plantuml
@startuml
component C1 $tag13 $tag1
component C2
component C3 $tag13
C1 -- C2

remove $tag13
restore $tag1
@enduml
```

### Remove All then Restore Specific Tag

```plantuml
@startuml
component C1 $tag13 $tag1
component C2
component C3 $tag13
C1 -- C2

remove *
restore $tag1
@enduml
```

## Ports

Ports define connection points on component boundaries. Use `port` (bidirectional), `portin` (input), or `portout` (output).

### Basic Port

```plantuml
@startuml
component "C" as c {
  port p1
  port p2
  port p3
  component c1
}

c --> p1
c --> p2
c --> p3
p1 --> c1
p2 --> c1
@enduml
```

### PortIn (Input Ports)

```plantuml
@startuml
component "C" as c {
  portin p1
  portin p2
  portin p3
  component c1
}

c --> p1
c --> p2
c --> p3
p1 --> c1
p2 --> c1
@enduml
```

### PortOut (Output Ports)

```plantuml
@startuml
component C {
  portout p1
  portout p2
  portout p3
  component c1
}

[o]
p1 --> o
p2 --> o
p3 --> o
c1 --> p1
@enduml
```

### Mixing PortIn and PortOut

```plantuml
@startuml
component "C" as i {
  portin p1
  portin p2
  portin p3
  portout po1
  portout po2
  portout po3
  component c1
}

[o]
i --> p1
i --> p2
i --> p3
p1 --> c1
p2 --> c1
po1 --> o
po2 --> o
po3 --> o
c1 --> po1
@enduml
```

## Display JSON Data on Component Diagram

Use `allowmixing` to combine component diagrams with JSON data:

```plantuml
@startuml
allowmixing

component Component
() Interface

json JSON {
  "fruit":"Apple",
  "size":"Large",
  "color": ["Red", "Green"]
}
@enduml
```

## Validation

After writing a `.puml` file or a PlantUML fenced block in Markdown, always validate the syntax:

- **Local** (preferred): `bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh <file.puml>`
- **Online** (fallback): `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/validate_online.py <file.puml>`

For PlantUML blocks embedded in Markdown, extract the content to a temporary `.puml` file before validating. If validation fails, read the error output, fix the syntax, and re-validate.
