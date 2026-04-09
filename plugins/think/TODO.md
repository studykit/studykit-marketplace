# TODO

## auto-spec skill

Create `auto-spec` skill to bridge the autonomous pipeline gap:
- auto-usecase (.usecase.md) → **auto-spec** (.spec.md) → auto-plan (.impl-plan.md)
- Currently users must use interactive think-spec in between

## auto-plan downstream handoff

Add think-code suggestion to auto-plan's Final Output:
- auto-plan → think-code

## auto-plan history file

Add history file (`<topic-slug>.impl-plan.history.md`) to auto-plan:
- Consolidated change timeline per quality round (units added, split, dependencies fixed)
- Autonomous decision rationale (strategy choice, unit sizing, etc.)
- Enables think-plan to pick up context when iterating on auto-plan output

## auto pipeline full handoff chain

Once auto-spec is ready, add downstream suggestions:
- auto-usecase → auto-spec
- auto-spec → auto-plan
