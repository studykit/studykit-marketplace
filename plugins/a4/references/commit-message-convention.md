# a4 Commit Message Convention

Subject form for every commit authored against an a4 workspace. Applies to a4 skills, a4 agents (`task-implementer`, `test-runner`, etc.), and users editing a4 artifacts manually. Does not apply to other plugins or to user-project work unrelated to `a4/`.

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
- `merge(a4)` is a4-specific, used only for `/a4:run`'s `--no-ff` integration commits that fold a `task-implementer` worktree branch into local main.

## Examples

| Source | Form |
|---|---|
| `task-implementer` per-task commit | `#42 feat(a4): render markdown preview` |
| `/a4:run` `--no-ff` merge commit | `#42 merge(a4): integrate render-markdown-preview` |
| `/a4:task` author / discard | `#42 docs(a4): author task render-markdown-preview` |
| `/a4:run` cycle results (multi-review) | `#57 #58 #59 chore(a4): cycle 2 test-runner findings` |
| `/a4:roadmap` initial UC + tasks | `#10 #41 #42 #43 docs(a4): roadmap for payment flow` |
| `/a4:run` UC ship-transition | `#10 #11 docs(a4): ship UC payment-checkout payment-refund` |
| `/a4:spec` author | `#15 docs(a4): record retry strategy decision` |
| Wiki edit, no triggering artifact | `docs(a4): clarify architecture overview` |
| Plugin source edit unrelated to a4 workspace | `chore(a4): bump validator pyproject deps` |

## Why

`git log --grep="#42"` returns the full lifecycle of artifact 42 (authoring → implementation → integration → ship → revision). For `/a4:run`, where worktree branches are auto-named `worktree-agent-<hex>` with no artifact information, the merge commit's `#<id>` prefix is the only durable task→branch mapping in history.
