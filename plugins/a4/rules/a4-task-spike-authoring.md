---
name: a4-task-spike-authoring
description: Pointers for authoring `a4/task/spike/**/*.md`. Auto-loaded on read/edit.
paths: ["a4/task/spike/**/*.md"]
---

# a4/task/spike/<id>-<slug>.md — authoring pointers

When **authoring or editing** any spike task file, read these first.

## Required reading before authoring

- [`../references/task-spike-authoring.md`](../references/task-spike-authoring.md) — purpose, sidecar convention (`<project-root>/spike/<id>-<slug>/`), frontmatter, lifecycle, body shape, common mistakes, "Don't" list.
- [`a4-workspace-policies.md`](a4-workspace-policies.md) — workspace-wide policies (also auto-loaded).

## Skill / scripts / schema

- Single ad-hoc → `/a4:task` (skill: [`../skills/task/SKILL.md`](../skills/task/SKILL.md)). No `/a4:roadmap` path.
- Discard → `/a4:task discard <id-or-slug> [reason]` (procedure: [`../skills/task/references/discard.md`](../skills/task/references/discard.md)). Sidecar archive is a manual `git mv`.
- Status flips → `../scripts/transition_status.py`.
- Validate → `uv run ../scripts/validate_body.py "<project-root>/a4" --file task/spike/<id>-<slug>.md`
- Section read → `uv run ../scripts/extract_section.py <file> <tag>`
- Body schema → `../scripts/body_schemas/task.xsd`
- Sibling rules: [`a4-task-feature-authoring.md`](a4-task-feature-authoring.md), [`a4-task-bug-authoring.md`](a4-task-bug-authoring.md)
