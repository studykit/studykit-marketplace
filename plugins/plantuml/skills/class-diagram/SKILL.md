---
name: class-diagram
disable-model-invocation: true
description: This skill provides PlantUML class diagram syntax reference. Use when writing, creating, or debugging PlantUML class diagrams. Applies when users mention "class diagram", "inheritance", "interface", "association", "composition", "aggregation", or need to diagram object-oriented structures, relationships, or type hierarchies in PlantUML.
---

> Source: https://plantuml.com/class-diagram

# PlantUML Class Diagram Reference

## Class Declaration

Keywords: `abstract`, `abstract class`, `annotation`, `circle`, `class`, `dataclass`, `diamond`, `entity`, `enum`, `exception`, `interface`, `metaclass`, `protocol`, `record`, `stereotype`, `struct`.

```plantuml
@startuml
abstract class AbstractList
interface List
class ArrayList
enum TimeUnit {
  DAYS
  HOURS
  MINUTES
}
annotation SuppressWarnings
@enduml
```

Short forms: `()` for circle, `<>` for diamond.

## Fields and Methods

```plantuml
@startuml
class Dummy {
  String data
  void methods()
}

class Flight {
  flightNumber : Integer
  departureTime : Date
}
@enduml
```

Override parser: `{field}` forces field, `{method}` forces method.

## Visibility Modifiers

| Character | Visibility |
|-----------|-----------|
| `-` | private |
| `#` | protected |
| `~` | package private |
| `+` | public |

```plantuml
@startuml
class Dummy {
  -field1
  #field2
  ~method1()
  +method2()
}
@enduml
```

Disable icons: `skinparam classAttributeIconSize 0`

## Static and Abstract Members

```plantuml
@startuml
class Dummy {
  {static} String id
  {abstract} void methods()
}
@enduml
```

## Separators in Class Body

Use `--`, `..`, `==`, `__` with optional titles.

```plantuml
@startuml
class User {
  .. Simple Getter ..
  + getName()
  + getAddress()
  .. Some setter ..
  + setName()
  __ private data __
  int age
  -- encrypted --
  String password
}
@enduml
```

## Generics

```plantuml
@startuml
class Foo<? extends Element> {
  int size()
}
Foo *- Element
@enduml
```

## Relationships

| Type | Symbol | Drawing |
|------|--------|---------|
| Extension (inheritance) | `<\|--` | Solid line, closed triangle |
| Implementation | `<\|..` | Dotted line, closed triangle |
| Composition | `*--` | Solid line, filled diamond |
| Aggregation | `o--` | Solid line, open diamond |
| Association | `-->` | Solid line, open arrow |
| Dependency | `..>` | Dotted line, open arrow |

Additional arrow heads: `#`, `x`, `}`, `+`, `^`

### Horizontal vs Vertical

Double dash `--` = vertical. Single dash `-` = horizontal.

### Labels and Cardinality

```plantuml
@startuml
Class01 "1" *-- "many" Class02 : contains
Driver - Car : drives >
Car *- Wheel : has 4 >
@enduml
```

### Direction Control

Use `-left->`, `-right->`, `-up->`, `-down->` (or `-l->`, `-r->`, `-u->`, `-d->`).

## Extends and Implements Keywords

```plantuml
@startuml
class ArrayList implements List
class ArrayList extends AbstractList
class A extends B, C {
}
@enduml
```

## Stereotypes and Custom Spots

```plantuml
@startuml
class System << (S,#FF7700) Singleton >>
class Date << (D,orchid) >>
@enduml
```

## Packages

```plantuml
@startuml
package "Classic Collections" #DDDDDD {
  Object <|-- ArrayList
}

package com.plantuml {
  Object <|-- Demo1
  Demo1 *- Demo2
}
@enduml
```

Package styles: `<<Node>>`, `<<Rectangle>>`, `<<Folder>>`, `<<Frame>>`, `<<Cloud>>`, `<<Database>>`

### Namespaces

```plantuml
@startuml
set separator ::
class X1::X2::foo {
  some info
}
@enduml
```

Disable: `set separator none`

## Notes

```plantuml
@startuml
class Object

note top of Object : In java, every class\nextends this one.

note "This is a floating note" as N1
Object .. N1
@enduml
```

### Notes on Fields and Methods

```plantuml
@startuml
class A {
  {static} int counter
  +void {abstract} start(int timeout)
}

note right of A::counter
  This member is annotated
end note
@enduml
```

## Additional Resources

For bracketed relationship styles (color, thickness, dashed), association classes, diamond associations, lollipop interfaces, hide/remove members and classes, tagged elements, layout helpers, skinparam customization, and large diagram splitting:
- **`references/advanced.md`** — Advanced class diagram features and styling

## Validation

After writing a `.puml` file or a PlantUML fenced block in Markdown, always validate the syntax:

- **Local** (preferred): `bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh <file.puml>`
- **Online** (fallback): `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/validate_online.py <file.puml>`

For PlantUML blocks embedded in Markdown, extract the content to a temporary `.puml` file before validating. If validation fails, read the error output, fix the syntax, and re-validate.
