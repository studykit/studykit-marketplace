---
name: a4-workspace-policies
description: Cross-cutting policy pointers for any file under `a4/`. Auto-loaded on every `a4/**/*.md` read.
paths: ["a4/**/*.md"]
---

# a4 — workspace policy index

These pointers apply to **every** file under `a4/`, regardless of type or location. Per-type rules (`a4-<type>-authoring.md`) build on these — they do not redefine them. The substance lives in [`../authoring/`](../references); this rule is the route in.

## Cross-cutting contracts

- `../authoring/frontmatter-universals.md` — universal frontmatter contract: `type:` field, ids, path-reference format, dates, status writers, structural relationship fields.
- `../authoring/<type>-authoring.md` — per-type field tables and lifecycles (one file per `type:` value).
- `../authoring/validator-rules.md` — schema enforcement and cross-file status consistency tables.
- `../authoring/body-conventions.md` — body heading form, blank-line discipline, link form, frontmatter vs body path-reference form, `## Change Logs` / `## Log` rules, wiki update protocol.
- `../dev/iterate-mechanics.md` — review-item walk procedure (filter, transition, close guard).
- `../authoring/commit-message-convention.md` — `#<id>` commit subject form.
