---
name: styles
disable-model-invocation: true
description: Structurizr DSL styles and themes reference. Use when styling C4 diagrams — customizing colors, shapes, borders, fonts, and relationship appearances in Structurizr DSL.
---

> Source: https://docs.structurizr.com/dsl/cookbook/element-styles/

# Styles Reference

## Element Styles

Apply styles to elements by matching their tags.

```
styles {
    element <tag> {
        shape <shape>
        icon <file|url>
        width <integer>
        height <integer>
        background <#rrggbb>
        color <#rrggbb>
        stroke <#rrggbb>
        strokeWidth <1-10>
        fontSize <integer>
        border <solid|dashed|dotted>
        opacity <0-100>
        metadata <true|false>
        description <true|false>
    }
}
```

### Available Shapes

`Box`, `RoundedBox`, `Circle`, `Ellipse`, `Hexagon`, `Diamond`, `Cylinder`, `Bucket`, `Pipe`, `Person`, `Robot`, `Folder`, `WebBrowser`, `Window`, `Terminal`, `Shell`, `MobileDevicePortrait`, `MobileDeviceLandscape`, `Component`

### Default Tags

Every element gets `Element` plus its type tag:
- `Person`
- `Software System`
- `Container`
- `Component`
- `Deployment Node`
- `Infrastructure Node`

### Common Patterns

```
styles {
    element "Person" {
        shape Person
        background #08427b
        color #ffffff
    }
    element "Software System" {
        background #1168bd
        color #ffffff
    }
    element "Container" {
        background #438dd5
        color #ffffff
    }
    element "Component" {
        background #85bbf0
        color #000000
    }
    element "Database" {
        shape Cylinder
    }
    element "External" {
        background #999999
        color #ffffff
        border dashed
    }
    element "Queue" {
        shape Pipe
    }
}
```

## Relationship Styles

```
styles {
    relationship <tag> {
        thickness <integer>
        color <#rrggbb>
        style <solid|dashed|dotted>
        routing <Direct|Orthogonal|Curved>
        fontSize <integer>
        width <integer>
        position <0-100>
        opacity <0-100>
    }
}
```

Default tag: `Relationship` (applies to all relationships).

### Style Specific Relationships

Add custom tags to relationships:

```
model {
    a -> b "Uses" "HTTPS" {
        tags "Secure"
    }
}

views {
    styles {
        relationship "Secure" {
            color #00aa00
            style dashed
        }
    }
}
```

## Group Styles

```
styles {
    element "Group" {
        color #ff0000
    }
    element "Group:Team A" {
        color #0000ff
    }
}
```

## Light/Dark Mode

```
styles {
    light {
        element "Software System" {
            background #1168bd
            color #ffffff
        }
    }
    dark {
        element "Software System" {
            background #2196F3
            color #ffffff
        }
    }
}
```

## Themes

Apply predefined themes:

```
views {
    theme default
    theme https://static.structurizr.com/themes/amazon-web-services-2023.01.31/theme.json
}
```

Multiple themes:

```
views {
    themes default https://static.structurizr.com/themes/amazon-web-services-2023.01.31/theme.json
}
```
