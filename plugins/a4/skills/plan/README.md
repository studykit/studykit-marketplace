# plan

Takes an architecture document and autonomously plans, implements, and tests the project — iterating until integration and smoke tests pass. Delegates IU implementation to per-IU subagents and orchestrates the execution order, progress tracking, and cycle loop.

## Current Notes

- **Primary file:** `plugins/a4/skills/plan/SKILL.md`
- **Current behavior:** Autonomous planning-and-execution orchestrator. It writes `.plan.md`, uses `plan-reviewer`, delegates IUs to `iu-implementer`, and uses `test-runner` for integration/smoke verification.

## Workflow

```plantuml
@startuml
title plan Workflow
skinparam conditionStyle inside

|#WhiteSmoke|tp| plan (orchestrator)
|#AliceBlue|iu| IU subagent (sonnet)
|#Lavender|ts| test subagent (sonnet)
|#MistyRose|rv| plan-reviewer agent

|tp|
start

partition "Input Resolution" {
  :Resolve $ARGUMENTS
  (full path / partial / slug);
  if (Existing .plan.md?) then (yes)
    :Resume Mode;
    note right
      Extract phase, cycle, status
      Compare source SHAs
      Check bootstrap staleness
      Reflect unreflected reports
    end note
    :Continue from recorded
    phase / cycle;
  else (only .arch.md)
    :Fresh Mode;
  endif
}

partition "Phase 1 — Plan Generation + Verification" #LightCyan {

  :Step 1: Read Sources;
  note right
    .arch.md — tech stack,
    components, contracts
    .usecase.md — UCs, domain model
    bootstrap report — verified
    build/run/test commands
  end note

  :Step 2: Explore Codebase
  (structure, conventions,
  patterns, test setup);

  :Step 3: Generate Plan
  (enter plan mode);
  note right
    Strategy (component / feature / hybrid)
    IUs with file mappings + unit test paths
    Dependency graph + implementation order
    Test plan: integration + smoke cases
    Test file convention
    Launch & Verify config
  end note
  :Write .plan.md
  (phase: plan-review, revision: 1);
  :Commit: plan + history;

  partition "Step 4: Verification Loop" {
    repeat
      |rv|
      :Review plan;
      note left
        FR coverage
        Component/contract coverage
        Tech stack consistency
        Test plan completeness
        Dependency validity
        File mapping specificity
      end note
      :Write review report;

      |tp|
      :Read review report;
      if (Issue type?) then (plan)
        :Auto-reflect into plan;
        :Increment revision;
        :Commit: report + plan + history;
      elseif (arch / usecase) then (upstream)
        :Set status: blocked; <<#Pink>>
        :Report upstream issues to user;
        stop
      else (all pass)
        break
      endif
    backward :Next round;
    repeat while (Round <= 3?) is (yes) ->done;
  }

  :Set phase: implement, cycle: 1;
  :Commit;
}

partition "Phase 2 — Implement + Test Loop" #Honeydew {

  repeat

    partition "Step 5: IU Implementation" {
      |tp|
      repeat
        :Identify ready IUs
        (deps all ""done"", status ""pending"");

        |iu|
        fork
          :Implement code
          per IU file mappings;
          :Write unit tests;
          :Run unit tests until pass;
          :Commit: code + tests;
          :Return: result + summary;
        fork again
          :Implement code
          per IU file mappings;
          :Write unit tests;
          :Run unit tests until pass;
          :Commit: code + tests;
          :Return: result + summary;
        end fork
        note right
          Independent IUs
          run in parallel
        end note

        |tp|
        :Track IU results;
        :pass -> status: **done**
        fail -> status: **failed**
        + record failure summary;

        if (Every 3 IUs?) then (checkpoint)
          :Update .plan.md statuses;
          :Commit;
        else (continue)
        endif

      repeat while (More ready IUs?) is (yes) ->all dispatched;
    }

    partition "Step 6: Integration + Smoke Test" {
      |ts|
      :Run integration test cases
      from plan's test plan;
      :Run smoke test cases
      from plan's test plan;
      :Write test report
      (factual results only);
      :Commit: test report;
    }

    partition "Step 7: Analyze Results" {
      |tp|
      :Read test report
      + IU failure summaries;

      if (All IUs done +\nall tests pass?) then (yes)
        :Set status: complete; <<#LightGreen>>
        :Commit: plan + history;
        :Report success to user;
        stop
      else (failures)
      endif

      :Classify failures
      using plan + arch context;

      if (Root cause?) then (arch / usecase)
        :Set status: blocked; <<#Pink>>
        :Report upstream issues to user;
        :Commit: plan + history;
        stop
      else (plan issues)
      endif

      :Autonomous plan revision;
      note right
        Identify affected IUs
        Revise descriptions / file mappings /
        deps / acceptance criteria
        Check ripple effects on dependents
        Reset affected IUs to ""pending""
      end note
      :Add test report to reflected_files;
      :Increment revision;
      :Commit: plan + history;

      |rv|
      :Verify revised plan;
      :Write review report;

      |tp|
      if (Reviewer result?) then (plan issues)
        :Fix and re-verify
        (max 2 inner rounds);
      elseif (arch / usecase) then (upstream)
        :Set status: blocked; <<#Pink>>
        :Report to user;
        stop
      else (pass)
      endif

      :Increment cycle;
    }

  backward :Next cycle;
  repeat while (Cycle <= 3?) is (yes) ->max reached;

  :Set status: blocked; <<#Pink>>
  :Report remaining failures
  (IU statuses, all test reports);
}

stop

@enduml
```
