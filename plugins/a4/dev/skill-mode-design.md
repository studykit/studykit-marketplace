# Skill Mode Design Memo

Why the a4 plugin ships the specific set of skills it does — and why several "obvious" pairs are deliberately missing. Read when proposing a new skill or removing an existing one. The current per-skill mode is the source of truth in each `../skills/<name>/SKILL.md` frontmatter; this doc captures the design rationale that frontmatter cannot.

## Two axes

A skill's mode is determined by two independent axes:

- **Mode** — does the skill make decisions *with* the user (interactive Socratic dialogue) or *for* the user (autonomous, decide-and-act)?
- **Direction** — does the skill produce **forward** output (decide what to build, given inputs) or **extract** output from raw input / existing code (recover what already is)?

The `auto-*` / `extract-*` / `ci-*` prefixes are descriptive, not categorical. `extract-usecase` is autonomous *and* an extractor (codebase / raw idea → UC set). `auto-scaffold` is autonomous because LLM-driven scaffold work (create dirs, install deps, configure build, run a smoke check) does not benefit from per-step dialogue. `ci-setup` is autonomous because the work is install + configure + verify against a known target.

## Why missing pairs are intentional

The plugin deliberately does **not** include:

- `auto-domain`, `auto-arch`, `auto-breakdown` — these stages are decision-collaboration. An autonomous variant would commit decisions the user has to re-litigate, multiplying review-item load without saving work.
- An interactive variant of `auto-scaffold` / `ci-setup` — the work is verification + setup, not decision. Environment or arch issues that need user input become review items (continue + review item), not interactive prompts.
- An interactive `auto-coding` variant — `auto-coding` is loop execution. Pause / resume / iteration entry are already supported via the `iterate` argument and review-item routing.

Adding these would inflate the namespace and prompt surface without serving real demand. Each skill's mode reflects the nature of its work, not symmetry-for-symmetry's-sake.

## Real signals for adding a missing pair

If the user repeatedly hits friction in one of the missing combinations, capture the recurring case under `<project-root>/a4/spec/` (plugin-level meta-design) before introducing a new skill. Real signals to watch:

- `auto-scaffold` or `ci-setup` repeatedly fails on the same sandboxed / air-gapped scenarios where the issue is *which* command to run, not *whether* it works → a guided variant might earn its keep.
- `extract-usecase` is triggered when the user actually wanted interactive discovery → no twin needed; recommend `/a4:usecase` instead.
- A decision-stage user wants to defer choices — already covered by `iterate` mode plus review items, not by autonomy.
