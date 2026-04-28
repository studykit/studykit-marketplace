---
name: a4-architecture-authoring
description: Pointers for authoring `a4/architecture.md`. Auto-loaded on read/edit.
paths: ["a4/architecture.md"]
---

# a4/architecture.md — authoring pointers

When **authoring or editing** `a4/architecture.md`, read these first. (On read-only access this rule already loaded; the references below carry the substance.)

## Required reading before authoring

- [`../references/architecture-authoring.md`](../references/architecture-authoring.md) — purpose, single-author rule, frontmatter contract, body shape, common mistakes, "Don't" list, after-authoring next steps.
- [`a4-workspace-policies.md`](a4-workspace-policies.md) — workspace-wide policies (also auto-loaded).

## Skill / scripts / schema

- Author / edit → `/a4:arch` (skill: [`../skills/arch/SKILL.md`](../skills/arch/SKILL.md)). Only in-situ editor.
- Validate → `uv run ../scripts/validate_body.py "<project-root>/a4" --file architecture.md`
- Section read → `uv run ../scripts/extract_section.py a4/architecture.md <tag>`
- Body schema → `../scripts/body_schemas/architecture.xsd`
