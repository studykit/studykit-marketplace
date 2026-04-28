---
name: a4-nfr-authoring
description: Pointers for authoring `a4/nfr.md`. Auto-loaded on read/edit.
paths: ["a4/nfr.md"]
---

# a4/nfr.md — authoring pointers

When **authoring or editing** `a4/nfr.md`, read these first.

## Required reading before authoring

- [`../references/nfr-authoring.md`](../references/nfr-authoring.md) — purpose, authorship (incl. `/a4:arch` footnote allowance), frontmatter, body shape, common mistakes, "Don't" list.
- [`a4-workspace-policies.md`](a4-workspace-policies.md) — workspace-wide policies (also auto-loaded).

## Skill / scripts / schema

- Author / edit → `/a4:usecase` (skill: [`../skills/usecase/SKILL.md`](../skills/usecase/SKILL.md)) — primary author.
- Footnote annotations only → `/a4:arch` (skill: [`../skills/arch/SKILL.md`](../skills/arch/SKILL.md)).
- Validate → `uv run ../scripts/validate_body.py "<project-root>/a4" --file nfr.md`
- Section read → `uv run ../scripts/extract_section.py a4/nfr.md <tag>`
- Body schema → `../scripts/body_schemas/nfr.xsd`
