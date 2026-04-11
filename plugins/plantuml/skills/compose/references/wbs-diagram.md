> Source: https://plantuml.com/wbs-diagram

# PlantUML WBS Diagram Reference

## OrgMode Syntax

WBS diagrams use `@startwbs` and `@endwbs`. The primary syntax uses asterisks (`*`) where each level of depth adds another `*`.

```plantuml
@startwbs
* Business Process Modelling WBS
** Launch the project
*** Complete Stakeholder Research
*** Initial Implementation Plan
** Design phase
*** Model of AsIs Processes Completed
**** Model of AsIs Processes Completed1
**** Model of AsIs Processes Completed2
*** Measure AsIs performance metrics
*** Identify Quick Wins
** Complete innovate phase
@endwbs
```

## Change Direction

By default, child nodes alternate left and right. Use `<` after the asterisks to force a node to the left side, or `>` to force it to the right side.

```plantuml
@startwbs
* Business Process Modelling WBS
** Launch the project
*** Complete Stakeholder Research
*** Initial Implementation Plan
** Design phase
***< Model of AsIs Processes Completed1
***> Model of AsIs Processes Completed2
*** Measure AsIs performance metrics
*** Identify Quick Wins
@endwbs
```

## Arithmetic Notation

An alternative syntax uses `+` for right-side nodes and `-` for left-side nodes. Each additional `+` or `-` increases the depth level.

```plantuml
@startwbs
+ New Job
++ Decide on Job Requirements
+++ Identity gaps
+++ Skills
++++ Java
++++ &lt;back:LightSkyBlue>SQL
++- Checklist
+++- Responsibilities
+++- Location
++ CV Upload Done
+++ CV Updated
++++ Spelling & Grammar
++++ Check CV on phone
+++ Response
++++ LinkedIn
++++ Monster
@endwbs
```

## Multiline Nodes

Use `:` to start multiline content and `;` to end it. This allows longer text within a single box.

```plantuml
@startwbs
* <&flag> Debian
** &lt;back:LightSkyBlue>Ubuntu
***:Linux Mint
Open Source
Project;
*** Kubuntu
*** Lubuntu
*** KDE Neon
** LMDE
** SolydXK
** SteamOS
** Raspbian
@endwbs
```

## Removing Boxes

Append `_` after the asterisks (OrgMode) or `+`/`-` (arithmetic) to remove the box around a node, rendering it as plain text.

**Selective boxless nodes (OrgMode):**

```plantuml
@startwbs
* World
** America
***_ Canada
***_ Mexico
***_ Brazil
** Europe
***_ England
***_ Germany
***_ Spain
@endwbs
```

**All boxless nodes:**

```plantuml
@startwbs
*_ World
**_ America
***_ Canada
***_ Mexico
***_ Brazil
**_ Europe
***_ England
***_ Germany
***_ Spain
@endwbs
```

**Selective boxless nodes (arithmetic notation):**

```plantuml
@startwbs
+ Project
++ Part One
+++ Task 1.1
---_ LeftTask 1.2
+++_ Task 1.3
-- Part Two
+++_ Task 2.1
+++ Task 2.2
@endwbs
```

## Colors with Inline Notation

Apply background colors directly to nodes using `[#Color]` after the asterisks or `+`/`-`.

```plantuml
@startwbs
*[#SkyBlue] this is the partner workance
**[#pink] this is my workpackage
**[#SkyBlue] this is another partner workpackage
***[#pink] this is my workpackage
***[#SkyBlue] this is another partner workpackage
**[#white] this is another partner workpackage
**[#SkyBlue] this is the last partner workpackage
@endwbs
```

## Colors with Style

Use the `<style>` block with stereotypes (`<<stylename>>`) for reusable color definitions.

```plantuml
@startwbs
<style>
wbsDiagram {
  .pink {
    BackgroundColor pink
  }
  .your_style_name {
    BackgroundColor SkyBlue
  }
}
</style>
* this is the partner workpackage <<your_style_name>>
** this is my workpackage <<pink>>
** this is another partner workpackage <<your_style_name>>
*** this is my workpackage <<pink>>
*** this is another partner workpackage <<your_style_name>>
** this is another partner workpackage <<your_style_name>>
** this is the last partner workpackage <<your_style_name>>
@endwbs
```

## Advanced Styling

Use the `<style>` block to control line colors, arrow colors, border styles, round corners, fonts, and depth-specific styles.

```plantuml
@startwbs
<style>
wbsDiagram {
  Linecolor black
  arrow {
    LineColor green
  }
  :depth(0) {
    BackgroundColor White
    RoundCorner 10
    LineColor red
  }
  node {
    :depth(2) {
      LineStyle 2
      LineThickness 2.5
    }
  }
  boxless {
    FontColor darkgreen
  }
}
</style>
* World
** America
***_ Canada
***_ Mexico
***_ Brazil
** Europe
***_ England
***_ Germany
***_ Spain
@endwbs
```

### Available Style Properties

- `BackgroundColor` -- node background color
- `RoundCorner` -- corner radius for rounded boxes
- `LineColor` -- border/connector line color
- `LineStyle` -- dash pattern for lines (e.g., `2` for dashed)
- `LineThickness` -- thickness of lines
- `FontColor` -- text color
- `Padding` -- internal padding within nodes
- `HorizontalAlignment` -- text alignment (`left`, `center`, `right`)
- `MaximumWidth` -- maximum width in pixels before wrapping
- `:depth(N)` -- target nodes at a specific depth level
- `arrow` -- style arrows/connectors
- `boxless` -- style boxless nodes specifically

## Word Wrap

Use `MaximumWidth` within the `<style>` block to control automatic text wrapping. The value is in pixels.

```plantuml
@startwbs
<style>
node {
  Padding 12
  Margin 3
  HorizontalAlignment center
  LineColor blue
  LineThickness 3.0
  BackgroundColor gold
  RoundCorner 40
  MaximumWidth 100
}

arrow {
  LineStyle 4
  LineThickness 0.5
  LineColor green
}
</style>

* Hi =)
** sometimes i have node with a very long text
*** this
*** &lt;b>this
** sometimes &lt;size:14>i have node with a very long text
*** this
*** this
@endwbs
```

## Arrows Between WBS Elements

Connect nodes using arrows by assigning aliases with `as` or parenthetical notation `(alias)`.

**Using `as` keyword:**

```plantuml
@startwbs
* Test
** A topic
*** "common" as c1
*** "common2" as c2
** "Another topic" as t2
t2 -> c1
t2 ..> c2 #blue
@endwbs
```

**Using parenthetical aliases:**

```plantuml
@startwbs
* Test
**(b) A topic
***(c1) common
***(c2) common2
**(t2) Another topic
t2 --> c1
b -> t2 #blue
@endwbs
```

### Arrow Styles

- `->` -- solid arrow
- `-->` -- longer solid arrow
- `..>` -- dotted arrow
- Append `#color` to set arrow color (e.g., `..> c2 #blue`)

## Creole and HTML Formatting

Nodes support Creole markup and inline HTML-like tags for rich text formatting.

```plantuml
@startwbs
* Creole on WBS
**:= Title
This is **bold**
This is //italics//
This is ""monospaced""
This is --stricken-out--
This is __underlined__
This is ~~wave-underlined~~;
**: <b>HTML Creole
<i>italics</i>
<s>stroked</s>
<u>underlined</u>
<plain>plain</plain>
<b>bold</b>;
@endwbs
```

### Supported Creole Markup

- `**bold**` -- bold text
- `//italics//` -- italic text
- `""monospaced""` -- monospaced text
- `--stricken-out--` -- strikethrough text
- `__underlined__` -- underlined text
- `~~wave-underlined~~` -- wavy underlined text
- `= Title` -- heading level within a multiline node

### Supported HTML-like Tags

- `<b>` -- bold
- `<i>` -- italics
- `<s>` -- strikethrough
- `<u>` -- underline
- `<plain>` -- plain text
- `<size:N>` -- font size
- `<back:Color>` -- background color for inline text
