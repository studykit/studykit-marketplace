# TODO

## auto-arch skill

Create `auto-arch` skill to bridge the autonomous pipeline gap:
- auto-usecase (.usecase.md) → **auto-arch** (.arch.md) → auto-scaffold → auto-plan (.impl-plan.md)
- Currently users must use interactive think-arch in between

## compass skill (pipeline navigator)

~~Create a `compass` router skill that triages user intent and diagnoses pipeline state.~~ **Done** — `skills/compass/SKILL.md`

Remaining work:
- Test with real pipeline artifacts
- Validate diagnosis accuracy on edge cases (e.g., multiple open items across layers)

## think-refactor skill

Create a skill for restructuring existing codebases:
- Analyzes an existing codebase and identifies restructuring opportunities
- Produces an architecture delta + plan that feeds into think-plan
- Fills the gap: current pipeline is greenfield-only (idea → code)
- Common need: "I have existing code, help me rethink/restructure it"

## spark-retrospective skill

Create a post-implementation learning capture skill:
- Runs after think-plan completes (Phase 2 — all tests pass or blocked)
- Analyzes: test reports, plan review cycle counts, blocked status diagnoses
- Surfaces patterns and lessons learned across the project
- Useful for cross-project learning, not just current iteration feedback

## Pipeline orchestrator

Create a mode or thin wrapper to chain the full autonomous pipeline:
- auto-usecase → auto-arch → auto-scaffold → auto-plan
- Eliminates manual invocation and file path passing between steps
- Depends on: auto-arch completion

## ~~auto-plan history file~~

~~Add history file (`<topic-slug>.impl-plan.history.md`) to auto-plan:~~
~~- Consolidated change timeline per quality round (units added, split, dependencies fixed)~~
~~- Autonomous decision rationale (strategy choice, unit sizing, etc.)~~
~~- Enables think-plan to pick up context when iterating on auto-plan output~~

**Done** — `skills/auto-plan/references/session-history.md`, integrated into SKILL.md Steps 8–10

## auto pipeline handoff chain

Once auto-arch is ready, add downstream suggestions:
- auto-usecase → auto-arch
- auto-arch → auto-scaffold
- auto-scaffold → auto-plan
- auto-plan: no downstream suggestion (think-plan Phase 2 handles implementation)
