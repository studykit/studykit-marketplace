# think-verify

Verify the implemented system end-to-end against the plan and spec, then diagnose failures by stage.

## Workflow

```plantuml
@startuml think-verify-workflow
title think-verify Workflow
skinparam activityFontSize 12

start
:Resolve plan / spec input;
:Read plan, spec, and prior reports;
:Extract Launch & Verify settings;
:Install or confirm verification tool;

:Run build;
if (Build passes?) then (yes)
  :Launch app with test isolation;
  if (App ready?) then (yes)
    :Run full test suite;
    :Verify platform capabilities and smoke scenario;

    while (More FRs to verify?) is (yes)
      :Perform user action;
      :Check expected behavior;
      :Capture evidence;
      :Record PASS / FAIL / BLOCKED / SKIP;
    endwhile (no)

    while (Remaining FAIL or BLOCKED?) is (yes)
      :Run Waterfall Trace;
      if (Root cause is code?) then (yes)
        :Spawn code-executor for fix;
        :Re-verify affected FR;
      else (no)
        :Record spec / plan issue;
      endif
    endwhile (no)
  else (no)
    :Record launch failure as L1;
  endif
else (no)
  :Record build failure as L1;
endif

:Write new integration report;
:Commit report;
stop
@enduml
```

## Diagnosis Waterfall

1. FR exists in spec?
2. IU covers FR in plan?
3. IU instructions are sufficient?
4. Code matches the IU?

The first failing check determines whether the issue belongs to **spec**, **plan**, or **code**.

## Output

A fresh `integration-report` file per run, including evidence, diagnosis, and auto-fix attempts.
