# Timing Diagram — Advanced Reference

> Source: https://plantuml.com/timing-diagram

## Intricated (Undefined) Robust States

Show uncertain or transitional states by listing multiple values in braces `{a,b}`.

```plantuml
@startuml
robust "Signal1" as S1
S1 has 0,1,2,hello

@0
S1 is 0

@100
S1 is {0,1} #SlateGrey

@200
S1 is 1

@300
S1 is hello
@enduml
```

## Intricated Binary States

```plantuml
@startuml
clock clk with period 1
binary "Enable" as EN

@0
EN is low

@5
EN is {low,high}

@10
EN is low
@enduml
```

## Hidden States

Use `{-}` for a break in the signal and `{hidden}` to completely hide a section.

```plantuml
@startuml
concise "Web User" as WU

@0
WU is {-}

@100
WU is A1

@200
WU is {-}

@300
WU is {hidden}

@400
WU is A2
@enduml
```

## Ordering Robust Signal States

Use `has` to declare and order states. Optional labels with `as`.

```plantuml
@startuml
robust "Flow rate" as rate
rate has "35 gpm" as high
rate has "15 gpm" as low
rate has "0 gpm" as none

@0
rate is high

@5
rate is low

@10
rate is none
@enduml
```

## Compact Mode

Global: `mode compact`
Per-participant: `compact robust "Name" as alias`

## Styling with `<style>`

```plantuml
@startuml
<style>
timingDiagram {
  document {
    BackGroundColor SandyBrown
  }
  constraintArrow {
    LineStyle 2-1
    LineThickness 3
    LineColor Blue
  }
}
</style>

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
@enduml
```

## Stereotypes for Per-Signal Styling

```plantuml
@startuml
<style>
timingDiagram {
  .red {
    LineColor red
  }
  .blue {
    LineColor blue
    LineThickness 5
  }
}
</style>

<<blue>> binary "Output Signal 1" as OS1
<<red>> binary "Input Signal 1" as IS1

@0
OS1 is low
IS1 is low

@5
OS1 is high
IS1 is high

@10
OS1 is low
IS1 is low
@enduml
```

## Complete Digital Hardware Example

```plantuml
@startuml
scale 5 as 150 pixels

clock clk with period 1
binary "enable" as en
binary "R/W" as rw
binary "data Valid" as dv
concise "dataBus" as db
concise "address bus" as addr

@6 as :write_beg
@10 as :write_end
@15 as :read_beg
@19 as :read_end

@0
en is low
db is "0x0"
addr is "0x03f"
rw is low
dv is 0

@:write_beg-3
en is high

@:write_beg-2
db is "0xDEADBEEF"

@:write_beg-1
dv is 1

@:write_beg
rw is high

@:write_end
rw is low
dv is low

highlight :write_beg to :write_end #Gold : Write

db@:write_beg-1 <-> @:write_end : setup time
@enduml
```

## Complete Web Caching Example

```plantuml
@startuml
concise "Client" as Client
concise "Server" as Server
concise "Response freshness" as Cache

Server is idle
Client is idle

@0
Client is send
Client -> Server@+25 : GET

@+25
Client is await

@+75
Client is recv

@+25
Client is idle

@+25
Client is send
Client -> Server@+25 : GET\nIf-Modified-Since: 150

@+25
Client is await

@+50
Client is recv

@+25
Client is idle

@100 <-> @275 : no need to re-request

@Server
25 is recv
+25 is work
+25 is send
Server -> Client@+25 : 200 OK\nExpires: 275
+25 is idle
+75 is recv
+25 is send
Server -> Client@+25 : 304 Not Modified
+25 is idle

@Cache
75 is fresh
+200 is stale
@enduml
```
