---
timestamp: 2026-04-25_0350
topic: a4-hook-automation
previous: 2026-04-25_0301_dispatcher-in-process-imports.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_0350. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

Executed the scripts-modularization task the previous handoff handed off. Chose **Option A.a + Shim** from that handoff's menu: `plugins/a4/scripts/` becomes the Python package itself (add `__init__.py`, add `common.py`); no directory rename; no file moves; all 42 external `uv run scripts/<name>.py` call sites across 23 caller files continue to work verbatim.

Scope was deliberately **first-half**. Three commits landed, shared helpers and one major structural refactor (`split_frontmatter` unification) are done. Eight sibling scripts are still untouched. See [§What's left](#whats-left) for the precise punch list.

Thread topic `a4-hook-automation` retained — the previous handoff framed modularization as the continuation of this thread.

# What shipped this session

Three commits on top of `0fe5a71dd` (the last commit from the previous handoff):

| SHA | Plugin version | Focus |
|---|---|---|
| `d985315a3` | a4 1.13.1 → 1.13.2 | Zero-risk helper extraction to `common.py` |
| `d548d1585` | a4 1.13.2 → 1.13.3 | `split_frontmatter` unified on `ParsedMarkdown` dataclass |
| `6c4588836` | a4 1.13.3 → **1.14.0** | `ISSUE_FOLDERS` aligned; `validate_body` now covers `idea/` |

## Commit 1 (`d985315a3`) — shared helper extraction

Created two new files:

- **`plugins/a4/scripts/__init__.py`** — empty; marks the directory as a Python package. Not functionally required (sibling imports work without it because `uv run <script>.py` adds the script's dir to `sys.path[0]` automatically), but makes the package status explicit.
- **`plugins/a4/scripts/common.py`** — first round of shared helpers. See [§common.py inventory](#commonpy-inventory-after-commit-3).

Removed verbatim duplicates of five items from four callers (`validate_frontmatter.py`, `validate_body.py`, `validate_status_consistency.py`, `refresh_implemented_by.py`): `WIKI_KINDS`, `is_int`, `is_empty`, `is_non_empty_list`, `normalize_ref`. Each caller now imports from `common`; private underscore aliases preserved where they existed (e.g., `is_int as _is_int`). Dropped `from typing import Any` where it became unused.

No signature changes. Dispatcher (`a4_hook.py`) untouched. Byte-for-byte output preservation verified against a smoke-test fixture — see [§Verification approach](#verification-approach).

## Commit 2 (`d548d1585`) — `split_frontmatter` canonicalization

The biggest change. Four scripts previously carried incompatible local `split_frontmatter` implementations with four different return shapes:

- `validate_frontmatter.py` → `(fm, body)`
- `validate_body.py` → `(fm, body, body_start_line)`
- `validate_status_consistency.py` → `fm` (bare)
- `refresh_implemented_by.py` → `(fm, raw_fm, body)` with a subtly different line-boundary algorithm

The dispatcher also called `vfm.split_frontmatter(path)` expecting the 2-tuple form — so consolidation required **atomic co-updates across the dispatcher + all four scripts**.

**New canonical API in `common.py`:**

```python
@dataclass(frozen=True)
class ParsedMarkdown:
    fm: dict | None          # None if absent/malformed/not-a-mapping
    raw_fm: str              # text between fences, no wrapping newlines
    body: str                # post-fence text, leading newline preserved
    body_start_line: int     # 1-based line in source where body begins


def split_frontmatter(path: Path) -> ParsedMarkdown: ...
```

**Canonical algorithm**: line-boundary `\n---` detection (the stricter of the two prior algorithms, taken from the old `refresh_implemented_by`). A stray `---` inside a body cannot confuse the split. Empty frontmatter (`---\n---\n...`) is handled explicitly.

**Class name: `ParsedMarkdown`, not `FrontmatterParts`.** The user caught mid-session that `FrontmatterParts` violates single-responsibility naming (it carries body + body_start_line, which are not parts of frontmatter). `ParsedMarkdown` accurately names "a parsed markdown document with YAML frontmatter."

**Dispatcher updated** to call `parsed = vfm.split_frontmatter(path); fm = parsed.fm` instead of tuple-unpacking. `vfm.split_frontmatter` still works — it's re-exported from `common` via `from common import split_frontmatter` in `validate_frontmatter.py`.

**Thin back-compat wrappers** in two scripts to avoid rewriting many internal call sites:
- `validate_status_consistency.split_frontmatter(path) -> dict | None` — returns `parsed.fm` only.
- `refresh_implemented_by.split_frontmatter(path) -> tuple[dict | None, str, str]` — returns `(fm, raw_fm, body)` from `ParsedMarkdown`.

Both are 1–2 line shims. Can be inlined in a future pass; kept for now to minimize diff.

### Two deliberate edge-case behavior adjustments (commit message documents both)

1. **Empty frontmatter block** (`---\n---\nbody`) now uniformly returns `fm=None` across every consumer. Previously `refresh_implemented_by` alone treated this as `fm={}` and would silently write `implemented_by:` into such files. It now reports `"{path}: unreadable frontmatter"` instead. Safer — an empty-fm UC is malformed by schema.

2. **`validate_body`'s line-number off-by-one is preserved verbatim**, not fixed. Current behavior: a broken wikilink on file line `N` is reported as `file:N+1`. Root cause: `body` retains a leading `\n` (the newline after the closing fence), which makes `body.splitlines()` emit a spurious empty string at index 0 that skews the `body_start_line + i` arithmetic. Canonical algorithm reproduces this verbatim because the user explicitly asked for no quiet bug fixes. See [§The validate_body off-by-one](#the-validate_body-off-by-one) for the fix path.

## Commit 3 (`6c4588836`) — `ISSUE_FOLDERS` alignment

`validate_body.py` previously declared a 4-tuple `ISSUE_FOLDERS = ("usecase", "task", "review", "decision")` missing `"idea"`. Every other consumer used the 5-tuple. Net effect: body-level rules (notably `wikilink-broken`) silently skipped `idea/*.md` files.

**Unified on the 5-tuple in `common.py`.** `validate_body` now classifies idea files as `"issue"` in `classify_file()` and runs the body wikilink sweep on them. The byte-identical `discover_files()` helper, previously duplicated between the two validators, moved to `common.py` in the same commit.

**Observable behavior change**: body violations in `idea/*.md` are now reported. Verified with a fixture containing `idea/21-wikilink.md` referencing `[[nonexistent-task]]` — commits 1–2 missed this entirely; commit 3 reports `idea/21-wikilink.md:10 (wikilink-broken)` both via `/a4:validate` and the Stop hook. Non-idea files produce byte-identical output to all prior commits.

Minor version bump (`1.13.3 → 1.14.0`) to flag the user-visible validator behavior extension.

# common.py inventory (after commit 3)

Complete surface of the new module at session end:

| Symbol | Kind | Used by |
|---|---|---|
| `WIKI_KINDS` | frozenset | validate_frontmatter, validate_body |
| `ISSUE_FOLDERS` | `tuple[str, ...]` | validate_frontmatter, validate_body |
| `is_int(value)` | helper | validate_frontmatter |
| `is_empty(value)` | helper | validate_frontmatter |
| `is_non_empty_list(value)` | helper | validate_status_consistency |
| `normalize_ref(ref)` | helper | validate_status_consistency, refresh_implemented_by |
| `ParsedMarkdown` | frozen dataclass | all four scripts + dispatcher (indirectly) |
| `split_frontmatter(path)` | function | all four scripts + dispatcher (indirectly) |
| `discover_files(a4_dir)` | function | validate_frontmatter, validate_body |

`common.py` has no PEP-723 header (it is not runnable standalone). It imports `yaml`. Every script that imports `common` must declare `pyyaml>=6.0` in its own PEP-723 header so `uv run` provisions yaml into that script's venv. All four scripts already do.

# What's left

## Remaining within the scripts-modularization thread

**None of the eight other scripts in `plugins/a4/scripts/` have been touched yet** by this refactor. Listed in decreasing order of expected common-helper overlap:

| Script | External `uv run` call sites | Expected overlap with common |
|---|---|---|
| `transition_status.py` | 12 | Likely its own `split_frontmatter` variant (needs raw_fm for rewrites) + ISSUE_FOLDERS + normalize_ref + some discovery |
| `allocate_id.py` | 15 | ISSUE_FOLDERS + frontmatter parsing (only needs `id`) |
| `index_refresh.py` | 3 | ISSUE_FOLDERS + frontmatter parsing + discovery; declares `TERMINAL_STATUSES` that may be shareable |
| `drift_detector.py` | 3 | Frontmatter parsing + discovery |
| `inject_includes.py` | 1 | Probably minimal overlap |
| `read_frontmatter.py` | 0 | Almost certainly a thin `yaml.safe_load` wrapper — prime candidate to delete if `split_frontmatter` subsumes it |
| `extract_section.py` | 0 | Probably self-contained |
| `a4_hook.py` | N/A (dispatcher) | Already uses common transitively via sibling imports; can't leverage common more without restructuring |

**Recommended next-commit shape**: pick one or two of the high-overlap scripts (`transition_status`, `allocate_id`, `index_refresh`), survey their helpers, and extract the duplicates. Do not attempt all 8 in one commit — each needs its own verification step because the callers across skills/agents expect specific CLI output shapes.

## Optional follow-up: fix `validate_body`'s off-by-one

Deliberately preserved in this session per the "no quiet bug fixes" rule. Standalone commit. Scope:

1. Change `common.split_frontmatter` so `body` does NOT retain the leading newline from the closing fence. Change `body_start_line` formula correspondingly.
2. Verify with a fixture where a body violation sits on a known file line N — reported line number should change from `N+1` to `N`.
3. Update any `/a4:validate` test expectations or docs that previously cited the buggy line numbers (none known at session end, but worth grepping).

Commit message must be loud about the change — it's user-visible.

## Other parked follow-ups (carried from previous handoff)

Re-evaluated against this session's state. Most are unaffected by this session; the in-process-import design still holds.

1. **`transition_status.py --sweep` SessionStart hook.** Still deferred. Becomes easier once `transition_status.py` is in the common-helper regime (can call its sweep function in-process from the dispatcher).
2. **`compass` wrapper.** Still open.
3. **SessionStart `systemMessage` for status-consistency-only output.** Still open; unchanged by this session.
4. **Observe the dispatcher in a real workspace.** Still the highest-value next test. Not done in this session (the smoke fixture is synthetic).
5. **`refresh_implemented_by.py` module docstring.** Still open (one-line cleanup).
6. **Hard-fail surfacing design.** Still open.
7. **Test harness for the dispatcher.** Still the best payoff of the modularization work. With `common.py` holding `ParsedMarkdown` + `split_frontmatter`, a `tests/` sibling directory can import `a4_hook` and call subcommand functions directly with patched stdin/env. No subprocess fixturing required.
8. **Stop budget elasticity.** Not rushed.

# Verification approach

Same synthetic fixture through all three commits. Build:

```
/tmp/a4-common-test/
├── .claude/tmp/a4-edited/
└── a4/
    ├── usecase/1-login.md         # has stale implemented_by: [task/99-stale]
    ├── usecase/2-broken.md        # missing id/status/created/updated
    ├── task/10-auth.md            # implements: [usecase/1-login]
    ├── idea/20-bad.md             # status=promoted, promoted:[]
    ├── idea/21-wikilink.md        # (added in commit 3 verification) body [[nonexistent-task]]
    ├── review/   decision/   spark/   (empty)
```

Per-commit checks run:

- `python3 -m py_compile` on every script (fast, catches typos).
- `uv run validate_frontmatter.py <fx>` → expect 4 violations on `usecase/2-broken.md`.
- `uv run validate_body.py <fx>` → commits 1–2: clean. Commit 3: 1 violation on `idea/21-wikilink.md:10`.
- `uv run validate_status_consistency.py <fx>` → 1 mismatch on `idea/20-bad.md`.
- `uv run validate_status_consistency.py <fx> --file idea/20-bad.md` → same single mismatch.
- `uv run refresh_implemented_by.py <fx> --dry-run` → 1 change on `usecase/1-login`.
- **Dispatcher:** three inputs (post-edit stdin JSON, stop stdin JSON, session-start env) → full JSON + stderr captured and compared against commit-1 output byte-for-byte.
- **Silent-skip paths:** empty stdin, malformed JSON, missing `CLAUDE_PROJECT_DIR` — all return rc=0 with no output.

The commit-3 `idea/21-wikilink.md` fixture addition is the only verified behavior change. Every other observable was held constant.

# The validate_body off-by-one

Concrete demonstration. File at commit-3 end state:

```
---                                 line 1
id: 3                               line 2
title: Body lines                   line 3
status: ready                       line 4
created: 2026-04-20                 line 5
updated: 2026-04-20                 line 6
---                                 line 7
                                    line 8 (empty)
[[nonexistent-target]]              line 9
```

Current output: `usecase/3-bodylines.md:10 (wikilink-broken): ...`.

Root cause: `common.split_frontmatter` intentionally keeps `body = "\n\n[[nonexistent-target]]\n"` (leading `\n` retained). `body.splitlines()` = `["", "", "[[nonexistent-target]]"]`. With `body_start_line = 8`, iteration yields `abs=8,9,10` for `i=0,1,2` — so `[[nonexistent-target]]` reports as line 10 instead of 9.

This bug existed in the old `validate_body.split_frontmatter` too; the unification preserved it.

# Design decisions worth remembering

1. **A.a layout chosen.** `plugins/a4/scripts/` IS the package. No subdirectory, no rename, no file moves. All 42 external `uv run scripts/<name>.py` call sites continue to work verbatim. The alternative B (`python -m scripts.<name>`) was rejected because it would force a 23-file sweep of skills/agents.

2. **`common.py` is a plain module, no PEP-723 header.** Scripts that import it must carry `pyyaml>=6.0` in their own headers. `a4_hook.py` is the dispatcher entry point and therefore the aggregator for deps that sibling modules transitively need.

3. **Line-boundary `\n---` detection is canonical.** The `split("---", 2)` approach that three of the four scripts used is vulnerable to body text containing `---` (e.g., a horizontal rule). Canonical uses line-boundary matching so this cannot mis-split.

4. **Back-compat wrappers kept in two scripts** (`validate_status_consistency.split_frontmatter` returning `fm`; `refresh_implemented_by.split_frontmatter` returning a 3-tuple). Purpose: avoid rewriting many internal call sites inside those scripts while the rest of the module is still in flight. Safe to inline if and when those scripts are pulled further into the common regime.

5. **`validate_body` off-by-one preserved, not fixed.** User explicitly asked for "no quiet bug fixes". Fix lives in a follow-up with a loud commit message.

6. **`idea/` coverage fix was NOT quiet.** It changes observable output (idea-file body violations are now reported). Minor-version bump (`1.13.3 → 1.14.0`) flags it. Non-idea output is byte-identical.

7. **Dispatcher `sys.path.insert(0, _SCRIPTS_DIR)` stays.** The previous handoff's promise to "drop the `sys.path` hack" applied to hypothetical Option A with a rename; under A.a the hack is still the cleanest way for the dispatcher to import its siblings. Once `__init__.py` is present the hack is syntactically redundant (Python auto-inserts script-dir), but being explicit costs one line and protects against invocation paths (e.g., `uv run -`, `python -m`) that don't auto-insert.

# Explicitly untouched

- **`plugins/a4/hooks/hooks.json`** — invocation lines unchanged.
- **`plugins/a4/hooks/README.md`, `hooks/cleanup-edited-a4.sh`, `hooks/sweep-old-edited-a4.sh`** — unchanged.
- **`plugins/a4/references/hook-conventions.md`** — unchanged this session. §3 still describes the in-process-import pattern correctly. Update it again when the modularization reaches the remaining 8 scripts (the sys.path note will become stale if/when the dispatcher stops needing it).
- **Skills and commands under `plugins/a4/`.** No SKILL.md or `commands/*.md` file touched. All 42 `uv run scripts/<name>.py` call sites continue to work.
- **Other plugins in the marketplace.** Only `a4` bumped — `1.13.1 → 1.14.0` across the three commits.
- **`plugins/a4/scripts/transition_status.py`, `allocate_id.py`, `drift_detector.py`, `extract_section.py`, `inject_includes.py`, `read_frontmatter.py`, `index_refresh.py`** — eight scripts not modified. Still self-contained PEP-723 units.

# Key files to re-read on the next session

- **`plugins/a4/scripts/common.py`** — the new module. Small, read it top-to-bottom. The `split_frontmatter` docstring documents the line-boundary algorithm and the canonical `ParsedMarkdown` contract.
- **`plugins/a4/scripts/validate_frontmatter.py`, `validate_body.py`, `validate_status_consistency.py`, `refresh_implemented_by.py`** — updated callers. Note how each `import` from `common` differs based on needs. The two back-compat wrappers are in `validate_status_consistency.py` and `refresh_implemented_by.py`.
- **`plugins/a4/scripts/a4_hook.py`** — dispatcher. Only change is the one `vfm.split_frontmatter(path)` call site (in `_stop()`) unpacking as `parsed.fm` now. Still has its `sys.path.insert` prelude.
- **Previous handoffs on this thread** — `2026-04-25_0301_dispatcher-in-process-imports.md` has the full rejected-alternatives list and the six-principle hook-conventions summary; `2026-04-25_0244_consolidate-hooks-into-dispatcher.md` explains why `a4_hook.py` exists as a single entry point.

# Outstanding parked threads

- **`a4-hook-automation`** (this thread) — open. Next tasks: (a) migrate one or two of the eight unvisited scripts into the common-helper regime (`transition_status`, `allocate_id`, `index_refresh` are highest-value), (b) optional line-number fix for `validate_body`, (c) everything else from the carried follow-ups.
- **`uc-status-transition-system`** — formally concluded; two minor parked items remain.
- **`idea.promoted` / `brainstorm.promoted` materialization** — still open. Unrelated to this thread.
- **`a4-redesign`, `experiments-slot`, `idea-slot`, `decision-slot-unification`** — unaffected by this session.
