# a4 Commit Message Convention

> **Audience:** Workspace authors writing `<project-root>/a4/**/*.md` files (or LLMs editing them on the user's behalf). Not for a4 plugin contributors — implementation references live in `../dev/`.

Subject form for every commit authored against an a4 workspace. Applies to any commit touching `a4/` artifacts. Does not apply to other plugins or to user-project work unrelated to `a4/`.

## Forms

**ID-bearing** — one or more workspace ids touched:

```
#<id1> [#<id2> ...] <type>(a4): <description>
```

**ID-less** — no a4 artifact touched (plugin meta-edits, build config, wiki edits without a triggering item):

```
<type>(a4): <description>
```

## Rules

- `<id>` is the global monotonic id allocated by `scripts/allocate_id.py`. No type prefix on the id (ids are unique across all artifact families).
- Multiple ids are space-separated and appear together before the Conventional Commits type prefix.
- `<type>` ∈ `feat | fix | docs | refactor | chore | test | merge`.
- `merge(a4)` is a4-specific, used only for `--no-ff` integration commits that fold a worktree branch into local main during the implement loop.

## Examples

| Source | Form |
|---|---|
| Per-task implementation commit | `#42 feat(a4): render markdown preview` |
| `--no-ff` merge commit (worktree → main) | `#42 merge(a4): integrate render-markdown-preview` |
| Single task author / discard | `#42 docs(a4): author task render-markdown-preview` |
| Cycle test-runner findings (multi-review) | `#57 #58 #59 chore(a4): cycle 2 test-runner findings` |
| Roadmap initial UC + tasks | `#10 #41 #42 #43 docs(a4): roadmap for payment flow` |
| UC ship-transition | `#10 #11 docs(a4): ship UC payment-checkout payment-refund` |
| Spec author | `#15 docs(a4): record retry strategy decision` |
| Wiki edit, no triggering artifact | `docs(a4): clarify architecture overview` |
| Plugin source edit unrelated to a4 workspace | `chore(a4): bump validator pyproject deps` |

## Why

`git log --grep="#42"` returns the full lifecycle of artifact 42 (authoring → implementation → integration → ship → revision). When worktree branches are auto-named `worktree-agent-<hex>` with no artifact information, the merge commit's `#<id>` prefix is the only durable task→branch mapping in history.
