---
name: object-diagram
disable-model-invocation: true
description: This skill provides PlantUML object diagram syntax reference. Use when writing, creating, or debugging PlantUML object diagrams. Applies when users mention "object diagram", "instance diagram", "object instance", "field values", or need to diagram runtime object states, snapshots, or concrete instances in PlantUML.
---

> Source: https://plantuml.com/object-diagram

# PlantUML Object Diagram Reference

An object diagram provides a graphical representation showcasing objects and their relationships at a specific moment in time, offering a snapshot of the system's structure.

## Definition of Objects

Use the `object` keyword to define objects. Use `as` to create an alias for objects with long names.

```plantuml
@startuml
object firstObject
object "My Second Object" as o2
@enduml
```

## Adding Fields

### Colon Notation

Declare fields one at a time using `:` after the object name.

```plantuml
@startuml
object user
user : name = "Dummy"
user : id = 123
@enduml
```

### Bracket Notation

Group all fields inside curly braces `{}`.

```plantuml
@startuml
object user {
  name = "Dummy"
  id = 123
}
@enduml
```

## Relations Between Objects

The following relationship types are supported. Replace `--` with `..` for dotted lines. Add labels using `:` and cardinality using double-quotes `""`.

| Type           | Symbol   | Description                     |
|----------------|----------|---------------------------------|
| Extension      | `<\|--`  | Specialization in hierarchy     |
| Implementation | `<\|..`  | Interface realization           |
| Composition    | `*--`    | Part cannot exist without whole |
| Aggregation    | `o--`    | Part can exist independently    |
| Dependency     | `-->`    | Object uses another             |
| Weak Dep.      | `..>`    | Weaker dependency form          |

```plantuml
@startuml
object Object01
object Object02
object Object03
object Object04
object Object05
object Object06
object Object07
object Object08

Object01 <|-- Object02
Object03 *-- Object04
Object05 o-- "4" Object06
Object07 .. Object08 : some labels
@enduml
```

## Association Objects (Diamond)

Use the `diamond` keyword to create an association node connecting multiple objects.

```plantuml
@startuml
object o1
object o2
diamond dia
object o3

o1  --> dia
o2  --> dia
dia --> o3
@enduml
```

## Notes

Notes can be attached to objects using directional keywords (`top`, `bottom`, `left`, `right`).

```plantuml
@startuml
object London {
  capital = true
}

note top of London : This is the capital\nof England.

note "This is a floating note" as N1
note "Connected to\nmultiple objects." as N2

object Paris {
  capital = true
}

London .. N2
N2 .. Paris
@enduml
```

### Multi-line Notes with Formatting

```plantuml
@startuml
object Foo
note top of Foo
  Supports <b>bold</b>, <i>italic</i>,
  <u>underline</u>, <size:18>size</size>,
  and <color:royalBlue>color</color>.
end note
@enduml
```

## Packages

Use `package` to group objects. Optional background color can be set with `#color`.

```plantuml
@startuml
package "Application Layer" #DDDDDD {
  object Controller {
    name = "MainController"
  }
  object Service {
    name = "UserService"
  }
  Controller --> Service
}

package "Data Layer" {
  object Repository {
    name = "UserRepository"
  }
}

Service --> Repository
@enduml
```

### Package Styles

```plantuml
@startuml
package foo1 <<Node>> {
  object obj1
}
package foo2 <<Rectangle>> {
  object obj2
}
package foo3 <<Folder>> {
  object obj3
}
package foo4 <<Frame>> {
  object obj4
}
package foo5 <<Cloud>> {
  object obj5
}
package foo6 <<Database>> {
  object obj6
}
@enduml
```

## Stereotypes

Define custom stereotypes with optional spot characters and colors.

```plantuml
@startuml
object Config << (S,#FF7700) Singleton >>
object Event << (E,orchid) >>

Config : instance = "global"
Event : type = "click"
@enduml
```

## Skinparam (Styling)

Use `skinparam` to customize colors and fonts for object diagram elements.

```plantuml
@startuml
skinparam object {
  BackgroundColor PaleGreen
  ArrowColor SeaGreen
  BorderColor SpringGreen
}

object User {
  name = "Alice"
}
object Order {
  id = 42
}
User "1" --> "many" Order : places
@enduml
```

### Stereotype-specific Styling

```plantuml
@startuml
skinparam object {
  BackgroundColor PaleGreen
  BorderColor SpringGreen
  BackgroundColor<<Important>> Wheat
  BorderColor<<Important>> Tomato
}

object Server <<Important>> {
  status = "active"
}
object Client {
  connected = true
}
Server <-- Client
@enduml
```

## Hide / Show Commands

Control visibility of object members and elements.

```plantuml
@startuml
object Dummy1 {
  +publicField
  -privateField
}
object Dummy2 {
  +anotherField
}

hide Dummy2 fields
@enduml
```

### Hide Unlinked Objects

```plantuml
@startuml
object Connected1
object Connected2
object Unlinked

Connected1 --> Connected2

hide @unlinked
@enduml
```

## Map Table or Associative Array

Use the `map` keyword to define key-value map tables with `=>` as the separator.

### Basic Map

```plantuml
@startuml
map CapitalCity {
  UK => London
  USA => Washington
  Germany => Berlin
}
@enduml
```

### Map with Title

```plantuml
@startuml
map "Map **Country => CapitalCity**" as CC {
  UK => London
  USA => Washington
  Germany => Berlin
}
@enduml
```

### Typed Map

```plantuml
@startuml
map "map: Map<Integer, String>" as users {
  1 => Alice
  2 => Bob
  3 => Charlie
}
@enduml
```

### Map Linked to Objects

Use `*->` inside a map entry to link a value to an object.

```plantuml
@startuml
object London

map CapitalCity {
  UK *-> London
  USA => Washington
  Germany => Berlin
}
@enduml
```

### Map with Multiple Object Links

```plantuml
@startuml
object London
object Washington
object Berlin
object NewYork

map CapitalCity {
  UK *-> London
  USA *--> Washington
  Germany *---> Berlin
}

NewYork --> CapitalCity::USA
@enduml
```

### Map Entry References

Use `MapName::key` to reference individual entries in a map for external links.

```plantuml
@startuml
object Foo
map Bar {
  abc=>
  def=>
}
object Baz

Bar::abc --> Baz : Label one
Foo --> Bar::def : Label two
@enduml
```

### Map with Packages

```plantuml
@startuml
package foo {
    object baz
}

package bar {
    map A {
        b *-> foo.baz
        c =>
    }
}

A::c --> foo
@enduml
```

## PERT Diagrams with Maps

Maps can be used to create Program Evaluation and Review Technique (PERT) diagrams.

```plantuml
@startuml PERT
left to right direction
' Horizontal lines: -->, <--, <-->
' Vertical lines: ->, <-, <->
title PERT: Project Name

map Kick.Off {
}
map task.1 {
    Start => End
}
map task.2 {
    Start => End
}
map task.3 {
    Start => End
}
map task.4 {
    Start => End
}
map task.5 {
    Start => End
}
Kick.Off --> task.1 : Label 1
Kick.Off --> task.2 : Label 2
Kick.Off --> task.3 : Label 3
task.1 --> task.4
task.2 --> task.4
task.3 --> task.4
task.4 --> task.5 : Label 4
@enduml
```

## Display JSON Data on Object Diagram

Embed JSON data alongside objects and classes using the `json` keyword.

```plantuml
@startuml
class Class
object Object
json JSON {
   "fruit":"Apple",
   "size":"Large",
   "color": ["Red", "Green"]
}
@enduml
```

## Layout Direction

Use `left to right direction` or `top to bottom direction` to control layout flow.

```plantuml
@startuml
left to right direction

object User {
  name = "Alice"
}
object Session {
  id = "abc123"
}
object Cart {
  items = 3
}

User --> Session
Session --> Cart
@enduml
```

## Validation

After writing a `.puml` file or a PlantUML fenced block in Markdown, always validate the syntax:

- **Local** (preferred): `bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh <file.puml>`
- **Online** (fallback): `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/validate_online.py <file.puml>`

For PlantUML blocks embedded in Markdown, extract the content to a temporary `.puml` file before validating. If validation fails, read the error output, fix the syntax, and re-validate.
