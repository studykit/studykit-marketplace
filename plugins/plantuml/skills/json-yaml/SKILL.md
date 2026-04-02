---
name: json-yaml
disable-model-invocation: true
description: This skill provides PlantUML JSON and YAML data visualization syntax reference. Use when writing, creating, or debugging PlantUML JSON or YAML diagrams. Applies when users mention "JSON diagram", "YAML diagram", "data visualization", "JSON tree", "YAML tree", or need to visualize JSON or YAML data structures as diagrams in PlantUML.
---

> Sources:
> - https://plantuml.com/json
> - https://plantuml.com/yaml

# PlantUML JSON & YAML Visualization Reference

## JSON Visualization

### Basic Syntax

JSON diagrams use `@startjson` and `@endjson` delimiters.

```plantuml
@startjson
{
  "fruit": "Apple",
  "size": "Large",
  "color": "Red"
}
@endjson
```

### Simple Values

You can display a single string, number, boolean, or null as a standalone diagram.

```plantuml
@startjson
"Hello world!"
@endjson
```

```plantuml
@startjson
42
@endjson
```

```plantuml
@startjson
true
@endjson
```

### Complex Nested JSON

Objects and arrays can be nested to any depth.

```plantuml
@startjson
{
  "firstName": "John",
  "lastName": "Smith",
  "isAlive": true,
  "age": 27,
  "address": {
    "streetAddress": "21 2nd Street",
    "city": "New York",
    "state": "NY",
    "postalCode": "10021-3100"
  },
  "phoneNumbers": [
    {
      "type": "home",
      "number": "212 555-1234"
    },
    {
      "type": "office",
      "number": "646 555-4567"
    }
  ],
  "children": [],
  "spouse": null
}
@endjson
```

### Supported Data Types

All JSON data types are supported:

- **Null:** `null`
- **Booleans:** `true`, `false`
- **Numbers:** integers, decimals, exponential notation (e.g., `1e10`)
- **Strings:** Unicode support, escape sequences (`\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`, `\uXXXX`)
- **Arrays:** ordered lists (homogeneous or mixed-type)
- **Objects:** key-value pairs

```plantuml
@startjson
{
  "null": null,
  "true": true,
  "false": false,
  "integer": 42,
  "decimal": 3.14,
  "string": "Hello",
  "array": [1, "two", true, null],
  "object": {"nested": "value"}
}
@endjson
```

### Highlighting Elements

Use `#highlight` to emphasize specific keys or nested paths. Paths are separated by `/`.

```plantuml
@startjson
#highlight "lastName"
#highlight "address" / "city"
#highlight "phoneNumbers" / "0" / "number"
{
  "firstName": "John",
  "lastName": "Smith",
  "isAlive": true,
  "age": 27,
  "address": {
    "streetAddress": "21 2nd Street",
    "city": "New York",
    "state": "NY",
    "postalCode": "10021-3100"
  },
  "phoneNumbers": [
    {
      "type": "home",
      "number": "212 555-1234"
    },
    {
      "type": "office",
      "number": "646 555-4567"
    }
  ],
  "children": [],
  "spouse": null
}
@endjson
```

### Custom Highlight Styles

Define custom style classes and apply them with `<<className>>`.

```plantuml
@startjson
<style>
  .h1 {
    BackGroundColor green
    FontColor white
    FontStyle italic
  }
  .h2 {
    BackGroundColor red
    FontColor white
    FontStyle italic
  }
</style>
#highlight "lastName" <<h1>>
#highlight "address" / "city" <<h2>>
{
  "firstName": "John",
  "lastName": "Smith",
  "address": {
    "streetAddress": "21 2nd Street",
    "city": "New York"
  }
}
@endjson
```

### Default Highlight Style

Customize the default highlight appearance using the `highlight` block inside `jsonDiagram`.

```plantuml
@startjson
<style>
jsonDiagram {
  highlight {
    BackGroundColor yellow
    FontColor red
    FontStyle bold
  }
}
</style>
#highlight "city"
{
  "name": "John",
  "city": "New York"
}
@endjson
```

### Global JSON Diagram Styling

Customize the overall diagram appearance using `<style>` with `jsonDiagram`.

```plantuml
@startjson
<style>
jsonDiagram {
  node {
    BackGroundColor Khaki
    LineColor lightblue
    FontName Helvetica
    FontColor red
    FontSize 18
    FontStyle bold
    RoundCorner 0
    LineThickness 2
    LineStyle 10-5
    separator {
      LineThickness 0.5
      LineColor black
      LineStyle 1-5
    }
  }
  arrow {
    BackGroundColor lightblue
    LineColor green
    LineThickness 2
    LineStyle 2-5
  }
}
</style>
{
  "fruit": "Apple",
  "size": "Large",
  "color": ["Red", "Green"]
}
@endjson
```

### Text Formatting (Creole and HTML)

JSON values support rich text formatting with Creole syntax and HTML-like tags.

```plantuml
@startjson
{
  "bold": "**bold text**",
  "italic": "//italic text//",
  "underlined": "__underlined text__",
  "strikethrough": "--stricken text--",
  "monospaced": "\"\"monospaced text\"\"",
  "colored": "<color:blue>blue text</color>",
  "sized": "<size:20>big text</size>",
  "background": "<back:yellow>highlighted</back>",
  "emoji": "<:heart:> love",
  "unicode": "<U+221E> infinity"
}
@endjson
```

### JSON Entities in Other Diagrams

JSON data can be embedded within class, object, component, deployment, use case, and state diagrams using the `json` keyword.

**In class/object diagrams:**

```plantuml
@startuml
json "Config" as cfg {
  "host": "localhost",
  "port": 8080,
  "debug": true
}

class Application {
  +start()
  +stop()
}

Application --> cfg : uses
@enduml
```

**In deployment/component diagrams:**

```plantuml
@startuml
allowmixing

json config {
  "database": {
    "host": "db.example.com",
    "port": 5432
  },
  "cache": {
    "host": "cache.example.com",
    "port": 6379
  }
}

component Server
Server --> config
@enduml
```

### Minimum and Maximum Array Size

Use `!$minArraySize` and `!$maxArraySize` to control how arrays render.

```plantuml
@startjson
{
  "items": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
}
@endjson
```

## YAML Visualization

### Basic Syntax

YAML diagrams use `@startyaml` and `@endyaml` delimiters.

```plantuml
@startyaml
fruit: Apple
size: Large
color: Red
@endyaml
```

### Complex Nested YAML

YAML supports deeply nested structures with objects, arrays, and mixed content.

```plantuml
@startyaml
doe: "a deer, a female deer"
ray: "a drop of golden sun"
pi: 3.14159
xmas: true
french-hens: 3
calling-birds:
  - huey
  - dewey
  - louie
  - fred
xmas-fifth-day:
  calling-birds: four
  french-hens: 3
  golden-rings: 5
  partridges:
    count: 1
    location: "a pear tree"
  turtle-doves: two
@endyaml
```

### Special Characters in Keys

YAML keys can include symbols and Unicode characters.

```plantuml
@startyaml
@fruit: Apple
$size: Large
&color: Red
❤: Heart
‰: Per mille
@endyaml
```

### Highlighting Elements

Use `#highlight` to emphasize specific keys or nested paths. Paths are separated by `/`.

```plantuml
@startyaml
#highlight "french-hens"
#highlight "xmas-fifth-day" / "partridges"
doe: "a deer, a female deer"
ray: "a drop of golden sun"
pi: 3.14159
xmas: true
french-hens: 3
calling-birds:
  - huey
  - dewey
  - louie
  - fred
xmas-fifth-day:
  calling-birds: four
  french-hens: 3
  golden-rings: 5
  partridges:
    count: 1
    location: "a pear tree"
  turtle-doves: two
@endyaml
```

### Custom Highlight Styles

Define custom style classes and apply them with `<<className>>`.

```plantuml
@startyaml
<style>
  .h1 {
    BackGroundColor green
    FontColor white
    FontStyle italic
  }
  .h2 {
    BackGroundColor red
    FontColor white
    FontStyle italic
  }
</style>
#highlight "french-hens" <<h1>>
#highlight "xmas-fifth-day" / "partridges" <<h2>>
doe: "a deer, a female deer"
ray: "a drop of golden sun"
french-hens: 3
xmas-fifth-day:
  calling-birds: four
  french-hens: 3
  golden-rings: 5
  partridges:
    count: 1
    location: "a pear tree"
  turtle-doves: two
@endyaml
```

### Default Highlight Style

Customize the default highlight appearance using the `highlight` block inside `yamlDiagram`.

```plantuml
@startyaml
<style>
yamlDiagram {
  highlight {
    BackGroundColor red
    FontColor white
    FontStyle italic
  }
}
</style>
#highlight "fruit"
fruit: Apple
size: Large
color: Red
@endyaml
```

### Global YAML Diagram Styling

Customize the overall diagram appearance using `<style>` with `yamlDiagram`.

```plantuml
@startyaml
<style>
yamlDiagram {
  node {
    BackGroundColor lightblue
    LineColor lightblue
    FontName Helvetica
    FontColor red
    FontSize 18
    FontStyle bold
    RoundCorner 0
    LineThickness 2
    LineStyle 10-5
    separator {
      LineThickness 0.5
      LineColor black
      LineStyle 1-5
    }
  }
  arrow {
    BackGroundColor lightblue
    LineColor green
    LineThickness 2
    LineStyle 2-5
  }
}
</style>
fruit: Apple
size: Large
color:
  - Red
  - Green
@endyaml
```

### Text Formatting (Creole and HTML)

YAML values support rich text formatting with Creole syntax and HTML-like tags.

```plantuml
@startyaml
bold: "**bold text**"
italic: "//italic text//"
monospaced: "\"\"monospaced text\"\""
strikethrough: "--stricken-out--"
underlined: "__underlined text__"
wave: "~~wave text~~"
@endyaml
```

HTML Creole tags supported in YAML values:

- `<b>bold</b>`
- `<i>italic</i>`
- `<font:monospaced>mono</font>`
- `<s>strikethrough</s>`
- `<u>underlined</u>`
- `<w>wave</w>`
- `<color:blue>colored text</color>`
- `<back:yellow>background</back>`
- `<size:20>sized text</size>`
- `<&icon>` (OpenIconic icons)
- `<U+XXXX>` (Unicode characters)
- `<:emoji:>` (emoji)
- `<img:url>` (inline images)

### YAML Entities in Other Diagrams

YAML data can be embedded within other diagram types using the `yaml` keyword, similar to JSON entities.

```plantuml
@startuml
allowmixing

yaml config {
  database:
    host: db.example.com
    port: 5432
  cache:
    host: cache.example.com
    port: 6379
}

component Server
Server --> config
@enduml
```

## Style Properties Reference

The following style properties are available for both `jsonDiagram` and `yamlDiagram`:

### Node Properties

| Property | Description | Example |
|---|---|---|
| `BackGroundColor` | Node background color | `BackGroundColor Khaki` |
| `LineColor` | Node border color | `LineColor lightblue` |
| `FontName` | Font family | `FontName Helvetica` |
| `FontColor` | Text color | `FontColor red` |
| `FontSize` | Text size | `FontSize 18` |
| `FontStyle` | Text style | `FontStyle bold` |
| `RoundCorner` | Corner rounding radius | `RoundCorner 0` |
| `LineThickness` | Border thickness | `LineThickness 2` |
| `LineStyle` | Dash pattern | `LineStyle 10-5` |

### Separator Properties (inside `node`)

| Property | Description | Example |
|---|---|---|
| `LineThickness` | Separator line thickness | `LineThickness 0.5` |
| `LineColor` | Separator line color | `LineColor black` |
| `LineStyle` | Separator dash pattern | `LineStyle 1-5` |

### Arrow Properties

| Property | Description | Example |
|---|---|---|
| `BackGroundColor` | Arrow head fill color | `BackGroundColor lightblue` |
| `LineColor` | Arrow line color | `LineColor green` |
| `LineThickness` | Arrow line thickness | `LineThickness 2` |
| `LineStyle` | Arrow dash pattern | `LineStyle 2-5` |

### Highlight Properties

| Property | Description | Example |
|---|---|---|
| `BackGroundColor` | Highlight background color | `BackGroundColor yellow` |
| `FontColor` | Highlighted text color | `FontColor white` |
| `FontStyle` | Highlighted text style | `FontStyle italic` |

## Validation

After writing a `.puml` file or a PlantUML fenced block in Markdown, always validate the syntax:

- **Local** (preferred): `bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh <file.puml>`
- **Online** (fallback): `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/validate_online.py <file.puml>`

For PlantUML blocks embedded in Markdown, extract the content to a temporary `.puml` file before validating. If validation fails, read the error output, fix the syntax, and re-validate.
