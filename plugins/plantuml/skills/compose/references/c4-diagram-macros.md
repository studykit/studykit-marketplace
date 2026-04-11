# C4-PlantUML Full Macro Reference

> Source: https://github.com/plantuml-stdlib/C4-PlantUML

## Include Files Hierarchy

Each file includes the previous level:

| File | Level | Adds |
|------|-------|------|
| `C4_Context.puml` | 1 - Context | Person, System, Boundary |
| `C4_Container.puml` | 2 - Container | Container, ContainerDb, ContainerQueue |
| `C4_Component.puml` | 3 - Component | Component, ComponentDb, ComponentQueue |
| `C4_Dynamic.puml` | Dynamic | Index macros (based on Component) |
| `C4_Deployment.puml` | Deployment | Deployment_Node, Node (based on Container) |
| `C4_Sequence.puml` | Sequence | Boundary_End, sequence support (based on Component) |

## Context Level Macros

### Person Macros

```
Person(alias, label, ?descr, ?sprite, ?tags, ?link, ?type)
Person_Ext(alias, label, ?descr, ?sprite, ?tags, ?link, ?type)
```

- `$type` uses same notation as `$techn`, displayed as `[characteristic A]`

### System Macros

```
System(alias, label, ?descr, ?sprite, ?tags, ?link, ?type, ?baseShape)
SystemDb(alias, label, ?descr, ?sprite, ?tags, ?link, ?type)
SystemQueue(alias, label, ?descr, ?sprite, ?tags, ?link, ?type)
System_Ext(alias, label, ?descr, ?sprite, ?tags, ?link, ?type, ?baseShape)
SystemDb_Ext(alias, label, ?descr, ?sprite, ?tags, ?link, ?type)
SystemQueue_Ext(alias, label, ?descr, ?sprite, ?tags, ?link, ?type)
```

### Boundary Macros

```
Boundary(alias, label, ?type, ?tags, ?link, ?descr)
Enterprise_Boundary(alias, label, ?tags, ?link, ?descr)
System_Boundary(alias, label, ?tags, ?link, ?descr)
```

### Built-in Sprites

- `person`, `person2` — human figure sprites
- `robot`, `robot2` — robot figure sprites

## Container Level Macros

```
Container(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link, ?baseShape)
ContainerDb(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link)
ContainerQueue(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link)
Container_Ext(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link, ?baseShape)
ContainerDb_Ext(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link)
ContainerQueue_Ext(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link)
Container_Boundary(alias, label, ?tags, ?link, ?descr)
```

## Component Level Macros

```
Component(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link, ?baseShape)
ComponentDb(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link)
ComponentQueue(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link)
Component_Ext(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link, ?baseShape)
ComponentDb_Ext(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link)
ComponentQueue_Ext(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link)
```

## Dynamic Diagram Macros

Based on Component macros with added index support:

```
Index($offset=1)       ' Returns current index, calculates next (function)
SetIndex($new_index)   ' Returns new index, calculates next (function)
LastIndex()            ' Returns last used index (function)
increment($offset=1)   ' Increase index (procedure, no output)
setIndex($new_index)   ' Set index (procedure, no output)
```

All relationship macros are extended with `?index` parameter:

```
Rel($from, $to, $label, ..., $index=Index())
```

## Deployment Diagram Macros

```
Deployment_Node(alias, label, ?type, ?descr, ?sprite, ?tags, ?link)
Node(alias, label, ?type, ?descr, ?sprite, ?tags, ?link)
Node_L(alias, label, ?type, ?descr, ?sprite, ?tags, ?link)
Node_R(alias, label, ?type, ?descr, ?sprite, ?tags, ?link)
```

## Sequence Diagram Macros

All element macros (Person, System, Container, Component) can be reused as participants.

**Important differences:**
- Element descriptions are not displayed by default (activate with `SHOW_ELEMENT_DESCRIPTIONS()`)
- Boundaries must be defined **without `{` and `}`** — use `Boundary_End()` instead

```
Boundary_End()
SHOW_ELEMENT_DESCRIPTIONS(?show)
SHOW_FOOT_BOXES(?show)
SHOW_INDEX(?show)
```

Only the extended `Rel()` macro is supported:

```
Rel($from, $to, $label, $techn="", $descr="", $sprite="", $tags="", $link="", $index="", $rel="")
```

- `$rel` allows PlantUML-specific arrow types (e.g., `-->`, `-[#red]->`)

## Relationship Macros

### Standard

```
Rel(from, to, label, ?techn, ?descr, ?sprite, ?tags, ?link)
BiRel(from, to, label, ?techn, ?descr, ?sprite, ?tags, ?link)
```

### Directional

```
Rel_U(from, to, label, ...) / Rel_Up(...)
Rel_D(from, to, label, ...) / Rel_Down(...)
Rel_L(from, to, label, ...) / Rel_Left(...)
Rel_R(from, to, label, ...) / Rel_Right(...)

BiRel_U(...) / BiRel_D(...) / BiRel_L(...) / BiRel_R(...)
Rel_Back(from, to, label, ...)
Rel_Neighbor(from, to, label, ...)
```

## Layout Macros

### Element Layout (without relationships)

```
Lay_U(from, to) / Lay_Up(from, to)
Lay_D(from, to) / Lay_Down(from, to)
Lay_L(from, to) / Lay_Left(from, to)
Lay_R(from, to) / Lay_Right(from, to)
Lay_Distance(from, to, ?distance)
```

### Global Layout

```
LAYOUT_TOP_DOWN()
LAYOUT_LEFT_RIGHT()
LAYOUT_LANDSCAPE()
LAYOUT_AS_SKETCH()
SET_SKETCH_STYLE(?bgColor, ?fontColor, ?warningColor, ?fontName, ?footerWarning, ?footerText)
HIDE_STEREOTYPE()
```

### Legend

```
LAYOUT_WITH_LEGEND()
SHOW_LEGEND(?hideStereotype, ?details)
SHOW_FLOATING_LEGEND(?alias, ?hideStereotype, ?details)
LEGEND()   ' Returns alias of floating legend for use with Lay_Distance
UpdateLegendTitle(newTitle)
```

### Person Display

```
HIDE_PERSON_SPRITE()
SHOW_PERSON_SPRITE(?sprite)
SHOW_PERSON_PORTRAIT()
SHOW_PERSON_OUTLINE()    ' Requires PlantUML >= 1.2021.4
```

## Custom Tags/Stereotypes

### Element Tags

```
AddElementTag(tagStereo, ?bgColor, ?fontColor, ?borderColor, ?shadowing, ?shape, ?sprite, ?techn, ?legendText, ?legendSprite, ?borderStyle, ?borderThickness)
```

Element-specific shortcuts (use element-specific default colors):

```
AddPersonTag(tagStereo, ?bgColor, ?fontColor, ?borderColor, ?shadowing, ?shape, ?sprite, ?legendText, ?legendSprite, ?type, ?borderStyle, ?borderThickness)
AddExternalPersonTag(...)
AddSystemTag(...)
AddExternalSystemTag(...)
AddContainerTag(...)
AddExternalContainerTag(...)
AddComponentTag(...)
AddExternalComponentTag(...)
AddNodeTag(...)
```

### Relationship Tags

```
AddRelTag(tagStereo, ?textColor, ?lineColor, ?lineStyle, ?sprite, ?techn, ?legendText, ?legendSprite, ?lineThickness)
```

### Boundary Tags

```
AddBoundaryTag(tagStereo, ?bgColor, ?fontColor, ?borderColor, ?shadowing, ?shape, ?type, ?legendText, ?borderStyle, ?borderThickness, ?sprite, ?legendSprite)
```

### Update Default Styles

```
UpdateElementStyle(elementName, ?bgColor, ?fontColor, ?borderColor, ?shadowing, ?shape, ?sprite, ?techn, ?legendText, ?legendSprite, ?borderStyle, ?borderThickness)
UpdateRelStyle(textColor, lineColor)
UpdateBoundaryStyle(?elementName, ?bgColor, ?fontColor, ?borderColor, ?shadowing, ?shape, ?type, ?legendText, ?borderStyle, ?borderThickness, ?sprite, ?legendSprite)
UpdateContainerBoundaryStyle(...)
UpdateSystemBoundaryStyle(...)
UpdateEnterpriseBoundaryStyle(...)
```

### Applying Tags

Attach tags via `$tags` keyword argument. Combine multiple tags with `+`:

```plantuml
Container(api, "API", "Java", $tags="v1.0+critical")
Rel(a, b, "Calls", $tags="async")
Boundary(b1, "Cloud", $tags="cloud")
```

### Shape and Line Helpers

```
RoundedBoxShape()    ' Rounded box shape
EightSidedShape()    ' Octagonal shape
SharpCornerShape()   ' Default sharp corners

DashedLine()         ' Dashed line style
DottedLine()         ' Dotted line style
BoldLine()           ' Bold line style
SolidLine()          ' Solid line style (reset dashed)
```

### Tag Rules

- `SHOW_LEGEND()` must be the last line (required to display custom tags; `LAYOUT_WITH_LEGEND()` does not show custom tags)
- No spaces between `$tags` and `=`
- No commas `,` in tag names
- If two tags define the same skinparam, the first definition wins
- Boundary tags use a separate namespace (suffix `_boundary` internally), allowing same tag name for elements and boundaries

## Element and Relationship Properties

Attach tabular properties to elements:

```
SetPropertyHeader(col1Name, ?col2Name, ?col3Name, ?col4Name)  ' Up to 4 columns, default: "Name", "Description"
WithoutPropertyHeader()                                         ' No header, second column bold
AddProperty(col1, ?col2, ?col3, ?col4)                         ' Add property row to next element
```

Example:

```plantuml
SetPropertyHeader("Property", "Value", "Description")
AddProperty("SLA", "99.9%", "Monthly uptime target")
AddProperty("RPS", "10,000", "Peak requests per second")
Container(api, "API Gateway", "Kong", "Routes and rate-limits API traffic")
```

Properties are also supported on relationships (since v2.5.0).

## Sprites and Images

### Built-in

`person`, `person2`, `robot`, `robot2`

### External Sprite Libraries

```plantuml
!define DEVICONS https://raw.githubusercontent.com/tupadr3/plantuml-icon-font-sprites/master/devicons
!define FONTAWESOME https://raw.githubusercontent.com/tupadr3/plantuml-icon-font-sprites/master/font-awesome-5
!include DEVICONS/angular.puml
!include FONTAWESOME/users.puml

Person(user, "Customer", $sprite="users")
Container(spa, "SPA", "angular", $sprite="angular")
```

### Sprite Options

- Standard: `$sprite="spriteName"`
- Scaled: `$sprite="spriteName,scale=0.5"`
- Colored: `$sprite="spriteName,scale=0.5,color=red"`
- Image: `$sprite="img:{url or file}"`
- OpenIconic: `$sprite="&envelope-closed"`

### Links

All elements and relationships support `$link` parameter for clickable SVG output:

```plantuml
Person(user, "User", $link="https://example.com/user-docs")
Rel(user, api, "Uses", $link="https://example.com/api-docs")
```

## Custom Color Schema Example

Define reusable color schemas in a separate file:

```plantuml
!$COLOR_PRIMARY = "#1168bd"
!$COLOR_SECONDARY = "#438dd5"
!$COLOR_NEUTRAL = "#f5f5f5"

UpdateElementStyle("person", $bgColor=$COLOR_PRIMARY, $fontColor=$COLOR_NEUTRAL)
UpdateElementStyle("system", $bgColor=$COLOR_SECONDARY, $fontColor=$COLOR_NEUTRAL)
UpdateRelStyle($lineColor="#707070", $textColor="#707070")
```

## Version Information

```
C4Version()              ' Current C4-PlantUML version string
C4VersionDetails()       ' Floating version details table (alias: C4VersionDetailsArea)
```

## Themes

C4-PlantUML supports themes for visual styles and language localization.

### Style Themes

Theme must come **BEFORE** `!include` statements:

```plantuml
!theme C4_united from <C4/themes>
!include <C4/C4_Container>
```

Available style themes:
- **Basic:** `C4_blue` (default), `C4_brown`, `C4_green`, `C4_violet`
- **Modern wireframe:** `C4_blue_new`, `C4_brown_new`, `C4_green_new`, `C4_violet_new`
- **Additional:** `C4_sandstone`, `C4_superhero`, `C4_united`

**Style flags** (set BEFORE includes):
- `!ROUNDED_STYLE=1` — rounded rectangles without color changes
- `!NEW_C4_STYLE=1` — modernized wireframe style

### Language Themes

Translate legend labels to other languages:

```plantuml
!theme C4Language_korean from <C4/themes>
!include <C4/C4_Container>
```

Available: `C4Language_english` (default), `C4Language_chinese`, `C4Language_danish`, `C4Language_dutch`, `C4Language_german`, `C4Language_italian`, `C4Language_japanese`, `C4Language_korean`, `C4Language_portuguese`, `C4Language_russian`, `C4Language_spanish`, `C4Language_ukrainian`

### Extended PlantUML Shapes via baseShape

Enable with `!ENABLE_ALL_PLANT_ELEMENTS = 1` before includes. Adds `$baseShape="..."` support on System, Container, Component (and _Ext variants).

Supported shapes: `actor`, `agent`, `artifact`, `boundary`, `card`, `circle`, `cloud`, `collections`, `control`, `entity`, `file`, `folder`, `frame`, `hexagon`, `interface`, `label`, `package`, `stack`, `storage`, `usecase`

## Compatibility

- `!NO_LAY_ROTATE=1` — compatibility mode for diagrams using `LAYOUT_LANDSCAPE()` with `Lay_*()` calls (bugfix in PlantUML v2.12.0 may change old layouts)
