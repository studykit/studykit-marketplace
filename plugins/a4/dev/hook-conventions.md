# a4/ hook conventions

Design principles and policies for hooks under `../hooks/` and the
dispatcher `../scripts/a4_hook.py`.

This document is the authoritative source. The dispatcher's module docstring
and `hooks/README.md` reference this file rather than duplicating its
contents.

---

## 1. State classification

Every hook that writes to disk writes one of two kinds of state. The choice
determines the hook's lifecycle requirements (§2).

### Session-scoped state

State that exists only because a particular Claude session exists. It is
meaningless outside that session. Typical markers:

- Path or filename embeds `session_id`.
- Lives under `.claude/tmp/` (not tracked by git).
- Re-creatable from scratch on each new session.

Examples:

- `.claude/tmp/a4-edited/a4-edited-<session_id>.txt` — this session's
  list of edited `a4/*.md` files, consumed by the `stop` hook.
- `.claude/tmp/a4-edited/a4-prestatus-<session_id>.json` — pre-edit
  on-disk `status:` snapshot keyed by absolute path, populated by the
  `pre-edit` hook (PreToolUse) and consumed by `post-edit`
  (PostToolUse) to detect the precise pre→post transition before
  running cascades.
- `.claude/tmp/a4-edited/a4-injected-<session_id>.txt` — append-only
  list of `<file_path>\t<type>` lines recording which (file, type)
  pairs have already received an authoring-contract injection in this
  session. Populated and consulted by the `pre-edit` hook to dedupe
  injection (one-shot per pair per session).

### Permanent workspace state

State that is part of the project itself, independent of any session.
Typical markers:

- Lives under tracked project directories (e.g., `a4/`).
- Version-controlled (committed with the workspace).
- Must always be internally consistent, regardless of which session (if
  any) is active.

Example: spec `supersedes:` chains in `a4/spec/*.md` — when a successor
spec reaches `active`, every predecessor it lists must end up at
`superseded`. The chain must remain consistent regardless of which
session (if any) was active when the successor was authored.

### Discriminator

> After a fresh clone + new session, **does the state need to already
> exist**?
> - Yes → permanent (must be in git).
> - No → session-scoped (recreated or derived).

---

## 2. Lifecycle symmetry

Different symmetry requirements follow from the state classification in §1.

### Rule A — Session-scoped writes require a symmetric cleanup

A hook that writes session-scoped state MUST be paired with a cleanup
counterpart that runs when the session ends, plus a safety-net sweep that
handles crashed sessions where the cleanup never fired.

Concrete pattern (the "edit-record family" — reference implementation):

| Phase | Event | Hook action |
|-------|-------|-------------|
| Create | PostToolUse | Append edited path to `a4-edited-<sid>.txt` |
| Consume | Stop | Read file, validate each path |
| Cleanup | SessionEnd | Delete `a4-edited-<sid>.txt` for this session |
| Safety net | SessionStart | Sweep `a4-edited-*.txt` older than 1 day |

The `a4-injected-<sid>.txt` and `a4-prestatus-<sid>.json` files follow
the same pattern — appended/written by `pre-edit` (PreToolUse), read by
either `pre-edit` itself (dedupe lookup) or `post-edit`, deleted by the
SessionEnd cleanup hook with the SessionStart sweep as safety net.
Adding a new session-scoped file requires adding it to BOTH
`hooks/cleanup-edited-a4.sh` (explicit `rm -f` line) and
`hooks/sweep-old-edited-a4.sh` (find `-name` clause).

### Rule B — Permanent-state reconciliation writes require idempotency, not a counterpart

A hook that writes permanent workspace state (to restore/maintain an
invariant) does NOT need a SessionEnd/Stop counterpart. Instead it MUST be
**idempotent**: re-running on the post-run state yields no further changes.

Why no counterpart: the write is not a session effect to be undone. The
invariant it restores must hold regardless of whether any session is
active. Undoing it at SessionEnd would actively break the invariant.

Example: `validate.py --fix` recovers spec / UC supersedes chains for
edits that bypassed the live cascade hook. It is idempotent — a second
run on the same workspace produces no further changes. No SessionEnd
counterpart exists or is needed. (The historical
`refresh_implemented_by.py` SessionStart writer fit this shape too; it
was retired in a4 v6.0.0 along with the `usecase.implemented_by:`
field.)

---

## 3. Language and invocation

### Python via `uv run` for anything non-trivial

Any hook that parses stdin JSON, wraps another `scripts/*.py`, shapes
structured output (`additionalContext` / `systemMessage`), or implements
non-trivial logic goes in the Python dispatcher `scripts/a4_hook.py` and is
invoked as:

```
uv run "../scripts/a4_hook.py" <subcommand>
```

This matches the project-wide Python convention (`uv run`, not raw
`python`) and lets hook logic share modules with skills and with the
existing `scripts/` family.

### Bash for trivial filesystem ops

A hook that only performs language-independent filesystem manipulation
(`rm`, `find ... -delete`, `mkdir`) stays as a small standalone bash
script under `hooks/*.sh`. Rationale: Python + `uv run` startup cost
buys nothing for a one-line `rm`, and bash expresses these operations
natively.

Current examples: `hooks/cleanup-edited-a4.sh`, `hooks/sweep-old-edited-a4.sh`.

### Fast path inside the dispatcher

The dispatcher keeps top-level imports minimal. Each subcommand imports
what it needs locally. The `post-edit` subcommand (fires on every
Write/Edit/MultiEdit) benefits most; other subcommands benefit marginally
but follow the same pattern for consistency.

### In-process module imports for sibling scripts

Sibling `scripts/*.py` validators and reconcilers are called **in-process
via `import`**, not via nested `uv run` subprocesses. The dispatcher
prepends its own directory to `sys.path` and declares the combined
dependency set (currently `pyyaml>=6.0`) in its own PEP-723 header, so a
single `uv run` pays the interpreter/venv startup once per hook event
instead of once per script call. Standalone CLI use of the validator
(`uv run validate.py <a4-dir> [<file> ...] [--only ...]`) remains
supported in parallel — `validate.py` keeps its own PEP-723 header for
that path.

### Shared modules

Cross-script helpers live in two plain (non-runnable) modules next to the
scripts:

- `scripts/markdown.py` — canonical markdown parser. Exports `parse(path)
  -> Markdown`, `extract_preamble(path) -> Preamble`, `extract_body(path)
  -> Body`, and the dataclasses `Preamble(fm, raw)` / `Body(line_start,
  content)` / `Markdown(preamble, body)` / `Heading(level, text, line)`.
  `Body.extract_headings()` returns ATX headings, skipping fenced code
  blocks. All frontmatter/body parsing in a4 scripts routes through this
  module — do not reintroduce per-script `split_frontmatter` copies.
- `scripts/common.py` — workspace-level helpers that do not touch
  markdown: `ISSUE_FOLDERS`, `WIKI_TYPES`, `discover_files(a4_dir)`,
  `is_int`, `is_empty`, `is_non_empty_list`, `normalize_ref`.

Neither module carries a PEP-723 header (they are imported, never
executed). Any script that imports `markdown` must declare `pyyaml>=6.0`
in its own PEP-723 header so `uv run` provisions yaml into that script's
venv.

---

## 4. In-event ordering

When a single event in `hooks.json` has multiple entries, they are listed
in **write/cleanup → read/report** order:

- Cleanup and safety-net operations run first so later entries see a
  clean state.
- Reconciliation writes that restore invariants run next so reports
  describe the *post-reconciliation* state.
- Read-only reports run last.

SessionStart currently has two entries, ordered per the rule above:
1. `sweep-old-edited-a4.sh` — safety-net cleanup (bash) for orphan
   `a4-edited-*` record files older than 1 day.
2. `a4_hook.py session-start` — read-only injection of the type →
   file-location map (`a4/<type>/<id>-<slug>.md` for issue families,
   `a4/<type>.md` for wiki pages) as `additionalContext`. Built from
   `common.WIKI_TYPES` / `common.ISSUE_FOLDERS`; silent when the project
   has no `a4/` directory.

When new SessionStart hooks are added, place them according to the rule
above (cleanup → reconciliation → read-only reports); if the rule is
ambiguous, extend this section rather than improvising.

---

## 5. Non-blocking policy

| Event | Blocking behavior |
|-------|-------------------|
| PostToolUse | Always exit 0. Never blocks an edit. |
| SessionStart | Always exit 0. Never blocks session entry. |
| SessionEnd | Always exit 0. Never blocks session termination. |
| Stop | On validation violations, emit JSON `{"decision": "block", "reason": ...}` on stdout (exit 0) — Claude Code surfaces the `reason` verbatim and forces Claude retry, *without* the `[command]: ` harness prefix that wraps stderr-on-rc=2 output. Exit 0 on clean result **and on any internal failure** (missing env, missing scripts, subprocess error). |

Internal failures — configuration errors, subprocess crashes, JSON parse
errors, timeouts — are never allowed to propagate as blocking failures.
They are either silent (Post/Session events) or logged to stderr with
exit 0 (Stop event) so hook bugs cannot strand the user.

The Stop event historically used `exit 2 + stderr` to signal violations.
Claude Code wraps that channel as `[<command>]: <stderr>`, which leaks
the literal `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/a4_hook.py" stop`
prefix into the conversation. The JSON `decision: block` route avoids
the prefix while preserving the retry semantics — see
`../scripts/a4_hook.py::_stop`.

---

## 6. Output channels

Claude Code recognizes two output channels in a SessionStart / PreToolUse /
PostToolUse hook's JSON payload:

- **`hookSpecificOutput.additionalContext`** — markdown-structured,
  verbose. Injected into the LLM's context. Use for full diagnostics
  (per-file diffs, rule explanations, error lists).
- **`systemMessage`** (top-level) — short, user-facing. Rendered above the
  prompt as
  `<Event>:<hook-name> says: <systemMessage>`.
  Use for a one-line summary of actionable news.

### Usage rule

- **Both channels together** when a hook affects workspace state the user
  should be aware of. The live example is the `post-edit` cascade
  hook: when a legal `status:` transition fires a cross-file cascade,
  it emits `systemMessage = "a4 cascade: <from> → <to> on <path>
  flipped N related file(s)"` for the user-facing one-liner, and
  `additionalContext` carrying the per-file flip table for the LLM.
  Silent on cosmetic edits (no transition) and on illegal jumps (which
  the Stop-hook safety net surfaces instead). The companion
  `updated:` auto-bump (see §8) is intentionally silent on both
  channels — it is a routine maintenance write, not actionable news.
- **`additionalContext` only** for informational reports where no
  user-visible notice is warranted (e.g., the PostToolUse status-
  consistency report — inline context for the LLM, no pop-up needed;
  and the PreToolUse authoring-contract injection — pointer-only
  reminder before an edit, no user-facing news).
- **`systemMessage` only** for short announcements with no LLM-relevant
  detail. Rare; none currently.
- **Neither (silent)** when the hook has nothing meaningful to report
  (silent-on-clean convention; see §7).

Note: the official documentation has historically understated that
`systemMessage` works on SessionStart. It does — empirically verified.

### PreToolUse authoring-contract injection

The `pre-edit` hook injects a pointer-style `additionalContext` block on
the first Write/Edit/MultiEdit of an `a4/*.md` file in a session, naming
the matching `authoring/` contracts for the file's `type:`. The hook is
the single mechanism that surfaces authoring contracts to the LLM at
edit time — pure reads do not pull the contract in.

Design choices:

- **Lazy.** Triggers on PreToolUse, not file open. Pure reads no longer
  pull in the contract.
- **Pointer-only.** The injection lists pointer paths and a short
  rationale; full contract bodies are not inlined. The LLM is expected
  to `Read` the listed files when it actually needs them. Inlining
  bodies is wasteful (cache miss + token bloat) and weaker than a
  direct `Read` (no line numbers, no in-file navigation).
- **Per-(file, type) dedupe.** A second edit to the same file in the
  same session emits nothing. `type:` change re-triggers injection
  because the contract changed.
- **Path-based type resolution.** `type:` is resolved from path
  (`common.WIKI_TYPES` for top-level wiki pages, `common.ISSUE_FOLDERS`
  for `<folder>/<id>-<slug>.md`), not by parsing frontmatter — the a4
  layout pins type by location, so the parse would be wasted IO.
- **Archive skipped.** Files under `a4/archive/` inject nothing —
  archived files retain their original type but are not active edit
  targets.
- **Silent on miss.** Unrecognized layouts or missing
  `authoring/<type>-authoring.md` inject nothing.
- **Edit only — never blocks.** PreToolUse exits 0; the contract is a
  hint, not a gate. Schema enforcement remains the Stop-hook
  responsibility (`markdown_validator`).

---

## 7. Silent-on-clean convention

A hook that finds no drift, no violation, no actionable signal emits
nothing — no heartbeat, no "ran successfully" line, no trailing whitespace.
Session entry and edit flows are high-attention moments; reserve any
visible output for news the user can act on.

Internal failures covered by §5 also emit nothing user-facing (Post/Session
events) or a short stderr line that does not block (Stop event — internal
failures still use stderr + rc=0 since they aren't surfaced through the
`decision: block` channel).

---

## 8. PostToolUse `updated:` auto-bump

The `post-edit` hook owns `updated:` on every a4/*.md edit. Authors and
skill runtimes never hand-bump the field; the hook unconditionally
rewrites it to the current KST timestamp on every Write/Edit/MultiEdit
of an `a4/*.md` file. This collapses the previous "status flips →
cascade refreshes; everything else → author bumps" split into a single
hook responsibility.

Driver order in `_post_edit` (consult `../scripts/a4_hook.py:_post_edit`
for the canonical sequence):

1. Compute `today = now_kst()` once and pass it through every step so
   `created` and `updated` end up identical on a fresh Write, and so
   two writes within the same minute can't drift across step
   boundaries.
2. `_maybe_stamp_created` — stamps `created: today` on a new-file
   Write whose schema requires it. Overwrites any pre-populated
   `created:` value the LLM wrote (`created:` is hook-owned per
   `../authoring/frontmatter-common.md`; backdating is not supported).
   Once stamped, immutable on subsequent Edits — this driver only
   fires on first Write (PreToolUse-recorded new file).
3. `_run_status_change_cascade` — runs the cascade engine on a legal
   `status:` transition, which calls `apply_status_change` on the
   primary (refreshing `updated:` there) and on every cascaded
   related file. Returns a bool: True iff `apply_status_change` ran on
   the primary.
4. `_refresh_updated_on_primary` — runs iff step 3 returned False
   (no transition, illegal transition, or family outside
   `FAMILY_TRANSITIONS`). Rewrites `updated:` on the primary alone;
   cascaded files are already covered by step 3.
5. `_report_status_consistency_post` — read-only.

Dedupe rationale: the cascade and the auto-bump both write `updated:`,
but the bool return from step 3 ensures each file is rewritten at
most once per edit event. Step 4's `_refresh_updated_on_primary` skips
silently when the file's `type:` cannot be resolved by path (archive
files, unrecognized layout) — those files are out of the workspace
contract.

Recovery for edits that bypass the hook (manual `git checkout`,
external editors): re-save the file through Claude Code, or run
`../scripts/validate.py --fix` for the supersedes-chain recovery sweep
(which does not currently bump `updated:` on the primary; that path
is explicitly only invoked when the live cascade hook missed). The
non-status `updated:` drift is benign — the validator does not gate on
it — so no separate sweep exists.

Output channel: silent on both `additionalContext` and `systemMessage`
(per §6) — auto-bump is routine maintenance, not actionable news. The
cascade path keeps its own `additionalContext + systemMessage` pair for
the cross-file flip summary.

---

## Non-goals

- **Unified language.** Bash hooks persist for trivial cases (§3). Forcing
  Python everywhere would add `uv run` startup cost with no corresponding
  benefit.
- **Per-subtask timeout granularity in `hooks.json`.** Event-level timeout
  is the unit; subtask-level budgeting (if needed) happens inside the
  dispatcher via `subprocess.run(..., timeout=...)`.
- **Rollback of reconciliation writes.** See §2 Rule B — reconciliation is
  invariant maintenance, not a session-scoped effect.
