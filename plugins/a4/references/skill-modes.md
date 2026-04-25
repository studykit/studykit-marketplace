# Skill Modes — Interactive vs Autonomous, Forward vs Reverse

Why each a4 pipeline stage has the mode it has, and why the missing interactive/autonomous pairs are intentional rather than gaps.

Companion to:
- [`wiki-authorship.md`](./wiki-authorship.md) — who can write each wiki page and how cross-stage feedback flows.
- [`frontmatter-schema.md`](./frontmatter-schema.md) — field-level rules.

## Two axes, not one

A skill's mode is determined by two independent axes:

- **Mode** — does the skill make decisions *with* the user (interactive Socratic dialogue) or *for* the user (autonomous, decide-and-act)?
- **Direction** — does the skill produce **forward** output from upstream wiki (decide what to build), or **reverse / batch** output from raw input or existing code (extract from what already is)?

The `/a4:auto-*` prefix is *not* a guarantee that the skill is the autonomous twin of an interactive `/a4:*` at the same stage. `auto-usecase` is named for its autonomy, but its primary job is reverse / batch extraction (codebase or raw idea → UC set), which has no interactive analog. `auto-bootstrap` is named for its autonomy because verification work (run commands, record results) does not benefit from dialogue.

## Per-stage mode

| Stage | Mode | Direction | Rationale |
|---|---|---|---|
| `usecase` | **interactive** | forward (Socratic discovery) | UCs are *discovered* by dialogue with a user who knows the problem; no automation replaces that knowledge |
| `auto-usecase` | autonomous | **reverse / batch** | Distinct job: extract or batch-shape UCs from raw input (codebase, idea, brainstorm). Not an "auto twin" of `usecase` — different input shape |
| `domain` | **interactive** | forward | Cross-cutting concept extraction is a decision-collaboration step (split / merge / state) requiring user judgement |
| `arch` | **interactive** | forward | Architecture choices are decisions; collaborative dialogue is the work |
| `roadmap` | **interactive** | forward | Milestone shaping and dependency calls require user judgement |
| `auto-bootstrap` | **autonomous** | forward | Pure verification — run build / launch / test commands, record what works. Environment / arch escape hatches flow through review items, not interactive prompts |
| `run` | **autonomous** | forward | Loop execution — implement / test until pass. Not a decision step; iteration entry is the `iterate` argument |

## Why missing pairs are intentional

The pipeline deliberately does **not** include:

- `/a4:auto-domain`, `/a4:auto-arch`, `/a4:auto-roadmap` — these stages are decision-collaboration. An autonomous variant would commit decisions the user has to re-litigate, multiplying review-item load without saving work.
- `/a4:bootstrap` (interactive) — bootstrap's work is verification, not decision. Environment or arch issues that need user input become review items (`auto-bootstrap` is **continue + review item** per [`wiki-authorship.md`](./wiki-authorship.md) §Stage-by-stage policy), not interactive prompts.
- `/a4:run` interactive variant — `run` is loop execution. Pause / resume / iteration entry are already supported via the `iterate` argument and review-item routing.

Adding these would inflate the namespace and prompt surface without serving real demand. Each stage's mode reflects the nature of the work, not symmetry-for-symmetry's-sake.

## When a missing pair becomes a real gap

If the user repeatedly hits friction in one of the missing combinations, capture the recurring case under `plugins/a4/spec/` (plugin-level meta-design) before introducing a new skill. Real signals to watch:

- `auto-bootstrap` repeatedly fails on the same sandboxed / air-gapped scenarios where the issue is *which* command to run, not *whether* it works → a guided variant might earn its keep.
- `auto-usecase` is triggered when the user actually wanted interactive discovery → fix compass routing first; a true `auto` twin of `usecase` would still be inferior to dialogue.
- A decision-stage user wants to defer choices — already covered by `iterate` mode plus review items, not by autonomy.

## Reading order

When changing skill mode behavior, read this document **before** SKILL.md edits. This is the "who decides vs who verifies" reference; `wiki-authorship.md` is the "who can write what" reference.
