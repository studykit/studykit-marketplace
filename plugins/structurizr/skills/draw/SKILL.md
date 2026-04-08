---
name: structurizr:draw
description: >
  Create Structurizr DSL diagrams for C4 model architecture visualization. Use when the user
  says "create a C4 diagram", "draw an architecture diagram with Structurizr", "generate
  Structurizr DSL", "make a system context / container / component / deployment diagram",
  "create a workspace DSL", or explicitly invokes /structurizr:draw. Also trigger when the
  user mentions "C4 model", "software architecture diagram", or wants to visualize system
  architecture using text-based DSL, even if they don't say "Structurizr" explicitly.
argument-hint: <diagram description or system architecture to visualize>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch
---

# Create Structurizr DSL Diagram

Create a Structurizr DSL diagram based on `$ARGUMENTS`.

## Output

Write a `.dsl` file containing a valid Structurizr workspace definition.

## Workflow

1. **Identify view types** from the user's description (system landscape, system context, container, component, deployment, dynamic)
2. **Consult reference** — read the matching view skill's SKILL.md for correct syntax patterns. For full language details, read `references/dsl-language.md`. For cookbook examples, read `references/cookbook.md`.
3. **If local references are insufficient** — fetch the official docs. See [Official Documentation](#official-documentation) below.
4. **Draft the workspace** using proper Structurizr DSL syntax
5. **Write output** as a `.dsl` file
6. **Review** — verify the DSL structure is syntactically correct
7. **Preview** — render the diagram so the user can see it immediately

## Preview

After writing the `.dsl` file, always render it so the user can see the diagram without extra steps:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/preview.sh <output.dsl>
```

This uses `structurizr` to export to PlantUML, then `plantuml` to render PNG images.

Prerequisites: `brew install structurizr plantuml`

To export as other formats:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/export.sh <output.dsl> svg      # SVG images
bash ${CLAUDE_PLUGIN_ROOT}/scripts/export.sh <output.dsl> plantuml  # PlantUML files
bash ${CLAUDE_PLUGIN_ROOT}/scripts/export.sh <output.dsl> mermaid   # Mermaid files
```

## Workspace Structure

Every Structurizr DSL file follows this structure:

```
workspace [name] [description] {
    model {
        // Elements: person, softwareSystem, container, component
        // Relationships: ->
        // Deployment: deploymentEnvironment, deploymentNode
    }
    views {
        // Diagrams: systemLandscape, systemContext, container, component, deployment, dynamic
        // Styles: styles { element, relationship }
    }
}
```

## Key Rules

- Assign identifiers to elements that need referencing: `identifier = person "Name"`
- Relationships use `->` syntax: `user -> system "Uses"`
- Views reference identifiers defined in the model section
- `include *` adds the default set of elements for each view type
- `autoLayout` enables automatic layout. Default is `tb` (top-bottom). If the user specifies a layout direction, use it. Available directions:
  - `tb` — top to bottom (default, compact width)
  - `bt` — bottom to top
  - `lr` — left to right (good for linear flows)
  - `rl` — right to left
  - When the user says "가로", "horizontal", or "left to right" → use `lr`
  - When the user says "세로", "vertical", or "top to bottom" → use `tb`
- Tags enable custom styling: elements get default tags (`Element`, `Person`, `Software System`, etc.)
- All relationships automatically receive the `Relationship` tag

## Quick Reference by View Type

| View | Scope | DSL |
|------|-------|-----|
| System Landscape | All systems | `systemLandscape { include * }` |
| System Context | One system | `systemContext <system> { include * }` |
| Container | Inside a system | `container <system> { include * }` |
| Component | Inside a container | `component <container> { include * }` |
| Deployment | Infrastructure | `deployment <*\|system> <env> { include * }` |
| Dynamic | Behavior flow | `dynamic <scope> { a -> b "action" }` |

For detailed syntax of each view type, read the corresponding reference skill.

## Styling and Themes

If the user requests a specific color scheme or theme, apply it. If not specified, use the "C4 Blue" theme as default.

Read `references/themes.md` for the full list of predefined themes and how to apply them.

### Interpreting User Requests

- "다크 테마", "dark theme", "dark mode" → use Dark theme
- "파란색", "blue" → use C4 Blue (default)
- "초록색", "green" → use Forest Green theme
- "모노톤", "grayscale", "흑백" → use Monochrome theme
- "따뜻한", "warm" → use Warm Earth theme
- "보라색", "purple" → use Deep Purple theme
- Custom color requests → build a custom palette matching the user's description

### Applying Styles

Apply styles in the `views` block using tags:

```
styles {
    element "Software System" {
        background #1168bd
        color #ffffff
        shape RoundedBox
    }
    relationship "Relationship" {
        color #707070
        thickness 2
    }
}
```

For full styling options (shapes, borders, opacity, etc.), read the `styles` reference skill.

## Official Documentation

When local `references/` files don't cover what you need, fetch from the official Structurizr docs:

| Topic | URL |
|-------|-----|
| DSL Language Reference | https://docs.structurizr.com/dsl/language |
| Cookbook (patterns & recipes) | https://docs.structurizr.com/dsl/cookbook/ |
| Cookbook: specific recipe | https://docs.structurizr.com/dsl/cookbook/{recipe-name}/ |
| Themes | https://docs.structurizr.com/dsl/cookbook/themes/ |
| AWS icons | https://docs.structurizr.com/dsl/cookbook/amazon-web-services/ |
| CLI export | https://docs.structurizr.com/cli/export |

Use `WebFetch` to retrieve the page content when you need syntax details, new cookbook recipes, or features not covered in local references. For example, if the user asks about workspace extension, filtered views, or cloud-specific icons that aren't in the local files, fetch the relevant cookbook page directly.
