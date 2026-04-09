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

partition "Step 2: Research and Analysis" {
  fork
    :Step 2a: Research similar systems;
    note right
      Skip if listed in
      frontmatter reflected_files
    end note
  fork again
    :Step 2b: Analyze source code;
    note left
      Skip if no source code
      referenced, or listed
      in frontmatter reflected_files
    end note
  end fork
}

partition "Step 3: Compose and Refine Loop" {

  while (Growth iteration <= 3?) is (continue)

    partition "3a: Compose" #LightBlue {
      :Launch **composer** subagent;
      note right: reflected_files updated\nin frontmatter
    }

    :3b: Verify and **commit**;

    partition "3c: Quality Loop (max 3)" #LightGreen {
      while (Quality round <= 3?) is (continue)
        :Launch **reviewer** subagent;

        if (All UCs PASS\n+ no Actor issues?) then (PASS)
          :**commit** review report;
          break
        else (NEEDS REVISION)
          :Launch **reviser** subagent;
          :**commit** review report\n+ revised document;
        endif
      endwhile (max reached)
      :Remaining issues\n-> Open Questions;
    }

    partition "3d: Growth Check" #LightYellow {
      if (System Completeness?) then (INCOMPLETE)
        :UC Candidates\nfrom reviewer;
      else (SUFFICIENT)
        :Launch **explorer** subagent;
        :**commit** exploration report;

        if (UC Candidates found?) then (yes)
          :UC Candidates\nfrom explorer;
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

| Agent | Lifecycle | Role |
|-------|-----------|------|
| **usecase-composer** | Subagent (per invocation) | Compose UC document from input + research |
| **usecase-reviewer** | Subagent (per invocation) | Review UC quality + system completeness |
| **usecase-reviser** | Subagent (per invocation) | Fix issues flagged by reviewer |
| **usecase-explorer** | Subagent (per invocation) | Explore new perspectives for UC candidates |

## Loop Structure

- **Growth Loop** (outer, max 3): Compose → Quality → Growth Check
- **Quality Loop** (inner, max 3): Review → Revise until PASS
- **Growth Check**: System Completeness first, then Perspective Exploration

## Commit Points

| Timing | Contents |
|--------|----------|
| After compose (3b) | UC document |
| After each quality round (3c) | Review report (+ revised document if NEEDS REVISION) |
| After exploration (3d) | Exploration report |

## File Naming

| File | Pattern |
|------|---------|
| UC document | `<topic-slug>.usecase.md` |
| Research report | `<topic-slug>.usecase.research-initial.md` |
| Code analysis report | `<topic-slug>.usecase.code-analysis.md` |
| Review report | `<topic-slug>.usecase.review-g<iteration>-q<round>.md` |
| Exploration report | `<topic-slug>.usecase.exploration-<iteration>.md` |

All files under `A4/`.
