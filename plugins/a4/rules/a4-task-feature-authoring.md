---
name: a4-task-feature-authoring
description: Pointers for authoring `a4/task/feature/**/*.md`. Auto-loaded on read/edit.
paths: ["a4/task/feature/**/*.md"]
---

# a4/task/feature/<id>-<slug>.md — authoring pointers

When **authoring or editing** any feature task file, read these first.

## Required reading before authoring

- [`../references/task-feature-authoring.md`](../references/task-feature-authoring.md) — purpose, smell check (empty anchors), frontmatter, lifecycle, body shape, complete-preflight, common mistakes, "Don't" list.
- [`a4-workspace-policies.md`](a4-workspace-policies.md) — workspace-wide policies (also auto-loaded).

## Skill / scripts / schema

- Single ad-hoc → `/a4:task` (skill: [`../skills/task/SKILL.md`](../skills/task/SKILL.md)).
- UC-driven batch → `/a4:roadmap` (skill: [`../skills/roadmap/SKILL.md`](../skills/roadmap/SKILL.md)).
- Discard → `/a4:task discard <id-or-slug> [reason]` (procedure: [`../skills/task/references/discard.md`](../skills/task/references/discard.md)).
- Status flips → `../scripts/transition_status.py`.
- Reverse-link refresh → `../scripts/refresh_implemented_by.py`.
- Validate → `uv run ../scripts/validate_body.py "<project-root>/a4" --file task/feature/<id>-<slug>.md`
- Section read → `uv run ../scripts/extract_section.py <file> <tag>`
- Body schema → `../scripts/body_schemas/task.xsd`
- Sibling rules: [`a4-task-bug-authoring.md`](a4-task-bug-authoring.md), [`a4-task-spike-authoring.md`](a4-task-spike-authoring.md)
