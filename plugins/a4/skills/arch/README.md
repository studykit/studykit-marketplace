# arch

Designs system architecture through collaborative dialogue — technology stack, external dependencies, components, information flows, interface contracts, and test strategy. Works from use cases produced by usecase.

## Current Notes

- **Primary file:** `plugins/a4/skills/arch/SKILL.md`
- **Current behavior:** Collaborative architecture design skill. It supports both first-pass design and iteration on an existing `.arch.md`, with reviewer feedback when the user wants it.

## Workflow

```plantuml
@startuml
title arch Workflow

start

partition "Input Resolution" {
  :Resolve $ARGUMENTS
  (file path, slug, or partial name);
  if (Existing .arch.md?) then (yes)
    :Iteration Mode;
    :Check source usecase changes
    (compare SHA);
    :Check unreflected reports
    (review, bootstrap, integration,
    plan, test);
  else (no)
    :First Design Mode;
  endif
}

if (First Design?) then (yes)

partition "Step 0: Explore Codebase" {
  :Explore project structure,
  conventions, dependencies,
  build setup, test config;
  if (Existing codebase?) then (yes)
    :Detect tech stack,
    confirm with user;
  else (no)
  endif
}

partition "Phase 1: Technology Stack" {
  :Select language, framework,
  platform, key libraries;
  if (Heavy decision\nwith trade-offs?) then (yes)
    :Suggest /a4:research
    for deep evaluation;
  else (lightweight)
    :Discuss inline,
    record with rationale;
  endif
}

partition "Phase 2: External Dependencies" {
  :Scan UCs for external
  interactions;
  :Present dependency list;
  :For each: clarify access pattern,
  constraints, fallback;
}

partition "Phase 3: Component Design" {
  :Identify components
  and responsibilities;
  repeat
    :Per-component deep dive
    (DB schema, information flow,
    interface contracts);
    if (Domain Model change needed?) then (yes)
      :Spawn domain-updater agent;
      :Update arch source SHA;
    else (no)
    endif
  repeat while (More components?) is (yes) ->done;
}

partition "Phase 4: Test Strategy" {
  :Identify test tiers
  (unit, integration, E2E);
  :Select tools per tier
  based on app type;
  :Verify tool choices
  (technical claim verification);
}

else (Iteration Mode)

partition "Impact Assessment" {
  :Assess new UCs against
  existing architecture;
  note right
    New components needed?
    New external dependencies?
    Tech stack changes?
    Fundamental flow changes?
  end note
  if (Fits existing arch?) then (yes)
    :Additive Feature path;
  else (no)
    :Full Iteration path;
    :Recommend starting point;
    note right
      User picks area(s)
      to rework (Phase 1–4)
    end note
    :Address selected areas
    (Phase 1–4 as needed);
  endif
}

if (Additive Feature?) then (yes)

partition "Additive Feature" {
  :Map new UCs to
  existing components;
  repeat
    :Per-UC deep dive
    (information flow,
    interface contracts);
    if (Domain Model change needed?) then (yes)
      :Spawn domain-updater agent;
      :Update arch source SHA;
    else (no)
    endif
  repeat while (More new UCs?) is (yes) ->done;
  :Review test coverage
  for new flows;
}

else (no)
endif

endif

partition "Review" {
  :Suggest review when
  areas substantially complete;
  if (User agrees?) then (yes)
    :Launch arch-reviewer agent;
    :Walk through findings;
    :Apply revisions;
  else (no)
  endif
}

partition "Wrap Up" {
  :End iteration checklist;
  :Increment revision;
  :Append session close to history;
  :Suggest next step:
  auto-bootstrap;
}

stop

@enduml
```
