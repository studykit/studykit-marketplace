# Skill Mode Design Memo

Why the a4 plugin ships the specific set of skills it does — and why several "obvious" pairs are deliberately missing. Read when proposing a new skill or removing an existing one. The current per-skill mode is the source of truth in each `../skills/<name>/SKILL.md` frontmatter; this doc captures the design rationale that frontmatter cannot.

## Two axes

A skill's mode is determined by two independent axes:

- **Mode** — does the skill make decisions *with* the user (interactive Socratic dialogue) or *for* the user (autonomous, decide-and-act)?
- **Direction** — does the skill produce **forward** output from upstream wiki (decide what to build), or **reverse / batch** output from raw input or existing code (extract from what already is)?

The `/a4:auto-*` prefix is *not* a guarantee that the skill is the autonomous twin of an interactive `/a4:*` at the same stage. `auto-usecase` is named for its autonomy, but its primary job is reverse / batch extraction (codebase or raw idea → UC set), which has no interactive analog. `auto-bootstrap` is named for its autonomy because verification work (run commands, record results) does not benefit from dialogue.

## Why missing pairs are intentional

The pipeline deliberately does **not** include:

- `/a4:auto-domain`, `/a4:auto-arch`, `/a4:auto-breakdown` — these stages are decision-collaboration. An autonomous variant would commit decisions the user has to re-litigate, multiplying review-item load without saving work.
- `/a4:bootstrap` (interactive) — bootstrap's work is verification, not decision. Environment or arch issues that need user input become review items (`auto-bootstrap` is **continue + review item** per `../workflows/wiki-authorship.md` §Stage-by-stage policy), not interactive prompts.
- `/a4:run` interactive variant — `run` is loop execution. Pause / resume / iteration entry are already supported via the `iterate` argument and review-item routing.

Adding these would inflate the namespace and prompt surface without serving real demand. Each stage's mode reflects the nature of the work, not symmetry-for-symmetry's-sake.

## Real signals for adding a missing pair

If the user repeatedly hits friction in one of the missing combinations, capture the recurring case under `<project-root>/a4/spec/` (plugin-level meta-design) before introducing a new skill. Real signals to watch:

- `auto-bootstrap` repeatedly fails on the same sandboxed / air-gapped scenarios where the issue is *which* command to run, not *whether* it works → a guided variant might earn its keep.
- `auto-usecase` is triggered when the user actually wanted interactive discovery → fix compass routing first; a true `auto` twin of `usecase` would still be inferior to dialogue.
- A decision-stage user wants to defer choices — already covered by `iterate` mode plus review items, not by autonomy.
