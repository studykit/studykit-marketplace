# think-plan

Autonomously generate an implementation plan from an architecture document, implement it, and iterate until integration and smoke tests pass.

## Workflow

```plantuml
@startuml think-plan-workflow
title think-plan Workflow
skinparam activityFontSize 12

start
:Resolve arch / plan input;

if (Existing .plan.md?) then (yes)
  :Resume from recorded phase/cycle;
else (no)
  :Start fresh;
endif

partition "Phase 1 — Plan + Verification" {
  :Read arch + usecase;
  :Explore codebase;
  :Generate plan (plan mode);
  :Write plan file;

  repeat
    :Spawn plan-reviewer agent;
    :Write review report;
    if (Issues found?) then (yes)
      if (Arch/usecase issue?) then (yes)
        :Stop — notify user;
        stop
      else (plan issue)
        :Auto-reflect into plan;
      endif
    endif
  repeat while (More rounds? (max 3)) is (yes)
  -> verification passed;
}

partition "Phase 2 — Implement + Test (max 3 cycles)" {
  repeat
    :Implement + write unit tests;
    :Unit tests must pass;
    :Run integration + smoke tests;
    :Write test report;
    if (Tests pass?) then (yes)
      :Set status: complete;
      stop
    else (no)
      if (Arch/usecase issue?) then (yes)
        :Stop — notify user;
        stop
      else (plan issue)
        :Update plan from report;
      endif
    endif
  repeat while (More cycles? (max 3)) is (yes)
  -> cycles exhausted;
  :Stop — notify user with reports;
}

stop
@enduml
```

## Main Deliverables

- Implementation plan (`.plan.md`) with IUs, dependency graph, test plan
- Working code with passing unit tests
- Integration + smoke test results
- Review and test reports for traceability

## File Structure

```
A4/<slug>.plan.md              — plan
A4/<slug>.plan.history.md      — event log (append-only)
A4/<slug>.plan.review-r<N>.md  — Phase 1 verification reports
A4/<slug>.test-report.c<N>.md  — Phase 2 test reports
```
