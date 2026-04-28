---
name: a4-actors-authoring
description: Pointers for authoring `a4/actors.md`. Auto-loaded on read/edit.
paths: ["a4/actors.md"]
---

# a4/actors.md — authoring pointers

When **authoring or editing** `a4/actors.md`, read these first.

## Required reading before authoring

- `../references/actors-authoring.md` — purpose, authorship (incl. `/a4:arch` system-actor allowance), frontmatter, body shape, slug discipline, common mistakes, "Don't" list.
- `a4-workspace-policies.md` — workspace-wide policies (also auto-loaded).

## Skill / scripts / schema

- Author / edit → `/a4:usecase` (skill: `../skills/usecase/SKILL.md`) — primary author.
- System-actor add → `/a4:arch` (skill: `../skills/arch/SKILL.md`).
- Validate → `uv run ../scripts/validate_body.py "<project-root>/a4" --file actors.md`
- Section read → `uv run ../scripts/extract_section.py a4/actors.md <tag>`
- Body schema → `../scripts/body_schemas/actors.xsd`
