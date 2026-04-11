# think-plan

Collaboratively derive an implementation plan from a specification, including units, dependencies, file mappings, and verification strategy.

## Workflow

```plantuml
@startuml think-plan-workflow
title think-plan Workflow
skinparam activityFontSize 12

start
:Resolve spec / plan input;
if (Existing .impl-plan.md?) then (yes)
  :Run existing-plan entry;
  if (Major spec or plan change?) then (redesign)
    :Switch to first-design flow;
  else (iteration)
    :Load backlog and choose update area;
  endif
else (no)
  :Start first-design flow;
endif

:Explore codebase patterns and test setup;
:Summarize spec;
:Select implementation strategy;

:Derive implementation units with user;
while (More units to define?) is (yes)
  :Present unit;
  :Adjust size / scope;
  :Confirm unit;
endwhile (no)

:Map dependencies;
:Generate implementation order and PlantUML graph;

while (More unit details to fill?) is (yes)
  :Define file mapping;
  :Define test strategy;
  :Define acceptance criteria;
endwhile (no)

:Derive Launch & Verify section;
:Write checkpointed plan updates;

if (Run risk assessment?) then (yes)
  :Launch risk assessor;
  :Reflect accepted risks into plan;
endif

:Show status and let user continue, iterate, or stop;
stop
@enduml
```

## Main Deliverables

- Ordered implementation units (IUs)
- Dependency graph + implementation order
- Per-IU file mappings, tests, acceptance criteria
- Launch & Verify section
- Optional reflected risk assessment

## Mode Split

- **First Design**: full flow from codebase exploration to risk assessment.
- **Iteration**: inspect spec changes, unreflected reports, and backlog before editing the plan.
