# compass

Pipeline navigator that helps users find the right skill or diagnose the next step in an ongoing pipeline. Acts as an entry point when the user doesn't know where to start or is stuck mid-pipeline.

## Current Notes

- **Primary file:** `plugins/think/skills/compass/SKILL.md`
- **Current behavior:** Acts as the navigation entry point for the think pipeline. It inspects existing `a4/` artifacts first and then recommends or invokes the next skill.

## Workflow

```plantuml
@startuml
title compass Workflow

start

partition "Step 1: Detect Context" {
  if ($ARGUMENTS is file path\nor topic slug?) then (yes)
    :Extract topic slug;
    :Scan for artifacts
    in a4/<slug>*;
    if (Artifacts found?) then (yes)
      -> Pipeline Diagnosis;
    else (no)
      -> Fresh Start;
    endif
  else (no / free-text)
    -> Fresh Start;
  endif
}

partition "Step 2: Fresh Start" {
  :Present skill catalog
  (Ideation, Pipeline interactive,
  Pipeline autonomous, Standalone);
  :Ask "What are you trying to do?";
  :User selects a skill;
  :Invoke selected skill;
  stop
}

partition "Step 3: Pipeline Diagnosis" {
  :3.1: Read artifact state
  (status, open items, source SHA,
  plan phase/cycle);

  :3.2: Read implementation state
  (file mappings, file existence check);

  :3.3: Diagnose gap layer;
  if (UC issues?) then (yes)
    :Recommend think-usecase;
  elseif (No arch / arch issues?) then (yes)
    :Recommend think-arch;
  elseif (No bootstrap / failures?) then (yes)
    :Recommend auto-bootstrap;
  elseif (No plan / plan issues?) then (yes)
    :Recommend think-plan;
  else (complete)
    :Report completion status;
  endif

  :3.4: Present diagnosis
  (status table + recommendation);
  :Wait for user confirmation;
  :Invoke recommended skill;
}

stop

@enduml
```
