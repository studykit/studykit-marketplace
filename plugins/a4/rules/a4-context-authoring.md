---
name: a4-context-authoring
description: Pointers for authoring `a4/context.md`. Auto-loaded on read/edit.
paths: ["a4/context.md"]
---

# a4/context.md — authoring pointers

When **authoring or editing** `a4/context.md`, read these first.

## Required reading before authoring

- [`../references/context-authoring.md`](../references/context-authoring.md) — purpose, authorship, frontmatter, body shape, common mistakes, "Don't" list, after-authoring steps.
- [`a4-workspace-policies.md`](a4-workspace-policies.md) — workspace-wide policies (also auto-loaded).

## Skill / scripts / schema

- Author / edit → `/a4:usecase` (skill: [`../skills/usecase/SKILL.md`](../skills/usecase/SKILL.md)) — primary author for `context.md`.
- Validate → `uv run ../scripts/validate_body.py "<project-root>/a4" --file context.md`
- Section read → `uv run ../scripts/extract_section.py a4/context.md <tag>`
- Body schema → `../scripts/body_schemas/context.xsd`
