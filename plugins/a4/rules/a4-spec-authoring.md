---
name: a4-spec-authoring
description: Pointers for authoring `a4/spec/**/*.md`. Auto-loaded on read/edit.
paths: ["a4/spec/**/*.md"]
---

# a4/spec/<id>-<slug>.md — authoring pointers

When **authoring or editing** any spec file, read these first.

## Required reading before authoring

- [`../references/spec-authoring.md`](../references/spec-authoring.md) — when a spec is warranted, conversational triggers, anti-patterns, frontmatter, lifecycle, body shape, common mistakes, "Don't" list.
- [`a4-workspace-policies.md`](a4-workspace-policies.md) — workspace-wide policies (also auto-loaded).

## Skill / scripts / schema

- Author / activate / revise → `/a4:spec` (skill: [`../skills/spec/SKILL.md`](../skills/spec/SKILL.md)).
- Status flips → `../scripts/transition_status.py` (writer-only).
- Research linkage → `../scripts/register_research_citation.py` (atomic four-place update).
- Validate → `uv run ../scripts/validate_body.py "<project-root>/a4" --file spec/<id>-<slug>.md`
- Section read → `uv run ../scripts/extract_section.py <file> <tag>`
- Body schema → `../scripts/body_schemas/spec.xsd`
