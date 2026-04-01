> Source: https://docs.structurizr.com/dsl/language

# Structurizr DSL Language Reference

## Table of Contents

1. [Workspace](#workspace)
2. [Model Elements](#model-elements)
3. [Relationships](#relationships)
4. [Deployment Elements](#deployment-elements)
5. [Views](#views)
6. [View Content Control](#view-content-control)
7. [Styles](#styles)
8. [Themes and Terminology](#themes-and-terminology)
9. [Configuration](#configuration)
10. [Advanced Features](#advanced-features)

---

## Workspace

Top-level construct wrapping model and views.

```
workspace [name] [description] {
    [properties]
    [!identifiers]
    [!docs]
    [!adrs]
    model { ... }
    views { ... }
    configuration { ... }
}
```

Can extend another workspace: `workspace extends <file|url>`

---

## Model Elements

### person

```
person <name> [description] [tags] {
    [description] [tags] [url] [properties] [perspectives] [-> relationships]
}
```
Default tags: `Element`, `Person`

### softwareSystem

```
softwareSystem <name> [description] [tags] {
    [!docs] [!adrs] [group] [container]
    [description] [tags] [url] [properties] [perspectives] [-> relationships]
}
```
Default tags: `Element`, `Software System`

### container

```
container <name> [description] [technology] [tags] {
    [!docs] [!adrs] [group] [component] [!components]
    [description] [technology] [tags] [url] [properties] [perspectives] [-> relationships]
}
```
Default tags: `Element`, `Container`

### component

```
component <name> [description] [technology] [tags] {
    [!docs] [!adrs] [group]
    [description] [technology] [tags] [url] [properties] [perspectives] [-> relationships]
}
```
Default tags: `Element`, `Component`

### element (custom)

```
element <name> [metadata] [description] [tags] {
    [description] [tags] [url] [properties] [perspectives] [-> relationships]
}
```
Default tags: `Element`

---

## Relationships

### Syntax

Explicit source:
```
<identifier> -> <identifier> [description] [technology] [tags] {
    [tags] [url] [properties] [perspectives]
}
```

Context-scoped (inside an element block):
```
-> <identifier> [description] [technology] [tags]
```

Remove relationship:
```
-/> <identifier>
```

### Permitted Source-Destination Combinations

- Person -> Person, Software System, Container, Component
- Software System -> Person, Software System, Container, Component
- Container -> Person, Software System, Container, Component
- Component -> Person, Software System, Container, Component
- Deployment Node -> Deployment Node
- Infrastructure Node -> Deployment Node, Infrastructure Node, Software System Instance, Container Instance
- Software System Instance -> Infrastructure Node
- Container Instance -> Infrastructure Node

---

## Deployment Elements

### deploymentEnvironment

```
deploymentEnvironment <name> {
    [group] [deploymentGroup] [deploymentNode] [-> relationships]
}
```

### deploymentNode

```
deploymentNode <name> [description] [technology] [tags] [instances] {
    [group] [deploymentNode] [infrastructureNode]
    [softwareSystemInstance] [containerInstance] [instanceOf]
    [-> relationships] [description] [technology] [instances] [tags] [url] [properties] [perspectives]
}
```
Default tags: `Element`, `Deployment Node`

Instances support ranges: `"4"`, `"1..N"`, `"0..1"`, `"1.._"`

### infrastructureNode

```
infrastructureNode <name> [description] [technology] [tags] {
    [-> relationships] [description] [technology] [tags] [url] [properties] [perspectives]
}
```
Default tags: `Element`, `Infrastructure Node`

### softwareSystemInstance / containerInstance

```
softwareSystemInstance <identifier> [deploymentGroups] [tags] { ... }
containerInstance <identifier> [deploymentGroups] [tags] { ... }
```

### instanceOf (alias)

```
instanceOf <identifier> [deploymentGroups] [tags] { ... }
```

### healthCheck

```
healthCheck <name> <url> [interval] [timeout]
```

---

## Views

### systemLandscape

```
systemLandscape [key] [description] {
    [include] [exclude] [autoLayout] [default] [animation] [title] [description] [properties]
}
```

### systemContext

```
systemContext <software system identifier> [key] [description] {
    [include] [exclude] [autoLayout] [default] [animation] [title] [description] [properties]
}
```

### container

```
container <software system identifier> [key] [description] {
    [include] [exclude] [autoLayout] [default] [animation] [title] [description] [properties]
}
```

### component

```
component <container identifier> [key] [description] {
    [include] [exclude] [autoLayout] [default] [animation] [title] [description] [properties]
}
```

### deployment

```
deployment <*|software system identifier> <environment> [key] [description] {
    [include] [exclude] [autoLayout] [default] [animation] [title] [description] [properties]
}
```

### dynamic

```
dynamic <*|software system identifier|container identifier> [key] [description] {
    <element> -> <element> [description] [technology]
    [autoLayout] [default] [title] [description] [properties]
}
```

### filtered

```
filtered <baseKey> <include|exclude> <tags> [key] [description]
```

### custom

```
custom [key] [title] [description] {
    [include] [exclude] [autoLayout] [default] [animation] [title] [description] [properties]
}
```

### image

```
image <*|element identifier> [key] {
    plantuml <file|url|viewKey>
    mermaid <file|url|viewKey>
    kroki <format> <file|url>
    image <file|url>
    [default] [title] [description] [properties]
}
```

---

## View Content Control

### include / exclude

```
include <*|identifier|expression>
exclude <identifier|expression>
```

Relationship patterns:
```
include "<source> -> <destination>"
exclude "* -> *"
```

### autoLayout

```
autoLayout [tb|bt|lr|rl] [rankSeparation] [nodeSeparation]
```

Directions: `tb` (top-bottom, default), `bt` (bottom-top), `lr` (left-right), `rl` (right-left).
Default separation: 300 pixels each.

### animation

```
animation {
    <identifier> [identifier...]
    <identifier> [identifier...]
}
```

---

## Styles

### Element styles

```
element <tag> {
    shape <Box|RoundedBox|Circle|Ellipse|Hexagon|Diamond|Cylinder|Bucket|Pipe|Person|Robot|Folder|WebBrowser|Window|Terminal|Shell|MobileDevicePortrait|MobileDeviceLandscape|Component>
    icon <file|url>
    width <integer>
    height <integer>
    background <#rrggbb|color name>
    color <#rrggbb|color name>
    stroke <#rrggbb|color name>
    strokeWidth <integer: 1-10>
    fontSize <integer>
    border <solid|dashed|dotted>
    opacity <integer: 0-100>
    metadata <true|false>
    description <true|false>
}
```

### Relationship styles

```
relationship <tag> {
    thickness <integer>
    color <#rrggbb|color name>
    style <solid|dashed|dotted>
    routing <Direct|Orthogonal|Curved>
    fontSize <integer>
    width <integer>
    position <integer: 0-100>
    opacity <integer: 0-100>
}
```

### Light/dark mode

```
styles {
    light { [element] [relationship] }
    dark { [element] [relationship] }
}
```

---

## Themes and Terminology

### theme / themes

```
theme <name|url|file>
themes <name|url|file> [name|url|file] ...
```

### terminology

```
terminology {
    person <term>
    softwareSystem <term>
    container <term>
    component <term>
    deploymentNode <term>
    infrastructureNode <term>
    relationship <term>
}
```

---

## Configuration

```
configuration {
    scope <landscape|softwaresystem|none>
    visibility <private|public>
    users {
        <username> <read|write>
    }
    properties { ... }
}
```

---

## Advanced Features

### Properties and metadata

```
properties {
    <name> <value>
}
```

```
tags "Tag1" "Tag2"
tags "Tag1,Tag2"
tag "Tag Name"
```

```
url https://example.com
```

```
perspectives {
    <name> <description> [value]
}
```

### Groups

```
group <name> {
    // elements
}
```

Nested groups require a separator:
```
properties {
    "structurizr.groupSeparator" "/"
}
```

Style individual groups: `element "Group:Company 1" { color #ff0000 }`

### Identifiers

```
!identifiers <hierarchical|flat>
```

### Implied relationships

```
!impliedRelationships <true|false>
```

### Include fragments

```
!include <file|directory|url>
```

### Workspace extension

```
!element <identifier> { ... }
!elements <expression> { ... }
!relationship <identifier> { ... }
!relationships <expression> { ... }
```
