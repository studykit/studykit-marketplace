---
name: a4-roadmap-authoring
description: Pointers for authoring `a4/roadmap.md`. Auto-loaded on read/edit.
paths: ["a4/roadmap.md"]
---

# a4/roadmap.md — authoring pointers

When **authoring or editing** `a4/roadmap.md`, read these first.

## Required reading before authoring

- `../references/roadmap-authoring.md` — purpose, single-author rule, stop-on-upstream policy, frontmatter, body shape, common mistakes, "Don't" list.
- `a4-workspace-policies.md` — workspace-wide policies (also auto-loaded).

## Skill / scripts / schema

- Author / edit → `/a4:roadmap` (skill: `../skills/roadmap/SKILL.md`).
- Validate → `uv run ../scripts/validate_body.py "<project-root>/a4" --file roadmap.md`
- Section read → `uv run ../scripts/extract_section.py a4/roadmap.md <tag>`
- Body schema → `../scripts/body_schemas/roadmap.xsd`
