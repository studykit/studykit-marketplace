---
title: "a4 commit message convention"
status: final
created: 2026-04-27
updated: 2026-04-27
---

# a4 commit message convention

## Context

The a4 workspace is a git-native wiki + issue tracker rooted at `<project-root>/a4/`. Every artifact — `task/`, `review/`, `adr/`, `usecase/`, `idea/`, `spark/` — carries a globally monotonic `id:` allocated by `plugins/a4/scripts/allocate_id.py`. Skills (`/a4:roadmap`, `/a4:task`, `/a4:adr`, `/a4:usecase`, `/a4:domain`, `/a4:arch`, `/a4:run`, others) and the agent loop produce commits whose subject describes a change to one or more of these artifacts.

The current de facto practice follows Conventional Commits (`<type>(a4): <description>`) without any artifact reference in the subject. Examples from this repository's recent history:

- `refactor(a4)!: absorb dashboard skill into workspace-assistant agent`
- `feat(a4): add workspace-assistant agent for delegated find + status transition`
- `docs(a4): drop the justifies reverse-view name`

Reverse-mapping a commit to "which artifact this changed" requires opening the diff and reading paths. The full lifecycle of a single artifact (authored → implemented → integrated → ship-confirmed → revised) is not extractable via `git log` alone.

A subject-level reference also matters for `/a4:run`'s parallel task-implementer worktree model. Worktree branches are auto-named `worktree-agent-<random-hex>` by Claude Code; the branch name carries no artifact information, so the only durable artifact-to-commit mapping must live in the commit message itself.

GitHub-issue-style `#<id>` is widely understood, supports `git log --grep="#42"` directly, and composes naturally with Conventional Commits.

## Decision

Commits authored against an a4 workspace follow one of two forms:

**ID-bearing commit** — one or more a4 workspace IDs are associated with the change:

```
#<id1> [#<id2> ...] <type>(a4): <description>
```

- `<id>` is the workspace's global monotonic id, with no type prefix (the id model is type-agnostic; ids are unique across all artifact families).
- Multiple ids are separated by single spaces and appear together before the Conventional Commits type prefix.
- `<type>` is the existing Conventional Commits subset already in use (`feat`, `fix`, `docs`, `refactor`, `chore`, `test`) plus `merge` for `--no-ff` merge commits authored by `/a4:run`.

**ID-less commit** — change unrelated to any a4 artifact (build configuration, plugin source unrelated to a4, wiki edit without a triggering artifact):

```
<type>(a4): <description>
```

This is the existing form, retained unchanged.

### Examples

| Source | Form |
|---|---|
| `task-implementer` per-task commit | `#42 feat(a4): render markdown preview` |
| `/a4:run` `--no-ff` merge commit | `#42 merge(a4): integrate render-markdown-preview` |
| `/a4:task` single-task author | `#42 docs(a4): author task render-markdown-preview` |
| `/a4:task discard` | `#42 docs(a4): discard task render-markdown-preview` |
| `/a4:run` cycle results (multi-review) | `#57 #58 #59 chore(a4): cycle 2 test-runner findings` |
| `/a4:roadmap` initial UC + tasks | `#10 #41 #42 #43 docs(a4): roadmap for payment flow` |
| `/a4:adr` author | `#15 docs(a4): record retry strategy decision` |
| `/a4:usecase` author | `#10 docs(a4): author UC payment-checkout` |
| `/a4:idea` author | `#71 docs(a4): capture idea for retry budget` |
| Wiki edit, no triggering artifact | `docs(a4): clarify architecture overview` |
| Plugin source edit (unrelated to a4 workspace) | `chore(a4): bump validator pyproject deps` |

## Scope

The convention applies to commits authored by:

- a4 skills under `plugins/a4/skills/`
- a4 agents under `plugins/a4/agents/` (`task-implementer`, `test-runner`, others)
- Users editing a4 artifacts manually (review-item authoring, wiki edits triggered by a specific artifact, manual `transition_status.py` calls)

The convention does not apply to commits in other plugins, in repository infrastructure unrelated to a4, or in user projects whose work is unrelated to their `a4/` workspace.

## Options Considered

- **(i) Conventional Commits only** — keep `<type>(a4): ...`, no `#<id>`. Audit / bisect / blame across an artifact's lifecycle requires opening diffs. Rejected: poor `git log` discoverability.
- **(ii) `#<id>` only, drop type prefix** — e.g., `#42 render markdown preview`. Loses change-type signal; breaks tooling that depends on Conventional Commits. Rejected: unnecessary loss of an existing useful signal.
- **(iii) Type-prefixed ids** — e.g., `#task/42`, `#review/57`, `#adr/15`. Disambiguates artifact family at a glance. Rejected: a4 ids are globally monotonic so the type tag is redundant; the surrounding subject (`merge(a4): #42 ...`, `docs(a4): #15 record retry strategy decision`) makes family obvious in context.
- **(iv) ID at the end** — `<type>(a4): <description> (#<id>)`, GitHub-PR-link style. Rejected: less prominent in `git log --oneline`, and `git log --grep="^#"` no longer anchors at message start.
- **(v) ID in commit body trailer** — `Refs: #42` after a blank line. Standard in many projects. Rejected: requires multi-line subject inspection, weaker oneline discoverability, no ergonomic difference vs. (iv).

The chosen form (id at the start, type prefix preserved, no type tag on the id) optimizes for `git log --oneline` readability, `git log --grep` ergonomics, and preservation of Conventional Commits semantics.

## Consequences

- `git log --grep="#42"` returns every commit in artifact 42's lifecycle (authoring, implementation, integration, revision, ship-confirmation). This becomes the canonical entry point for audit / bisect / blame on an artifact.
- Existing skill SKILL.md `## Commit Points` sections that prescribe specific message forms must be updated to reference this convention. Notable known sites:
  - `plugins/a4/skills/run/SKILL.md` `Commit Points` block (UC ship-transition message `docs(a4): ship UC <ids>` becomes `#<id1> [#<id2> ...] docs(a4): ship UC <slugs>`).
  - `plugins/a4/skills/task/SKILL.md` `Commit Points` mentions a single commit covering author / refresh / sidecar; subject becomes `#<id> docs(a4): author task <slug>` or `#<id> docs(a4): discard task <slug>`.
  - Any other SKILL.md `Commit Points` that names a literal subject form.

  These are follow-up edits (one per skill) and are not part of this ADR's scope.
- The `merge` Conventional Commits type is a a4-specific extension, used only for `/a4:run`'s `--no-ff` merge commits that integrate a task-implementer worktree branch. Other types remain the standard set.
- Multi-id commits with many ids produce long subject lines (e.g., a roadmap of 30 tasks → 31 ids: 1 UC + 30 tasks). `git log --oneline` truncates per terminal width; this is acceptable since such commits are rare and the long form is recoverable via `git log --format=%s`.
- A commit-message validator is feasible (regex `^(#\d+ )*\w+(\(a4\))?[!]?:`) but is left out of scope for this ADR; introduce a `.githooks/commit-msg` check only after observed violations justify the friction.

## Open Questions

- Should very-large multi-id commits (>10 ids) move the id list to a body line (`Touches: #1 #2 ... #15`) and keep the subject short? Defer until the case appears in practice; the current form remains workable up to roughly 8 ids per `git log --oneline` width.
- Should the `merge` type be normalized to `chore(a4): merge task <slug>` or `feat(a4): <task description> (worktree merge)` instead of a custom type? Defer; `merge(a4)` reads clearly and survives any future tightening of allowed Conventional Commits types.
- Cross-workspace ID collision (a future scenario where multiple a4 workspaces' commit history is merged into one repository) is not addressed; treat it as a separate ADR if and when the case arises.
