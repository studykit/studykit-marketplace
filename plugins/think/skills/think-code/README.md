# think-code

Execute an implementation plan by orchestrating `coder` agents unit by unit.

## Workflow

```plantuml
@startuml think-code-workflow
title think-code Workflow
skinparam activityFontSize 12

start
:Resolve and confirm .impl-plan.md;
:Read plan;
if (All TODO?) then (fresh start)
  :Fresh Start mode;
elseif (DONE + TODO mix?) then (resume)
  :Resume mode;
else (IN_PROGRESS)
  :Interrupted-session recovery;
endif

:Explore codebase and test runner;
:Review plan summary with user;

while (More phases to execute?) is (yes)
  if (Sequential phase?) then (yes)
    while (More units in phase?) is (yes)
      :Create tasks;
      :Mark IU IN_PROGRESS;
      :Spawn fresh coder agent;
      if (Agent success?) then (yes)
        :Mark IU DONE;
        :Write completion note;
      else (deviation)
        :Write deviation note;
        :Reset IU to TODO;
        :Block downstream runtime tasks;
      endif
    endwhile (no)
  else (parallel)
    :Spawn one isolated agent per IU;
    :Wait for all results;
    :Merge worktrees and run full test suite;
    :Update plan file;
  endif

  :Show phase summary and ask whether to continue;
endwhile (no)

:Report completed / remaining / blocked IUs;
stop
@enduml
```

## Agent Contract

| Input to agent | Output from agent |
|---|---|
| IU details, codebase context, recent completion notes, shared integration points | `success` or `deviation`, completion note, commit hash, or deviation details |

## Deviation Rule

Only escalate **plan vs reality mismatches**. Normal build/test failures stay within the agent's responsibility.
