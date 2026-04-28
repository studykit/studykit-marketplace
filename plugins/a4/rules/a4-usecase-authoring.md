---
name: a4-usecase-authoring
description: Pointers for authoring `a4/usecase/**/*.md`. Auto-loaded on read/edit.
paths: ["a4/usecase/**/*.md"]
---

# a4/usecase/<id>-<slug>.md — authoring pointers

When **authoring or editing** any UC file, read these first.

## Required reading before authoring

- [`../references/usecase-authoring.md`](../references/usecase-authoring.md) — purpose, abstraction discipline, frontmatter, lifecycle, body shape, in-situ wiki nudge, splitting protocol, common mistakes, "Don't" list.
- [`a4-workspace-policies.md`](a4-workspace-policies.md) — workspace-wide policies (also auto-loaded).

## Skill / scripts / schema

- Socratic interview → `/a4:usecase` (skill: [`../skills/usecase/SKILL.md`](../skills/usecase/SKILL.md)) — primary author for `context.md`, `actors.md`, `nfr.md` too.
- Forward-shape draft → `/a4:auto-usecase` (skill: [`../skills/auto-usecase/SKILL.md`](../skills/auto-usecase/SKILL.md)).
- Status flips → `../scripts/transition_status.py`.
- Reverse-link refresh → `../scripts/refresh_implemented_by.py`.
- Validate → `uv run ../scripts/validate_body.py "<project-root>/a4" --file usecase/<id>-<slug>.md`
- Section read → `uv run ../scripts/extract_section.py <file> <tag>`
- Body schema → `../scripts/body_schemas/usecase.xsd`
- Abstraction guard → [`../skills/usecase/references/abstraction-guard.md`](../skills/usecase/references/abstraction-guard.md)
- Splitting guide → [`../skills/usecase/references/usecase-splitting.md`](../skills/usecase/references/usecase-splitting.md)
