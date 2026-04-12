# spark-decide

A solution discovery facilitator that helps move from multiple options to a well-reasoned decision through structured research and evaluation. Produces an Architecture Decision Record (ADR) with rationale, rejected alternatives, and next steps.

## Workflow

```plantuml
@startuml
title spark-decide Workflow

start

partition "Input Handling" {
  if (File path provided?) then (yes)
    :Read file, extract ideas;
    :Present options to user;
    -> Phase 2;
  else (topic/problem)
    -> Phase 1;
  endif
}

partition "Phase 1: Problem Framing" {
  :Uncover the decision,
  trigger, constraints;
  :Identify success criteria
  (force-rank top 3-5);
}

partition "Framework Selection" {
  switch (Decision type?)
  case (3+ options, quantifiable)
    :Weighted Scoring;
  case (Compare vs baseline)
    :Pugh Matrix;
  case (Quick, 2-3 options)
    :Pros-Cons-Risks;
  case (Strategic, external)
    :SWOT per Option;
  case (Resource-constrained)
    :Cost-Benefit;
  endswitch
  :Create working file
  with Context & Criteria;
}

partition "Phase 2: Option Generation" {
  if (From brainstorm file?) then (yes)
    :Present extracted ideas;
    :User selects options to evaluate;
  else (fresh)
    :Brainstorm 3-7 candidates;
  endif
  :Confirm final option list;
  :Checkpoint write;
}

partition "Phase 3: Research" {
  repeat
    :Ask before researching each option;
    :Research option
    (WebSearch, codebase, Agent);
    :Present findings objectively;
    :Track via task;
  repeat while (More options?) is (yes) ->done;
  :Research checkpoint;
}

partition "Phase 4: Evaluation" {
  :Walk through framework
  evaluation systematically;
  :Surface disagreements;
  if (Conversation stuck?) then (yes)
    :Apply challenge mode
    (Devil's Advocate / Reframer);
  else (no)
  endif
  :Sensitivity check;
}

partition "Phase 5: Decision" {
  :State the decision;
  :Document trade-offs;
  :Document rejected alternatives;
  :Assess reversibility;
  :Identify risks;
  :Define next steps;
}

partition "Wrap Up" {
  :Run decision-reviewer agent;
  :Walk through review findings;
  :Apply revisions;
  :Finalize file (status: final);
  :Report file path;
}

stop

@enduml
```
