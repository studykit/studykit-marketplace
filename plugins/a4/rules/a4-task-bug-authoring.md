---
name: a4-task-bug-authoring
description: Pointers for authoring `a4/task/bug/**/*.md`. Auto-loaded on read/edit.
paths: ["a4/task/bug/**/*.md"]
---

# a4/task/bug/<id>-<slug>.md — authoring pointers

When **authoring or editing** any bug task file, read these first.

## Required reading before authoring

- [`../references/task-bug-authoring.md`](../references/task-bug-authoring.md) — purpose, frontmatter, lifecycle, body shape, complete-preflight, common mistakes, "Don't" list (incl. regression-test requirement).
- [`a4-workspace-policies.md`](a4-workspace-policies.md) — workspace-wide policies (also auto-loaded).

## Skill / scripts / schema

- Single ad-hoc → `/a4:task` (skill: [`../skills/task/SKILL.md`](../skills/task/SKILL.md)). No `/a4:roadmap` path; bugs are single-task only.
- Discard → `/a4:task discard <id-or-slug> [reason]` (procedure: [`../skills/task/references/discard.md`](../skills/task/references/discard.md)).
- Status flips → `../scripts/transition_status.py`.
- Validate → `uv run ../scripts/validate_body.py "<project-root>/a4" --file task/bug/<id>-<slug>.md`
- Section read → `uv run ../scripts/extract_section.py <file> <tag>`
- Body schema → `../scripts/body_schemas/task.xsd`
- Sibling rules: [`a4-task-feature-authoring.md`](a4-task-feature-authoring.md), [`a4-task-spike-authoring.md`](a4-task-spike-authoring.md)
