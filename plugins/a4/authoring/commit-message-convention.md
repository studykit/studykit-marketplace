# a4 Commit Message Convention

Subject form for commits derived from an a4 workspace artifact (see Rules for "derived"). Commits touching the workspace without a triggering artifact (wiki polish, workspace meta) are ID-less. Out of scope: edits inside `plugins/a4/` itself, and project work unrelated to the workspace.

## Forms

```
#<id1> [#<id2> ...] <type>(a4): <description>   # derived from artifacts
<type>(a4): <description>                        # no artifact in scope
```

## Rules

- **Derived** = edits the artifact file *or* carries work tracing back to it (per-task implementation, per-issue fix, per-UC ship work). Heuristic: *"does this commit advance the lifecycle of artifact #N?"* The artifact file need not be in the diff.
- `<id>` is the frontmatter `id:` value (allocated at file creation — see `./frontmatter-issue.md` § `id`). No type prefix; ids are globally unique.
- Multiple ids are space-separated, ordered by relevance (most directly driving first).
- `<type>` follows Conventional Commits, plus a4-specific `merge(a4)` — reserved for `--no-ff` worktree → main integration commits.

## Examples

| Source | Form |
|---|---|
| Per-task code commit (no a4 file edited) | `#42 feat(a4): render markdown preview` |
| `--no-ff` merge (worktree → main) | `#42 merge(a4): integrate render-markdown-preview` |
| Single artifact author | `#42 docs(a4): author task render-markdown-preview` |
| Multi-review cycle findings | `#57 #58 #59 chore(a4): cycle 2 test findings` |
| Task batch derivation | `#41 #42 #43 docs(a4): derive tasks for payment flow` |
| UC ship-transition | `#10 #11 docs(a4): ship UC payment-checkout payment-refund` |
| Wiki edit, no triggering artifact | `docs(a4): clarify architecture overview` |

## Why

`git log --grep="#42"` should return artifact 42's full lifecycle (authoring → implementation → integration → ship → revision). That thread only stays intact if id-prefixing keys off **derivation**, not file-touch — per-task implementation commits typically touch project code only and would drop out under a file-touch trigger. With generated worktree branches, the merge commit's `#<id>` is the only durable task→branch mapping.
