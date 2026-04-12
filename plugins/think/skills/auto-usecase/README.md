# auto-usecase

Autonomously generates a complete Use Case document from an idea or brainstorm input — no human interaction. Runs research, composes, reviews, and expands through iterative growth loops.

## Current Notes

- **Primary file:** `plugins/think/skills/auto-usecase/SKILL.md`
- **Current behavior:** Runs autonomously from an idea or source file, writes `A4/<slug>.usecase.md`, and coordinates research / review / exploration reports for incremental resume support.

## Workflow

```plantuml
@startuml
title auto-usecase Workflow

start

partition "Step 1: Understand Input" {
  :Parse input
  (idea, file path, or description);
  :Determine topic slug;
  if (Output file exists?) then (yes)
    :Resume Detection
    (check research, code analysis,
    last_step, reflected_files);
  else (no)
  endif
}

partition "Step 2: Research & Analysis" {
  fork
    :2a: Research Similar Systems
    (launch research agent,
    search comparable products,
    identify UC candidates);
  fork again
    if (Source code referenced?) then (yes)
      :2b: Analyze Source Code
      (launch code analysis agent,
      extract features and actors);
    else (no)
    endif
  end fork
}

partition "Step 3: Compose & Refine" {
  repeat :Growth Iteration;

    :3a: Compose
    (launch usecase-composer agent);

    :3b: Verify & Commit;

    partition "3c: Quality Loop (inner)" {
      repeat
        :Launch usecase-reviewer agent;
        if (Verdict?) then (ALL_PASS)
          :Commit review report;
          break
        else (NEEDS_REVISION)
          :Launch usecase-reviser agent;
          :Commit revised document;
        endif
      backward :Next quality round;
      repeat while (Round <= 3?) is (yes) ->max reached;
    }

    partition "3d: Growth Check (outer)" {
      if (System completeness?) then (INCOMPLETE)
        :Pass UC Candidates
        back to compose;
      else (SUFFICIENT)
        :Launch usecase-explorer agent;
        if (UC Candidates found?) then (yes)
          :Pass candidates
          back to compose;
        else (no)
          break
        endif
      endif
    }

  backward :Next growth iteration;
  repeat while (Iteration <= 3?) is (yes) ->max reached;
}

:Report results
(UCs generated, coverage,
growth iterations, review status);

stop

@enduml
```
