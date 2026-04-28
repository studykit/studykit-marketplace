---
name: a4-workspace-policies
description: Cross-cutting policy pointers for any file under `a4/`. Auto-loaded on every `a4/**/*.md` read.
paths: ["a4/**/*.md"]
---

# a4 — workspace policy index

These pointers apply to **every** file under `a4/`, regardless of type or location. Per-type rules (`a4-<type>-authoring.md`) build on these — they do not redefine them. The substance lives in [`../references/`](../references); this rule is the route in.

## Cross-cutting contracts

- [`../references/frontmatter-schema.md`](../references/frontmatter-schema.md) — full field schema, lifecycle tables, validator behavior, writer-owned fields.
- [`../references/body-conventions.md`](../references/body-conventions.md) — body tag form, blank-line discipline, link form, frontmatter vs body path-reference form, `<change-logs>` / `<log>` rules, wiki update protocol.
- [`../references/wiki-authorship.md`](../references/wiki-authorship.md) — primary-author table, in-situ edit allowances, cross-stage stop/continue policy.
- [`../references/iterate-mechanics.md`](../references/iterate-mechanics.md) — review-item walk procedure (filter, transition, close guard).
- [`../references/spec-triggers.md`](../references/spec-triggers.md) — when a spec is warranted; conversational + content-aware triggers; anti-patterns.
- [`../references/commit-message-convention.md`](../references/commit-message-convention.md) — `#<id>` commit subject form.
- [`../references/pipeline-shapes.md`](../references/pipeline-shapes.md) — Full / Reverse / Minimal / No-shape pipelines.
- [`../references/skill-modes.md`](../references/skill-modes.md) — interactive vs autonomous, forward vs reverse axes per skill.

## Writer scripts (never hand-edit the fields they own)

- `../scripts/transition_status.py` — `status:` and `<log>` for task / usecase / spec / review (incl. cascades: UC discarded → tasks/reviews; UC revising → tasks pending-reset; spec active → predecessors superseded).
- `../scripts/refresh_implemented_by.py` — `usecase.implemented_by:` from `task.implements:`.
- `../scripts/register_research_citation.py` — spec ↔ research four-place atom (`research:`, `<research>`, `cited_by:`, `<cited-by>`).
- `../scripts/allocate_id.py` — global monotonic id allocator. Allocate via:
  ```bash
  uv run "../scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
  ```
- `../scripts/validate_frontmatter.py` / `../scripts/validate_body.py` — validators.
- `../scripts/drift_detector.py` — cross-file drift + close-guard re-surfacer.
