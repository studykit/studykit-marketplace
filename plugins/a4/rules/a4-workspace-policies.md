---
name: a4-workspace-policies
description: Cross-cutting policy pointers for any file under `a4/`. Auto-loaded on every `a4/**/*.md` read.
paths: ["a4/**/*.md"]
---

# a4 — workspace policy index

These pointers apply to **every** file under `a4/`, regardless of type or location. Per-type rules (`a4-<type>-authoring.md`) build on these — they do not redefine them. The substance lives in `../authoring/` (frontmatter / body contracts) and `../workflows/` (cross-skill workflow contracts); this rule is the route in.

## When this rule applies — and when it does not

This index auto-loads on every `a4/**/*.md` open, including passive reads. **The required-reading list below applies only when you intend to author or modify the file** — i.e., the user has asked you to write a new a4 file, edit an existing one, change frontmatter, change status, or otherwise produce a write. **If the current task is read-only** (the user only asked you to read, summarize, search, quote, or answer questions about the file's content), **skip the required-reading step entirely** — do not pre-load `../authoring/*.md` files just because this rule fired. The auto-load of this pointer is sufficient context for read-only tasks.

If the task transitions from read-only to authoring mid-conversation (the user asks for an edit after a read), perform the required reading at that point, before the first write.

## Required reading before authoring or editing

Applies only when authoring or modifying an `a4/**/*.md` file (see the section above for read-only exemption). Read these **before** the first write. They are universal — per-type rules build on top, they do not replace these.

> **Important:** Auto-loading this `rules/` index does **not** satisfy the requirement. The files listed below live under `../authoring/` (a different directory from this `rules/` pointer). You **must** explicitly open each required file with the `Read` tool — do not assume that an auto-loaded `rules/a4-<type>-authoring.md` pointer file substitutes for the substance file at `../authoring/<type>-authoring.md`. The two are different files with different content; the `rules/` file is a pointer, the `authoring/` file is the contract.

- `../authoring/frontmatter-universals.md` — **MUST `Read` before the first write in an authoring or editing session.** Universal frontmatter contract: `type:` field, ids (and `../scripts/allocate_id.py`), path-reference format, dates, status writers, structural relationship fields.
- `../authoring/body-conventions.md` — **MUST `Read` before the first write in an authoring or editing session.** Body heading form, blank-line discipline, link form, frontmatter vs body path-reference form, `## Change Logs` / `## Log` rules, wiki update protocol.
- `../authoring/validator-rules.md` — **MUST `Read` before the first write in an authoring or editing session.** Schema enforcement and cross-file status consistency tables.
- `../authoring/<type>-authoring.md` — **MUST `Read` before the first write** of a file of that `type:` (e.g. `../authoring/task-authoring.md` for `type: task`). This is **not** the same file as the auto-loaded `rules/a4-<type>-authoring.md` pointer.

## Conditional reading

Read these when the situation applies.

- `../workflows/iterate-mechanics.md` — review-item walk procedure (filter, transition, close guard). Read when working a review-iterate flow.
- `../authoring/commit-message-convention.md` — `#<id>` commit subject form. Read when composing a commit that touches an a4 file.
