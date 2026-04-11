# think-spec

Collaboratively turn use cases into a buildable specification covering requirements, domain model, and architecture.

## Workflow

```plantuml
@startuml think-spec-workflow
title think-spec Workflow
skinparam activityFontSize 12

start
:Resolve input files;
if (Existing .spec.md?) then (yes)
  :Run iteration entry checks;
else (no)
  :Start first-design flow;
endif

:Explore codebase and detect tech stack;

while (User wants to continue?) is (yes)
  if (Work on Requirements?) then (yes)
    :Scan excluded ideas for platform FRs;
    :Specify use cases into FRs;
    :Group UI screens;
    if (Need mocks?) then (yes)
      :Generate / iterate HTML mocks;
    endif
    :Define authorization rules if roles differ;
    :Capture NFRs if user wants them;
  endif

  if (Work on Domain Model?) then (yes)
    :Extract concepts;
    :Map relationships;
    :Define state transitions;
  endif

  if (Work on Architecture?) then (yes)
    :Identify dependencies and components;
    :Deep-dive interfaces / schemas / flows;
    :Verify technical claims;
  endif

  if (Checkpoint triggered?) then (yes)
    :Write spec update;
  endif

  :Show phase status and let user choose next move;
endwhile (no)

if (End iteration?) then (yes)
  :Run phase review and append session close;
else (finalize)
  :Resolve review findings and finalize spec;
endif
stop
@enduml
```

## Phase Structure

| Phase | Focus |
|------|-------|
| Requirements | FRs, screen groups, mocks, auth rules, NFRs |
| Domain Model | concepts, relationships, state transitions |
| Architecture | dependencies, components, schemas, interfaces |

## Key Rules

- Start from requirements in **First Design**, but allow jumping between phases.
- In **Iteration**, surface cross-phase impact whenever one phase changes.
- Keep abstraction boundaries: requirements = behavior, domain = concepts, architecture = interfaces/components.
