---
name: a4-domain-authoring
description: Pointers for authoring `a4/domain.md`. Auto-loaded on read/edit.
paths: ["a4/domain.md"]
---

# a4/domain.md — authoring pointers

When **authoring or editing** `a4/domain.md`, read these first.

## Required reading before authoring

- `../references/domain-authoring.md` — purpose, authorship (incl. `/a4:arch` limited allowance), frontmatter, body shape, common mistakes, "Don't" list, after-authoring steps.
- `a4-workspace-policies.md` — workspace-wide policies (also auto-loaded).

## Skill / scripts / schema

- Author / edit → `/a4:domain` (skill: `../skills/domain/SKILL.md`) — primary author.
- Limited in-situ edits → `/a4:arch` (skill: `../skills/arch/SKILL.md`) — Phase 3 b3 decision table.
- Validate → `uv run ../scripts/validate_body.py "<project-root>/a4" --file domain.md`
- Section read → `uv run ../scripts/extract_section.py a4/domain.md <tag>`
- Body schema → `../scripts/body_schemas/domain.xsd`
