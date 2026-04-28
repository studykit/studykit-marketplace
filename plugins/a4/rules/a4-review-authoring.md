---
name: a4-review-authoring
description: Pointers for authoring `a4/review/**/*.md`. Auto-loaded on read/edit.
paths: ["a4/review/**/*.md"]
---

# a4/review/<id>-<slug>.md — authoring pointers

When **authoring or editing** any review file, read these first. (Review items are emitted by skills / agents / drift detector — never hand-written.)

## Required reading before authoring

- `../references/review-authoring.md` — kinds (finding/gap/question), emitter sources, frontmatter, lifecycle, cascade, close guard, body shape, common mistakes, "Don't" list.
- `a4-workspace-policies.md` — workspace-wide policies (also auto-loaded).

## Skill / scripts / schema

- Drift scan → `/a4:drift` (skill: `../skills/drift/SKILL.md`). Writes `source: drift-detector`.
- Resolve → iterate flows: `/a4:usecase iterate`, `/a4:arch iterate`, `/a4:domain iterate`, `/a4:roadmap iterate`, `/a4:run iterate`.
- Status flips → `../scripts/transition_status.py` (writer-only; handles `target: usecase/X discarded` cascade).
- Validate → `uv run ../scripts/validate_body.py "<project-root>/a4" --file review/<id>-<slug>.md`
- Section read → `uv run ../scripts/extract_section.py <file> <tag>`
- Body schema → `../scripts/body_schemas/review.xsd`
