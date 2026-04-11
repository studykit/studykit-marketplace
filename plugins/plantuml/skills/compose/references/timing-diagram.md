> Source: https://plantuml.com/timing-diagram

# PlantUML Timing Diagram Reference

## Participant Types

| Type | Description |
|------|-------------|
| `robust` | Complex line signal with multiple named states |
| `concise` | Simplified signal for data movement |
| `rectangle` | Similar to concise but within a rectangle |
| `clock` | Repeating transitions with period, pulse, offset |
| `binary` | Exactly 2 states: `high`/`low` or `0`/`1` |
| `analog` | Continuous signals with linear interpolation |

```plantuml
@startuml
robust "Web Browser" as WB
concise "Web User" as WU

@0
WB is Idle
WU is Idle

@100
WB is Processing
WU is Waiting

@300
WB is Waiting
@enduml
```

## Binary and Clock Signals

```plantuml
@startuml
clock "Clock_0" as C0 with period 50
clock "Clock_1" as C1 with period 50 pulse 15 offset 10
binary "Enable" as EN

@0
EN is low

@5
EN is high

@10
EN is low
@enduml
```

## State Changes Using @ Notation

Use `@<time>` for absolute time, `@+<offset>` for relative time.

```plantuml
@startuml
robust "Web Browser" as WB
concise "Web User" as WU

@0
WU is Idle
WB is Idle

@+100
WU -> WB : URL
WU is Waiting

@+200
WB is Processing

@+100
WB is Waiting
@enduml
```

## Date and Time Format Usage

### Date Format

```plantuml
@startuml
robust "Web Browser" as WB
concise "Web User" as WU

@2019/07/02
WU is Idle
WB is Idle

@2019/07/04
WU is Waiting : some note

@2019/07/05
WB is Processing
@enduml
```

### Time Format (HH:MM:SS)

```plantuml
@startuml
robust "Web Browser" as WB

@1:15:00
WB is Idle

@1:16:30
WB is Waiting

@1:17:30
WB is Processing
@enduml
```

### Custom Date Format

```plantuml
@startuml
use date format "YY-MM-dd"

robust "Web Browser" as WB

@19-07-02
WB is Idle

@19-07-04
WB is Waiting

@19-07-05
WB is Processing
@enduml
```

## Participant-Oriented Definition

Define all transitions for a single participant on one line.

```plantuml
@startuml
robust "Web Browser" as WB
concise "Web User" as WU

@WB
0 is idle
+200 is Processing
+100 is Waiting

@WU
0 is Waiting
+500 is ok
@enduml
```

## Anchor Points

Name specific times for reuse with `as :label`.

```plantuml
@startuml
clock clk with period 1
binary "Enable" as EN
concise "dataBus" as db

@0 as :start
@5 as :en_high
@10 as :en_low

@:start
EN is low
db is "0x0000"

@:en_high
EN is high

@:en_high+6
db is "0xFFFF"

@:en_low
EN is low
@enduml
```

## Decimal and Negative Time Values

Time values can be decimal (`@5.5`) or negative (`@-200`).

## Defining States by Clock Reference

Use `@<clock>*<tick>` to reference clock ticks.

```plantuml
@startuml
scale 5 as 150 pixels
clock clk with period 1
robust "Signal1" as S1

@0
S1 is 0

@clk*2
S1 is 1

@clk*4
S1 is 0
@enduml
```

## Analog Signals

```plantuml
@startuml
analog "Analog" between 0 and 500 as A

@0
A is 0

@100
A is 350

@200
A is 200

@300
A is 400

@400
A is 0
@enduml
```

## Analog Signal Range and Customization

```plantuml
@startuml
analog "VCC" between -4.5 and 6.5 as VCC
VCC ticks num on multiple 3
VCC is 200 pixels height

@0
VCC is 0

@100
VCC is 5

@200
VCC is -3

@300
VCC is 5
@enduml
```

## Messages Between Participants

```plantuml
@startuml
robust "Web Browser" as WB
concise "Web User" as WU

@0
WU is Idle
WB is Idle

@100
WU is Waiting
WU -> WB : URL

@200
WB is Processing
WB -> WU@+75 : Page

@300
WB is Waiting
@enduml
```

## Time Constraints and Delays

```plantuml
@startuml
robust "Web Browser" as WB
concise "Web User" as WU

@0
WU is Idle
WB is Idle

@100
WU is Waiting
WB is Processing

@300
WB is Waiting

WB@0 <-> @50 : {50 ms lag}
@200 <-> @+150 : {150 ms}
@enduml
```

## Highlighted Periods

```plantuml
@startuml
robust "Web Browser" as WB

@0
WB is Idle

@100
WB is Processing

@300
WB is Waiting

highlight 200 to 450 #Gold;line:DimGrey : This is my caption
@enduml
```

## Notes

```plantuml
@startuml
robust "Web Browser" as WB

@0
WB is Idle

@100
note top of WB : first note\non several\nlines
WB is Processing
@enduml
```

## Adding Colors to States

Append a color code after the state value.

```plantuml
@startuml
concise "LR" as LR
LR is AtPlace #palegreen

@200
LR is Lowered #pink

@400
LR is Raised #palegreen
@enduml
```

## Initial State and Scale

```plantuml
@startuml
scale 100 as 50 pixels

robust "Web Browser" as WB
WB is Initializing

@0
WB is idle

@100
WB is Processing
@enduml
```

## Time Axis Control

- `manual time-axis` — labels only at state-change points
- `hide time-axis` — completely remove axis

## Title, Header, Footer, Legend, Caption

```plantuml
@startuml
Title This is my title
header: some header
footer: some footer
legend
  Some legend
end legend
caption some caption

robust "Web Browser" as WB
concise "Web User" as WU

@0
WU is Idle
WB is Idle

@100
WU is Waiting
WB is Processing
@enduml
```

## Additional Resources

For intricated/hidden states, state ordering with `has`, compact mode, `<style>` blocks, stereotypes, and complete examples:
- **`timing-diagram-advanced.md`** — Less-common timing diagram features and styling
