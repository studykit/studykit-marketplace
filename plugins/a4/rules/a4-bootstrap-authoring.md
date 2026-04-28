---
name: a4-bootstrap-authoring
description: Pointers for authoring `a4/bootstrap.md`. Auto-loaded on read/edit.
paths: ["a4/bootstrap.md"]
---

# a4/bootstrap.md — authoring pointers

When **authoring or editing** `a4/bootstrap.md`, read these first.

## Required reading before authoring

- `../references/bootstrap-authoring.md` — purpose, single-writer rule, frontmatter, body shape (incl. why `<verify>` lives only here), common mistakes, "Don't" list.
- `a4-workspace-policies.md` — workspace-wide policies (also auto-loaded).

## Skill / scripts / schema

- Author / edit → `/a4:auto-bootstrap` (skill: `../skills/auto-bootstrap/SKILL.md`). Sole writer; re-runs archive prior copy.
- Validate → `uv run ../scripts/validate_body.py "<project-root>/a4" --file bootstrap.md`
- Section read → `uv run ../scripts/extract_section.py a4/bootstrap.md <tag>`
- Body schema → `../scripts/body_schemas/bootstrap.xsd`
