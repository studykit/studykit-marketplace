---
name: a4-workspace-policies
description: Cross-cutting policy pointers for any file under `a4/`. Auto-loaded on every `a4/**/*.md` read.
paths: ["a4/**/*.md"]
---

# a4 — workspace policy index

These pointers apply to **every** file under `a4/`, regardless of type or location. Per-type rules (`a4-<type>-authoring.md`) build on these — they do not redefine them. The substance lives in [`../references/`](../references); this rule is the route in.

## Cross-cutting contracts

- `../references/frontmatter-schema.md` — full field schema, lifecycle tables, validator behavior, writer-owned fields.
- `../references/body-conventions.md` — body heading form, blank-line discipline, link form, frontmatter vs body path-reference form, `## Change Logs` / `## Log` rules, wiki update protocol.
- `../docs/iterate-mechanics.md` — review-item walk procedure (filter, transition, close guard).
- `../references/commit-message-convention.md` — `#<id>` commit subject form.
