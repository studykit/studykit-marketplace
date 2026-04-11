# Activity Diagram — Advanced Reference

> Source: https://plantuml.com/activity-diagram-beta

## Goto and Label (Experimental)

```plantuml
@startuml
title Point two queries to same activity\nwith `goto`
start
if (Test Question?) then (yes)
'space label only for alignment
label sp_lab0
label sp_lab1
'real label
label lab
:shared;
else (no)
if (Second Test Question?) then (yes)
label sp_lab2
goto sp_lab1
else
:nonShared;
endif
endif
:merge;
@enduml
```

## Connectors

Connectors create named junction points using parentheses. Can be colored.

```plantuml
@startuml
start
:Some activity;
(A)
detach
(A)
:Other activity;
@enduml
```

### Colored connectors

```plantuml
@startuml
start
:The connector below wishes he was blue;
#blue:(B)
:This next connector feels green;
#green:(G)
stop
@enduml
```

### Styled connectors

```plantuml
@startuml
<style>
circle {
  Backgroundcolor palegreen
  LineColor green
  LineThickness 2
}
</style>

(1)
:a;
(A)
@enduml
```

## SDL (Specification and Description Language) Shapes

Use `<<stereotype>>` after an activity to change its shape.

```plantuml
@startuml
start
:SDL Shape;
:input;
<<input>>
:output;
<<output>>
:procedure;
<<procedure>>
:load;
<<load>>
:save;
<<save>>
:continuous;
<<continuous>>
:task;
<<task>>
end
@enduml
```

### SDL complex example

```plantuml
@startuml
:Ready;
:next(o);
<<procedure>>
:Receiving;
split
 :nak(i);
 <<input>>
 :ack(o);
 <<output>>
split again
 :ack(i);
 <<input>>
 :next(o)
 on several lines;
 <<procedure>>
 :i := i + 1;
 <<task>>
 :ack(o);
 <<output>>
split again
 :err(i);
 <<input>>
 :nak(o);
 <<output>>
split again
 :foo;
 <<save>>
split again
 :bar;
 <<load>>
split again
 :i > 5;
 <<continuous>>
 stop
end split
:finish;
@enduml
```

## UML Shapes

```plantuml
@startuml
:action;
:object;
<<object>>
:ObjectNode typed by signal;
<<objectSignal>>
:AcceptEventAction without TimeEvent trigger;
<<acceptEvent>>
:SendSignalAction;
<<sendSignal>>
:Trigger;
<<trigger>>
:AcceptEventAction with TimeEvent trigger;
<<timeEvent>>
:an action;
@enduml
```

## Condition Style (skinparam)

Controls how condition labels are rendered.

```plantuml
@startuml
skinparam conditionStyle inside
start
repeat
  :act1;
  :act2;
repeatwhile (<b>end)
:act3;
@enduml
```

Options: `inside`, `diamond`, `InsideDiamond`

## Condition End Style

Controls the merge point shape after conditionals.

```plantuml
@startuml
skinparam ConditionEndStyle diamond
:A;
if (decision) then (yes)
    :B1;
else (no)
    :B2;
endif
:C;
@enduml
```

Options: `diamond`, `hline`

## Styling with `<style>`

```plantuml
@startuml
<style>
activityDiagram {
  BackgroundColor #33668E
  BorderColor #33668E
  FontColor #888
  FontName arial
  diamond {
    BackgroundColor #ccf
    LineColor #00FF00
    FontColor green
    FontName arial
    FontSize 15
  }
  arrow {
    FontColor gold
    FontName arial
    FontSize 15
  }
  partition {
    LineColor red
    FontColor green
    RoundCorner 10
    BackgroundColor PeachPuff
  }
  note {
    FontColor Blue
    LineColor Navy
    BackgroundColor #ccf
  }
}
document {
   BackgroundColor transparent
}
</style>
start
:init;
-> test of color;
if (color?) is (<color:red>red) then
  :print red;
else
 :print not red;
 note right: no color
endif
partition End {
  :end;
}
-> this is the end;
end
@enduml
```

## Creole and HTML Formatting in Activities

```plantuml
@startuml
:Creole:
  wave: ~~wave~~
  bold: **bold**
  italics: //italics//
  monospaced: ""monospaced""
  stricken-out: --stricken-out--
  underlined: __underlined__;
:HTML Creole:
  bold: <b>bold
  italics: <i>italics
  monospaced: <font:monospaced>monospaced
  stroked: <s>stroked
  underlined: <u>underlined
  waved: <w>waved
  Blue: <color:blue>Blue
  Orange: <back:orange>Orange background
  big: <size:20>big;
@enduml
```

## Complete Example

```plantuml
@startuml
start
:ClickServlet.handleRequest();
:new page;
if (Page.onSecurityCheck) then (true)
  :Page.onInit();
  if (isForward?) then (no)
    :Process controls;
    if (continue processing?) then (no)
      stop
    endif

    if (isPost?) then (yes)
      :Page.onPost();
    else (no)
      :Page.onGet();
    endif
    :Page.onRender();
  endif
else (false)
endif

if (do redirect?) then (yes)
  :redirect process;
else
  if (do forward?) then (yes)
    :Forward request;
  else (no)
    :Render page template;
  endif
endif

stop
@enduml
```
