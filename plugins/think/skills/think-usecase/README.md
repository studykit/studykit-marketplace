# think-usecase

Collaboratively turn an idea into concrete use cases through an interview-driven workflow.

## Workflow

```plantuml
@startuml think-usecase-workflow
title think-usecase Workflow
skinparam activityFontSize 12

start
:Resolve input and working file;
if (Existing .usecase.md?) then (yes)
  :Run iteration entry checks;
else (no)
  :Create draft working file;
endif

while (User wants to continue?) is (yes)
  :Discovery loop;
  note right
    Ask about current situation,
    actors, desired change,
    and success outcome
  end note

  if (Enough detail for a UC?) then (yes)
    :Draft use case;
    :Confirm / revise with user;
    :Track confirmed UC via task;

    if (Checkpoint triggered?) then (yes)
      :Write working file update;
      :Update actors / context / diagram;
    endif

    if (UC too large?) then (yes)
      :Split into smaller UCs;
    endif
  endif

  if (5+ UCs confirmed?) then (yes)
    :Analyze UC relationships;
  endif

  if (User requested research?) then (yes)
    :Run similar-systems research;
  endif
endwhile (no)

:Choose end iteration or finalize;
:Run reviewer;
if (User chose exploration?) then (yes)
  :Run explorer;
endif
if (Finalize?) then (yes)
  :Finalize file and create issues;
else (no)
  :Append session close and next steps;
endif
stop
@enduml
```

## Core Flow

1. Resolve or create the `.usecase.md` working file.
2. Interview the user to uncover scenarios, actors, desired behavior, and outcomes.
3. Convert concrete scenarios into confirmed use cases.
4. Write checkpoint updates instead of rewriting on every turn.
5. Review at the end of the session, then optionally explore gaps or finalize.

## Key Side Flows

- **Iteration mode**: resume from an existing `.usecase.md` with entry checks.
- **Use case splitting**: break oversized UCs into smaller independent value slices.
- **Research**: only on request or explicit agreement.
- **Review / exploration**: reviewer first, explorer only if the user chooses it.
