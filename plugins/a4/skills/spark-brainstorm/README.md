# spark-brainstorm

An expert brainstorming facilitator that helps generate ideas through structured creative thinking techniques. Assesses the situation and selects the best-fit technique from SCAMPER, Free Brainstorming, Mind Mapping, Reverse Brainstorming, Random Stimulus, and more.

## Current Notes

- **Primary file:** `plugins/a4/skills/spark-brainstorm/SKILL.md`
- **Current behavior:** Interactive facilitation skill. It selects a brainstorming technique from the bundled references and can optionally save the session summary when the user wants it.

## Workflow

```plantuml
@startuml
title spark-brainstorm Workflow

start

partition "Situation Assessment" {
  :Assess Target Existence
  (existing target vs blank slate);
  :Assess Stuckness
  (flowing vs stuck);
  :Ask 1-2 focused questions
  if dimensions unclear;
}

partition "Technique Selection" {
  switch (Situation?)
  case (Existing + Divergent)
    :Select SCAMPER;
  case (Blank slate + Divergent)
    :Select Free Brainstorming;
  case (Blank slate + Complex)
    :Select Mind Mapping;
  case (Stuck + Divergent)
    :Select Reverse Brainstorming;
  case (Stuck + Fresh perspective)
    :Select Random Stimulus;
  case (Multi-perspective)
    :Select Six Thinking Hats;
  case (Grouping needed)
    :Select Affinity Diagram;
  endswitch
  :Read technique reference file;
}

partition "Facilitation Session" {
  repeat
    :Guide with selected technique;
    :Adapt to user energy
    (scarce → contribute,
    flowing → stay back,
    stuck → reframe);
    :Summarize progress
    every 3-4 exchanges;
    if (Technique stalling?) then (yes)
      :Switch technique
      (within-phase transition);
      :Read new technique file;
    else (no)
    endif
    if (8-15+ ideas generated?) then (yes)
      :Suggest organizing
      (Six Hats / Affinity);
    else (no)
    endif
  repeat while (User continues?) is (yes) ->done;
}

partition "Wrapping Up" {
  :Ask to summarize;
  if (User agrees?) then (yes)
    :Draft summary
    (Context, Discussion Journey, Ideas);
    :Ask save location;
    :Write brainstorm file;
    :Report file path;
  else (no)
    :End session;
  endif
}

:Suggest handoff to
research + decision-review
(optional);

stop

@enduml
```
