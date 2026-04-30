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

SessionStart currently has only one entry — `sweep-old-edited-a4.sh`,
the safety-net cleanup (bash). When new SessionStart hooks are added,
place them according to the rule above (cleanup → reconciliation →
read-only reports); if the rule is ambiguous, extend this section
rather than improvising.

---

## 5. Non-blocking policy

| Event | Blocking behavior |
|-------|-------------------|
| PostToolUse | Always exit 0. Never blocks an edit. |
| SessionStart | Always exit 0. Never blocks session entry. |
| SessionEnd | Always exit 0. Never blocks session termination. |
| Stop | Exit 2 on validation violations (forces Claude retry). Exit 0 on clean result **and on any internal failure** (missing env, missing scripts, subprocess error). |

Internal failures — configuration errors, subprocess crashes, JSON parse
errors, timeouts — are never allowed to propagate as blocking failures.
They are either silent (Post/Session events) or logged to stderr with
exit 0 (Stop event) so hook bugs cannot strand the user.

---

## 6. Output channels

Claude Code recognizes two output channels in a SessionStart / PostToolUse
hook's JSON payload:

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
  the Stop-hook safety net surfaces instead).
- **`additionalContext` only** for informational reports where no
  user-visible notice is warranted (e.g., the PostToolUse status-
  consistency report — inline context for the LLM, no pop-up needed).
- **`systemMessage` only** for short announcements with no LLM-relevant
  detail. Rare; none currently.
- **Neither (silent)** when the hook has nothing meaningful to report
  (silent-on-clean convention; see §7).

Note: the official documentation has historically understated that
`systemMessage` works on SessionStart. It does — empirically verified.

---

## 7. Silent-on-clean convention

A hook that finds no drift, no violation, no actionable signal emits
nothing — no heartbeat, no "ran successfully" line, no trailing whitespace.
Session entry and edit flows are high-attention moments; reserve any
visible output for news the user can act on.

Internal failures covered by §5 also emit nothing user-facing (Post/Session
events) or a short stderr line that does not block (Stop event).

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
