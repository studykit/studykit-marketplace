# auto-usecase

Autonomously generate a complete `.usecase.md` file from raw input without human interaction.

## Workflow

```plantuml
@startuml auto-usecase-workflow
title auto-usecase Workflow
skinparam activityFontSize 12

start

:Step 1: Understand Input;
note right
  Determine topic slug,
  identify target system (if any)
end note

if (Target system exists?) then (yes)
  :Step 2: Load System Context;
else (no)
endif

partition "Resume Detection" {
  if (research-initial.consumed.md?) then (exists)
    :Skip research;
  elseif (research-initial.md?) then (exists)
    :Use existing research;
  else (neither)
    :Step 3: Launch research subagent;
    note right: Background via TeamCreate
  endif
}

partition "Step 4: Compose and Refine Loop" {

  while (Growth iteration <= 3?) is (continue)

    partition "4a: Compose" #LightBlue {
      if (First iteration?) then (yes)
        :Wait for research subagent;
      else (no)
      endif
      :**usecase-composer**\nwrites UC document;
      if (First iteration?) then (yes)
        :Rename research\nto .consumed.md;
      else (no)
      endif
    }

    :4b: Verify and **commit**;

    partition "4c: Quality Loop (max 3)" #LightGreen {
      while (Quality round <= 3?) is (continue)
        :**usecase-reviewer**\nwrites review report;

        if (All UCs PASS\n+ no Actor issues?) then (PASS)
          :**commit** review report;
          break
        else (NEEDS REVISION)
          :**usecase-reviser**\nfixes document;
          :**commit** review report\n+ revised document;
        endif
      endwhile (max reached)
      :Remaining issues\n-> Open Questions;
    }

    partition "4d: Growth Check" #LightYellow {
      if (System Completeness?) then (INCOMPLETE)
        :UC Candidates\nfrom reviewer;
      else (SUFFICIENT)
        :**usecase-explorer**\nwrites exploration report;
        :**commit** exploration report;

        if (UC Candidates found?) then (yes)
          :UC Candidates\nfrom explorer;
          :Rename exploration\nto .consumed.md;
        else (no)
          break
        endif
      endif
    }

  endwhile (max reached)
  :Remaining gaps\n-> Open Questions;
}

:Final Output;
note right
  Report: file path, UC count,
  exclusions, research summary,
  growth/review rounds,
  completeness status,
  UCs passed (M/N)
end note

stop

@enduml
```

## Agents

| Agent | Role |
|-------|------|
| **usecase-composer** | Compose UC document from input + research |
| **usecase-reviewer** | Review UC quality + system completeness |
| **usecase-reviser** | Fix issues flagged by reviewer |
| **usecase-explorer** | Explore new perspectives for UC candidates |

## Loop Structure

- **Growth Loop** (outer, max 3): Compose → Quality → Growth Check
- **Quality Loop** (inner, max 3): Review → Revise until PASS
- **Growth Check**: System Completeness first, then Perspective Exploration

## Commit Points

| Timing | Contents |
|--------|----------|
| After compose (4b) | UC document |
| After each quality round (4c) | Review report (+ revised document if NEEDS REVISION) |
| After exploration (4d) | Exploration report |

## File Naming

| File | Pattern |
|------|---------|
| UC document | `<topic-slug>.usecase.md` |
| Research report | `<topic-slug>.usecase.research-initial.md` → `.consumed.md` |
| Review report | `<topic-slug>.usecase.review-g<iteration>-q<round>.md` |
| Exploration report | `<topic-slug>.usecase.exploration-<iteration>.md` → `.consumed.md` |

All files under `A4/co-think/`.
