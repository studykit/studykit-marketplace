---
name: d2:draw
description: >
  Create D2 diagrams for software architecture, network topology, flow charts, ERD, sequence
  diagrams, and general-purpose diagramming. Use when the user says "create a D2 diagram",
  "draw an architecture diagram", "generate a D2 file", "make a sequence diagram", "create
  an ERD", "draw a flowchart", "make a grid diagram", or explicitly invokes /d2:draw. Also
  trigger when the user mentions "D2 language", "d2lang", wants text-based diagrams, or asks
  for diagrams with SQL tables, class diagrams, or sequence diagrams — even if they don't
  say "D2" explicitly. If the user asks for a diagram and doesn't specify a tool, consider
  D2 as a strong default for general-purpose diagramming.
argument-hint: <diagram description or system to visualize>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch
---

# Create D2 Diagram

Create a D2 diagram based on `$ARGUMENTS`.

## Output

Write a `.d2` file containing a valid D2 diagram definition.

## Workflow

1. **Identify diagram type** from the user's description (general, sequence, sql_table, class, grid, or mixed)
2. **Pick theme** — if the user specified a theme or color preference, map it to a theme ID. Otherwise use theme 3 (Flagship Terrastruct) as the default for clean, professional output.
3. **Consult reference** — read `references/d2-language.md` for core syntax. For special diagram types (sql_table, sequence, grid, class), read `references/special-diagrams.md`. For theme/style details, read `references/themes.md`.
4. **If local references are insufficient** — fetch the official docs. See [Official Documentation](#official-documentation) below.
5. **Draft the diagram** using proper D2 syntax
6. **Write output** as a `.d2` file
7. **Review** — verify the D2 syntax is correct
8. **Preview** — render the diagram with the chosen theme so the user can see it immediately

## Preview

After writing the `.d2` file, always render it so the user can see the diagram without extra steps:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/preview.sh <output.d2> [theme-id] [layout-engine]
```

- **theme-id**: Default is `3` (Flagship Terrastruct) — clean, professional output. See themes section for all IDs.
- **layout-engine**: `dagre` (default) or `elk`. See layout engine section for when to use each.

Prerequisites: `brew install d2`

For sketch (hand-drawn) style, render directly:

```bash
d2 --sketch --theme 3 <output.d2> <output.png>
```

To export as other formats:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/export.sh <output.d2> svg [theme-id] [layout]   # SVG image
bash ${CLAUDE_PLUGIN_ROOT}/scripts/export.sh <output.d2> pdf [theme-id] [layout]   # PDF document
bash ${CLAUDE_PLUGIN_ROOT}/scripts/export.sh <output.d2> pptx [theme-id] [layout]  # PowerPoint
```

## D2 File Structure

D2 files are declarative — you define shapes, connections, and styles:

```d2
# Shapes
server: Web Server
db: Database {
  shape: cylinder
}

# Connections
server -> db: queries

# Containers (nesting)
cloud: AWS {
  server: Web Server
  db: Database {
    shape: cylinder
  }
  server -> db
}

# Styles
server.style: {
  fill: "#1168bd"
  stroke: "#0b4884"
  font-color: "#ffffff"
  border-radius: 8
}
```

## Key Rules

- **Shapes** are declared by key name: `my_shape` or `my_shape: "Label"`
- **Connections** use `--`, `->`, `<-`, or `<->`: `a -> b: "label"`
- **Containers** use nesting with `{}`: `parent: { child1; child2 }`
- **Shape types** set via `shape` property: `rectangle` (default), `oval`, `circle`, `diamond`, `hexagon`, `cylinder`, `queue`, `package`, `step`, `page`, `document`, `person`, `cloud`, `callout`, `stored_data`, `parallelogram`, `square`, `c4-person`
- **Person shapes** — the built-in `person` shape is minimalistic. For better-looking people, prefer using an icon with `shape: image`:
  ```d2
  user: User {
    shape: image
    icon: https://icons.terrastruct.com/essentials%2F359-users.svg
  }
  ```
  Browse icons at https://icons.terrastruct.com for alternatives (tech, people, infra, etc.)
- **Icons** via URL: `shape.icon: https://icons.terrastruct.com/essentials%2F226-alarm.svg`
- **Standalone images**: `logo: { shape: image; icon: ./logo.png }`
- **Semicolons** separate multiple declarations on one line: `a; b; c`
- **Comments** use `#` for single-line
- **Labels** can include Markdown for standalone text blocks
- **Globs** enable bulk styling: `*.style.fill: red` applies to all top-level shapes

## Layout Direction

D2 supports layout direction via the `direction` keyword:

```d2
direction: right   # left-to-right flow
direction: down    # top-to-bottom (default)
direction: left    # right-to-left
direction: up      # bottom-to-top
```

When the user specifies a layout preference:
- "horizontal", "left to right", "가로" -> use `direction: right`
- "vertical", "top to bottom", "세로" -> use `direction: down` (default)

## Layout Engine

D2 supports multiple layout engines, each with different strengths. Set via CLI flag or environment variable.

| Engine | Flag | Description |
|--------|------|-------------|
| dagre | `--layout dagre` | Default. Fast, hierarchical/layered layout (Graphviz DOT-based) |
| elk | `--layout elk` | More mature, better for complex diagrams. Supports width/height on containers |

The preview script uses the default engine (dagre). To use a different engine, render directly:

```bash
d2 --layout elk --theme 3 <output.d2> <output.png>
```

### Interpreting User Requests

- "dagre", "기본 레이아웃", "default layout" -> dagre (default)
- "elk", "복잡한 레이아웃", "complex layout" -> elk
- "hierarchical", "계층형" -> dagre (designed for hierarchical layouts)
- "compact", "밀집" -> elk (generally produces more compact output)

## Styling

Apply styles using the `style` property on any shape or connection:

```d2
server: Web Server {
  style: {
    fill: "#1168bd"
    stroke: "#0b4884"
    font-color: "#ffffff"
    border-radius: 8
    shadow: true
  }
}

server -> db: {
  style: {
    stroke: "#707070"
    stroke-width: 2
    animated: true
  }
}
```

Available style properties: `fill`, `stroke`, `stroke-width`, `stroke-dash`, `font-color`, `font-size`, `bold`, `italic`, `underline`, `opacity`, `border-radius`, `shadow`, `3d`, `multiple`, `double-border`, `animated`, `fill-pattern`, `text-transform`

## Themes

D2 has built-in themes applied via the CLI `--theme` flag. The preview script accepts an optional theme parameter.

Read `references/themes.md` for the full list of themes and how to apply them.

### Interpreting User Requests

- "dark theme", "다크 테마", "dark mode" -> theme 200 (Dark Mauve)
- "터미널", "terminal", "monospace" -> theme 300 (Terminal)
- "기본", "default", "neutral" -> theme 0 (Neutral Default)
- "보라색", "purple", "grape" -> theme 6 (Grape Soda)
- "녹색", "green" -> theme 104 (Everglade Green)
- "따뜻한", "warm", "earth" -> theme 103 (Earth Tones)
- "colorblind", "접근성" -> theme 8 (Colorblind Clear)
- Custom color requests -> use inline `style` properties to match the user's description

## Quick Reference by Diagram Type

| Type | Key Syntax |
|------|-----------|
| General / Flowchart | Shapes + connections with `->` |
| Sequence Diagram | `shape: sequence_diagram` on container |
| SQL Table / ERD | `shape: sql_table` with column definitions |
| UML Class | `shape: class` with fields and methods |
| Grid Layout | `grid-rows` / `grid-columns` on container |

For detailed syntax of each special diagram type, read `references/special-diagrams.md`.

## Official Documentation

When local `references/` files don't cover what you need, fetch from the official D2 docs:

| Topic | URL |
|-------|-----|
| Language Tour | https://d2lang.com/tour/intro/ |
| Shapes | https://d2lang.com/tour/shapes |
| Connections | https://d2lang.com/tour/connections |
| Containers | https://d2lang.com/tour/containers |
| Style | https://d2lang.com/tour/style |
| Icons | https://d2lang.com/tour/icons |
| SQL Tables | https://d2lang.com/tour/sql-tables |
| Sequence Diagrams | https://d2lang.com/tour/sequence-diagrams |
| Grid Diagrams | https://d2lang.com/tour/grid-diagrams |
| Classes | https://d2lang.com/tour/classes |
| Globs | https://d2lang.com/tour/globs |
| Themes | https://d2lang.com/tour/themes |
| Layouts | https://d2lang.com/tour/layouts |
| Text & Markdown | https://d2lang.com/tour/text |
| Imports | https://d2lang.com/tour/imports |
| CLI Manual | https://d2lang.com/tour/man/ |

Use `WebFetch` to retrieve the page content when you need syntax details or features not covered in local references.
