# a4 Commit Message Convention

Subject form for every commit derived from an a4 workspace artifact. A commit is "derived" if it edits an artifact file (authoring, status flip, body revision) **or** carries work that traces back to an artifact (per-task implementation, per-issue fix, per-UC ship work). Commits with no artifact in scope but still touching the workspace (wiki polish, workspace meta) are ID-less. Edits inside `plugins/a4/` itself, and project work unrelated to the workspace, are outside this convention.

## Forms

**ID-bearing** — the commit is derived from one or more workspace artifacts:

```
#<id1> [#<id2> ...] <type>(a4): <description>
```

**ID-less** — no a4 artifact drives the commit (wiki polish without a triggering item, workspace meta-edits with no associated artifact):

```
<type>(a4): <description>
```

## Rules

- A commit is "derived" from an artifact if it edits the artifact file **or** the work it carries traces back to that artifact (per-task implementation, per-issue fix, per-UC ship work). Heuristic: *"does this commit advance the lifecycle of artifact #N?"* — if yes, prefix `#N`. The artifact file does not need to be in the diff.
- `<id>` is the artifact file's frontmatter `id:` value (already allocated at file-creation time — see `./frontmatter-universals.md` §Ids). No type prefix on the id (ids are unique across all artifact families).
- Multiple ids are space-separated and appear together before the Conventional Commits type prefix. Order them by relevance (the artifact most directly driving the commit first).
- `<type>` ∈ `feat | fix | docs | refactor | chore | test | merge`.
- `merge(a4)` is a4-specific, used only for `--no-ff` integration commits that fold a worktree branch into local main during the implement loop.

## Examples

| Source | Form |
|---|---|
| Per-task implementation commit (code change, no a4 file edited) | `#42 feat(a4): render markdown preview` |
| Per-task fix / refactor commit (code only) | `#42 fix(a4): handle empty preview path` |
| Bug fix landing for a logged issue (code only) | `#88 fix(a4): correct cascade flip on retract` |
| `--no-ff` merge commit (worktree → main) | `#42 merge(a4): integrate render-markdown-preview` |
| Single task author / discard | `#42 docs(a4): author task render-markdown-preview` |
| Cycle test-runner findings (multi-review) | `#57 #58 #59 chore(a4): cycle 2 test-runner findings` |
| Breakdown — task batch derivation | `#41 #42 #43 docs(a4): derive tasks for payment flow` |
| UC ship-transition | `#10 #11 docs(a4): ship UC payment-checkout payment-refund` |
| Spec author | `#15 docs(a4): record retry strategy decision` |
| Wiki edit, no triggering artifact | `docs(a4): clarify architecture overview` |

## Why

`git log --grep="#42"` should return the full lifecycle of artifact 42 — authoring → implementation → integration → ship → revision — across both a4 file edits and the code commits those artifacts drove. That lifecycle thread only stays intact if id-prefixing keys off **derivation**, not file-touch: per-task implementation commits typically edit project code only, and would silently drop out of the thread under a file-touch trigger. When worktree branches are auto-named `worktree-agent-<hex>` with no artifact information, the merge commit's `#<id>` prefix is the only durable task→branch mapping in history.
