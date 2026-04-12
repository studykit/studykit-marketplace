# auto-plan

Autonomously generates a complete implementation plan from an architecture document — no human interaction. Makes all decisions independently, records assumptions, and refines through quality review loops.

## Workflow

```plantuml
@startuml
title auto-plan Workflow

start

partition "Step 1: Resolve Input" {
  :Resolve $ARGUMENTS
  to .arch.md file;
  :Determine topic slug;
  if (Output file exists?) then (yes)
    :Resume Detection
    (check source SHA, last_step,
    reflected_files);
  else (no)
  endif
}

partition "Step 2: Read Sources & Explore" {
  :Read .arch.md;
  :Read .usecase.md;
  if (Bootstrap report exists?) then (yes)
    :Read verified commands;
  else (no)
  endif
  :Explore codebase
  (structure, conventions,
  test setup, build config);
}

partition "Step 3: Derive Implementation Units" {
  :Choose strategy
  (hybrid / feature-first / component-first);
  :Derive units with
  UC mapping, components,
  dependencies, file mapping,
  test strategy, acceptance criteria;
}

partition "Step 4: Build Dependency Graph" {
  :Check for circular dependencies;
  :Topological sort;
  :Identify parallelizable units;
  :Generate PlantUML diagram;
}

partition "Step 5: Launch & Verify" {
  :Fill build, launch, test
  commands and smoke scenario;
}

partition "Step 6: Risk Assessment" {
  :Identify cross-cutting risks;
}

partition "Step 7–9: Write, History, Commit" {
  :Write .plan.md;
  :Write compose entry
  to history file;
  :Commit;
}

partition "Step 10: Quality Loop" {
  repeat
    :Launch plan-reviewer agent;
    if (Verdict?) then (ACTIONABLE)
      :Commit review report;
      break
    else (NEEDS_REVISION)
      :Read review report;
      :Apply fixes to plan;
      :Commit revised plan;
    endif
  backward :Next round;
  repeat while (Round <= 3?) is (yes) ->max reached;
}

:Report results to user;

stop

@enduml
```
