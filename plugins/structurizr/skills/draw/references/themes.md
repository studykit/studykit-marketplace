# Structurizr DSL Color Themes

Predefined color palettes for consistent, professional diagrams. Apply these in the `styles` block inside `views`.

## C4 Blue (Default)

The standard C4 model color scheme. Good contrast, widely recognized.

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
    element "External" {
        background #999999
        color #ffffff
        border dashed
    }
    element "Database" {
        shape Cylinder
    }
    element "Queue" {
        shape Pipe
    }
    relationship "Relationship" {
        color #707070
        thickness 2
    }
}
```

## Dark

Dark background tones with bright accents. Modern look, easy on the eyes.

```
styles {
    element "Person" {
        shape Person
        background #1db954
        color #ffffff
    }
    element "Software System" {
        background #2d6a4f
        color #ffffff
    }
    element "Container" {
        background #40916c
        color #ffffff
    }
    element "Component" {
        background #52b788
        color #000000
    }
    element "External" {
        background #555555
        color #ffffff
        border dashed
    }
    element "Database" {
        shape Cylinder
    }
    element "Queue" {
        shape Pipe
    }
    relationship "Relationship" {
        color #95d5b2
        thickness 2
    }
}
```

## Forest Green

Natural green palette. Good for sustainability or nature-related projects.

```
styles {
    element "Person" {
        shape Person
        background #1b4332
        color #ffffff
    }
    element "Software System" {
        background #2d6a4f
        color #ffffff
    }
    element "Container" {
        background #40916c
        color #ffffff
    }
    element "Component" {
        background #74c69d
        color #000000
    }
    element "External" {
        background #6c757d
        color #ffffff
        border dashed
    }
    element "Database" {
        shape Cylinder
    }
    element "Queue" {
        shape Pipe
    }
    relationship "Relationship" {
        color #52b788
        thickness 2
    }
}
```

## Monochrome

Clean grayscale palette. Professional, distraction-free.

```
styles {
    element "Person" {
        shape Person
        background #212529
        color #ffffff
    }
    element "Software System" {
        background #495057
        color #ffffff
    }
    element "Container" {
        background #6c757d
        color #ffffff
    }
    element "Component" {
        background #adb5bd
        color #000000
    }
    element "External" {
        background #dee2e6
        color #000000
        border dashed
    }
    element "Database" {
        shape Cylinder
    }
    element "Queue" {
        shape Pipe
    }
    relationship "Relationship" {
        color #495057
        thickness 2
    }
}
```

## Warm Earth

Warm earthy tones. Approachable, friendly.

```
styles {
    element "Person" {
        shape Person
        background #6d4c41
        color #ffffff
    }
    element "Software System" {
        background #d84315
        color #ffffff
    }
    element "Container" {
        background #e64a19
        color #ffffff
    }
    element "Component" {
        background #ff8a65
        color #000000
    }
    element "External" {
        background #8d6e63
        color #ffffff
        border dashed
    }
    element "Database" {
        shape Cylinder
    }
    element "Queue" {
        shape Pipe
    }
    relationship "Relationship" {
        color #a1887f
        thickness 2
    }
}
```

## Deep Purple

Rich purple palette. Elegant, creative.

```
styles {
    element "Person" {
        shape Person
        background #4a148c
        color #ffffff
    }
    element "Software System" {
        background #6a1b9a
        color #ffffff
    }
    element "Container" {
        background #8e24aa
        color #ffffff
    }
    element "Component" {
        background #ce93d8
        color #000000
    }
    element "External" {
        background #757575
        color #ffffff
        border dashed
    }
    element "Database" {
        shape Cylinder
    }
    element "Queue" {
        shape Pipe
    }
    relationship "Relationship" {
        color #ab47bc
        thickness 2
    }
}
```

## Ocean Blue

Cool blue tones. Clean, corporate.

```
styles {
    element "Person" {
        shape Person
        background #01579b
        color #ffffff
    }
    element "Software System" {
        background #0277bd
        color #ffffff
    }
    element "Container" {
        background #0288d1
        color #ffffff
    }
    element "Component" {
        background #4fc3f7
        color #000000
    }
    element "External" {
        background #78909c
        color #ffffff
        border dashed
    }
    element "Database" {
        shape Cylinder
    }
    element "Queue" {
        shape Pipe
    }
    relationship "Relationship" {
        color #29b6f6
        thickness 2
    }
}
```

## Custom Theme Tips

When users request custom colors:

1. Pick a **primary color** for Software System (the most prominent element)
2. Derive lighter/darker shades for Container and Component
3. Person should be the **darkest shade** for visual anchor
4. External systems use a **neutral gray** with dashed border
5. Relationships use a **muted version** of the primary color
6. Ensure **contrast**: light text (`#ffffff`) on dark backgrounds, dark text (`#000000`) on light backgrounds
