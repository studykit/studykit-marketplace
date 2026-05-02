# a4 cascade & validator internals

Implementation jump-table for the status cascade engine, the cascade hook, the recovery sweep, and the validator. Maps the contracts described in `../authoring/frontmatter-common.md` (universal rules including status changes and cascades and title placeholders) and the per-type lifecycles in `../authoring/<type>-authoring.md` to the modules that enforce them.

## Cascade engine

- **Status model (canonical):** `../scripts/status_model.py` — per-family status enums, allowed transitions (`FAMILY_TRANSITIONS`), terminal / in-progress / active classifications, supersedes-trigger maps, cascade input sets, legality predicates. Imported by every other cascade-aware module.
- **Cascade engine:** `../scripts/status_cascade.py` — supersedes / discarded / revising cascade primitives shared by the PostToolUse cascade hook and the `/a4:validate --fix` recovery sweep.
- **Cascade hook:** `../scripts/a4_hook.py` — PostToolUse hook entry point; detects pre→post `status:` transitions, refreshes `updated:` on the primary file, runs cascades on related files. Reads pre-edit `status:` snapshot from `.claude/tmp/a4-edited/a4-prestatus-<sid>.json`.
- **Recovery sweep:** `../scripts/validate.py --fix` — supersedes-chain idempotent sweep for edits that bypassed the hook (manual `git checkout`, external editors, direct script writes). Walks live successors and reconciles `superseded` flips workspace-wide. Surfaced to users as the `/a4:validate --fix` skill command.

## Validator

- **Validator entrypoint:** `../scripts/validate.py` — unified CLI; runs every check registered in `markdown_validator.registry.CHECKS`. Surfaced to users as the `/a4:validate` skill.
- **Frontmatter validator:** `../scripts/markdown_validator/frontmatter.py` — required fields, enums, types, path-reference format, id uniqueness, post-draft authoring invariants.
- **Status consistency checker:** `../scripts/markdown_validator/status_consistency.py` — cross-file status drift checks (supersedes-chain, discarded / revising cascades, idea / brainstorm `promoted:` consistency). Cascade behavior is contracted in `../authoring/frontmatter-issue.md` § Status changes and cascades and the per-type lifecycles in `../authoring/<type>-authoring.md`.
- **Transition legality safety net:** `../scripts/markdown_validator/transitions.py` — Stop-hook git-diff check that rejects `status:` jumps outside `FAMILY_TRANSITIONS`. Catches illegal direct `status:` edits the cascade hook silently ignored.

## Hook flow

See `./hook-conventions.md` for the design principles (state classification, lifecycle symmetry, in-event ordering, blocking vs non-blocking policy, output channels).

The four hook flows in `../hooks/hooks.json` all dispatch through `../scripts/a4_hook.py` subcommands:

- `pre-edit` (PreToolUse) — stash on-disk `status:` of the file about to be edited.
- `post-edit` (PostToolUse) — record the edit, run the status-change cascade if pre→post is a legal transition, refresh `updated:`, report per-component status-consistency on the post-cascade state.
- `stop` (Stop) — frontmatter schema checks AND transition-legality safety net (HEAD-vs-working-tree git diff against `FAMILY_TRANSITIONS`) on session-edited files.
- `user-prompt` (UserPromptSubmit) — resolve `#<id>` references in the prompt to `a4/<type>/<id>-<slug>.md` paths and inject them as `additionalContext`.

Two thin shell wrappers in `../hooks/` (`cleanup-edited-a4.sh`, `sweep-old-edited-a4.sh`) handle SessionStart/SessionEnd file housekeeping for `.claude/tmp/a4-edited/` only.

## Allocator

- **Id allocator:** `../scripts/allocate_id.py` — workspace-global, monotonic id allocation. Computes `max(existing ids in a4/) + 1`. Skills invoke it before writing any new issue file. Wiki pages do not carry an `id:`.
