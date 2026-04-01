# D2 Language Reference

## Table of Contents

1. [Shapes](#shapes)
2. [Connections](#connections)
3. [Containers](#containers)
4. [Labels](#labels)
5. [Icons](#icons)
6. [Styles](#styles)
7. [Classes (Reusable Styles)](#classes-reusable-styles)
8. [Globs (Bulk Styling)](#globs-bulk-styling)
9. [Layout Direction](#layout-direction)
10. [Text and Markdown](#text-and-markdown)
11. [Imports](#imports)
12. [Comments](#comments)

---

## Shapes

Shapes are the basic building blocks. Declare them by key name:

```d2
# Simple shape (label = key)
server

# Shape with custom label
server: Web Server

# Shape with type
db: Database {
  shape: cylinder
}
```

### Available Shape Types

| Shape | Keyword |
|-------|---------|
| Rectangle | `rectangle` (default) |
| Square | `square` |
| Circle | `circle` |
| Oval | `oval` |
| Diamond | `diamond` |
| Hexagon | `hexagon` |
| Page | `page` |
| Parallelogram | `parallelogram` |
| Document | `document` |
| Cylinder | `cylinder` |
| Queue | `queue` |
| Package | `package` |
| Step | `step` |
| Callout | `callout` |
| Stored Data | `stored_data` |
| Person | `person` |
| C4 Person | `c4-person` |
| Cloud | `cloud` |
| Image (standalone) | `image` |

### Shape with Image

```d2
logo: {
  shape: image
  icon: https://icons.terrastruct.com/essentials%2F073-monitor.svg
}
```

### Multiple Shapes on One Line

Use semicolons:

```d2
a; b; c
```

---

## Connections

Connections link shapes together.

### Connection Operators

| Operator | Direction |
|----------|-----------|
| `--` | Bidirectional (no arrows) |
| `->` | Left to right |
| `<-` | Right to left |
| `<->` | Bidirectional (with arrows) |

### Connection Labels

```d2
server -> db: queries
user -> server: HTTP request
```

### Connection Chaining

```d2
a -> b -> c -> d
```

### Cycles

D2 allows circular references:

```d2
Stage1 -> Stage2 -> Stage3 -> Stage1
```

### Self-Referencing

```d2
server -> server: health check
```

### Arrowhead Customization

```d2
a -> b: {
  source-arrowhead: {
    shape: diamond
    style.filled: true
  }
  target-arrowhead: {
    shape: arrow
    label: 1
  }
}
```

Available arrowhead shapes: `triangle` (default), `arrow`, `diamond`, `circle`, `box`, `cf-one`, `cf-many`, `cross`

Diamond, circle, and box can be styled with `style.filled: true/false`.

---

## Containers

Nesting creates containers (groups):

```d2
cloud: AWS {
  vpc: VPC {
    subnet: Private Subnet {
      server: Web Server
      db: Database {
        shape: cylinder
      }
    }
  }
  server -> db: queries
}
```

### Referencing Nested Objects

Use dot notation:

```d2
cloud.vpc.server -> external_api: calls
```

### Container Labels

```d2
# Shorthand
cloud: My Cloud {
  child
}

# Explicit label keyword
cloud: {
  label: My Cloud
  child
}
```

### Parent Reference with Underscore

Inside nested blocks, `_` references the parent:

```d2
cloud: {
  server: Web Server
  server -> _.external: calls
}
external: External API
```

---

## Labels

```d2
# Key as label (default)
server

# Custom label
server: "My Web Server"

# Explicit label keyword (useful for containers)
server: {
  label: "My Web Server"
}
```

---

## Icons

Add icons to any shape via URL:

```d2
server: Web Server {
  icon: https://icons.terrastruct.com/essentials%2F112-server.svg
}
```

Free icon collection: https://icons.terrastruct.com

For standalone image shapes:

```d2
logo: {
  shape: image
  icon: https://icons.terrastruct.com/aws%2F_Group%20Icons%2FRegion_light-bg.svg
}
```

Local file paths also work with the CLI: `icon: ./my-icon.png`

---

## Styles

Apply styles via the `style` property:

```d2
server: Web Server {
  style: {
    fill: "#1168bd"
    stroke: "#0b4884"
    font-color: "#ffffff"
    font-size: 16
    bold: true
    border-radius: 8
    shadow: true
    opacity: 0.9
  }
}
```

### All Style Properties

| Property | Applies To | Description |
|----------|-----------|-------------|
| `fill` | Shapes | Background color (hex, CSS name, gradient) |
| `stroke` | Shapes, Connections | Border/line color |
| `stroke-width` | Shapes, Connections | Border/line thickness |
| `stroke-dash` | Shapes, Connections | Dashed line pattern |
| `font-color` | Shapes, Connections | Text color |
| `font-size` | Shapes, Connections | Text size |
| `font` | Shapes, Connections | Font family |
| `bold` | Shapes, Connections | Bold text |
| `italic` | Shapes, Connections | Italic text |
| `underline` | Shapes, Connections | Underline text |
| `text-transform` | Shapes, Connections | Case transformation |
| `opacity` | Shapes, Connections | 0 to 1 |
| `border-radius` | Shapes | Rounded corners |
| `shadow` | Shapes | Drop shadow |
| `3d` | Rectangles, Squares | 3D appearance |
| `multiple` | Shapes | Stacked/multiple copies effect |
| `double-border` | Rectangles, Ovals | Double outline |
| `animated` | Connections | Animated flow |
| `fill-pattern` | Shapes | Pattern fill |

### Connection Styles

```d2
a -> b: {
  style: {
    stroke: red
    stroke-width: 3
    stroke-dash: 5
    animated: true
  }
}
```

---

## Classes (Reusable Styles)

Define reusable style templates:

```d2
classes: {
  server: {
    style: {
      fill: "#1168bd"
      font-color: "#ffffff"
      border-radius: 8
    }
  }
  database: {
    shape: cylinder
    style: {
      fill: "#2b7332"
      font-color: "#ffffff"
    }
  }
}

web: Web Server {
  class: server
}
db: PostgreSQL {
  class: database
}
```

Multiple classes (applied left-to-right, later overrides earlier):

```d2
node: {
  class: [server, highlighted]
}
```

---

## Globs (Bulk Styling)

Apply styles to multiple elements at once:

```d2
# All top-level shapes get blue fill
*.style.fill: "#1168bd"

# All shapes at all levels
**.style.stroke: "#333"

# All connections
(* -> *)[*].style.stroke: red

# Exclude specific elements
*.style.fill: blue
exception.style.fill: red
```

---

## Layout Direction

Control the flow direction of the diagram:

```d2
direction: right   # left to right
direction: down    # top to bottom (default)
direction: left    # right to left
direction: up      # bottom to top
```

Can also be set per-container:

```d2
parent: {
  direction: right
  a -> b -> c
}
```

---

## Text and Markdown

Standalone text blocks support Markdown:

```d2
explanation: |md
  # Architecture Overview
  This diagram shows the **main components** of the system.

  - API Gateway handles routing
  - Auth service manages tokens
  - Database stores user data
|
```

Code blocks:

```d2
code_sample: |go
  func main() {
    fmt.Println("Hello")
  }
|
```

LaTeX:

```d2
formula: |latex
  \\sum_{i=0}^{n} x_i
|
```

---

## Imports

Spread D2 across multiple files:

```d2
# Import another .d2 file
...@another-file.d2
```

---

## Comments

```d2
# This is a single-line comment

# D2 does not have block comments — use multiple # lines
```
