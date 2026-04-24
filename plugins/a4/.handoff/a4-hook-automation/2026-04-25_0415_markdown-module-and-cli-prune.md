---
timestamp: 2026-04-25_0415
topic: a4-hook-automation
previous: 2026-04-25_0350_scripts-common-extraction.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_0415. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

Continued the scripts-modularization thread from the prior handoff. Two deliberate moves:

1. **Extract a dedicated `markdown.py` module** and redesign its public surface to reflect the user's mental model — `Preamble` / `Body` / `Markdown` dataclasses plus `parse` / `extract_preamble` / `extract_body` free functions and a `Body.extract_headings()` method. `ParsedMarkdown` + `split_frontmatter` are gone.
2. **Prune dead-code CLIs** (`read_frontmatter.py`, `extract_section.py`). Both had zero callers across the whole repo and one was a hand-rolled mini-YAML parser intentionally avoiding PyYAML — now subsumed by `markdown.parse`.

Also: migrated `allocate_id.py` into the shared-module regime (one of the "eight untouched" scripts flagged in the previous handoff's punch list).

All changes landed in a single non-handoff commit `b5c32ca57`. a4 1.14.0 → **1.14.1** (patch bump — deleted files had no known callers, so no externally observable behavior change).

Thread topic `a4-hook-automation` retained.

# What shipped this session

Single commit on top of `6c4588836` (last commit from the prior handoff).

## `scripts/markdown.py` — new module

Replaces the markdown-parsing half of `common.py`. The previous handoff's `split_frontmatter` + `ParsedMarkdown` API is retired. New surface:

```
Classes
  Preamble         .fm: dict | None, .raw: str
  Body             .line_start: int, .content: str
                   .extract_headings() -> list[Heading]
  Markdown         .preamble: Preamble, .body: Body
  Heading          .level: int, .text: str, .line: int

Functions
  parse(path)              -> Markdown
  extract_preamble(path)   -> Preamble   # does NOT go through parse()
  extract_body(path)       -> Body       # does NOT go through parse()
```

**Naming.** User chose "preamble" as the a4 term for YAML frontmatter. Class names match. Top-level function name changed from `extract_markdown` → `parse` mid-session per user direction.

**Non-delegating single-purpose helpers.** `extract_preamble` and `extract_body` deliberately do NOT call `parse()`. Reason (user directive): `extract_preamble` should not pay body processing cost, and `extract_body` should not run YAML parsing. They share a private `_locate_preamble(text) -> (raw, body_offset, body_line_start) | None` that only walks fences, plus `_load_yaml(raw) -> dict | None`. `parse` composes both.

**Canonical algorithm preserved.** Still line-boundary `\n---` detection; still handles empty preamble (`---\n---\n...`) explicitly; still returns `fm=None` on YAML error while retaining `raw`. The Body off-by-one quirk (leading newline retained in `content`, `line_start + i` convention) is **preserved verbatim** — see [§The off-by-one is still there](#the-off-by-one-is-still-there).

**Heading extraction.** `Body.extract_headings()` (instance method, not module function — user-requested move) parses ATX headings `# ...` through `###### ...`, including optional closing `#`s. Skips fenced code blocks (``` and ~~~). Setext underline headings (`===` / `---`) are NOT recognized — out of scope for current a4 needs. Heading line numbers use the same `line_start + i` convention as validate_body, so the off-by-one propagates here consistently.

## `scripts/common.py` — trimmed

After the split, `common.py` holds only workspace-level helpers:

| Symbol | Used by |
|---|---|
| `WIKI_KINDS` | validate_frontmatter, validate_body |
| `ISSUE_FOLDERS` | validate_frontmatter, validate_body, allocate_id |
| `discover_files(a4_dir)` | validate_frontmatter, validate_body |
| `is_int`, `is_empty`, `is_non_empty_list` | validate_frontmatter, validate_status_consistency |
| `normalize_ref(ref)` | validate_status_consistency, refresh_implemented_by |

No yaml import (removed), no markdown-parsing symbols (moved).

## Caller migration

Five files updated to the new API:

- **`validate_frontmatter.py`** — `from markdown import extract_preamble`; both call sites use `extract_preamble(p).fm`.
- **`validate_body.py`** — `from markdown import extract_preamble, parse`; one site uses `parse(path)` and reads `parsed.preamble.fm` / `parsed.body.content` / `parsed.body.line_start`, the wiki-page scan uses `extract_preamble`.
- **`validate_status_consistency.py`** — local shim renamed from `split_frontmatter` to `_fm` (since it no longer "splits"); now `def _fm(path): return extract_preamble(path).fm`. All 6 internal call sites sed-renamed.
- **`refresh_implemented_by.py`** — local 3-tuple shim renamed from `split_frontmatter` to `_parse`, now wrapping `markdown.parse`. Second call site (`collect_implements`) uses `extract_preamble` directly since it only needs `fm`.
- **`a4_hook.py`** — dispatcher no longer goes through `vfm.split_frontmatter`. It now has a local `from markdown import extract_preamble` in `_stop()` and calls `preamble = extract_preamble(path); fm = preamble.fm`.

No shim for backward compatibility at the module level. Every caller was updated in the same commit. The handoff predecessor's `split_frontmatter` re-exports are gone.

## `allocate_id.py` migration

Converted from self-contained to shared-module consumer:

- Removed local `ISSUE_FOLDERS` tuple → imports from `common`.
- Removed hand-rolled `text.split("---", 2)` → uses `extract_preamble(path).fm["id"]`.
- Removed `import yaml` (transitive dep via markdown). PEP-723 header still declares `pyyaml>=6.0` for the transitive need.
- Same CLI contract: `<a4-dir>`, `--list`, `--check`. Verified byte-for-byte on the smoke fixture against the new file — all three modes produce identical output to the old version.
- 22 lines → 8 lines for `extract_id`.
- **Minor robustness improvement (not a bug fix):** the old `split("---", 2)` could in principle mis-split on `---` embedded in bodies. For well-formed a4 files the two algorithms agree. No known file was affected in practice.

## `read_frontmatter.py` and `extract_section.py` — deleted

Both audited by grep across `plugins/`, `global/`, `.claude-plugin/` for `uv run <name>.py`, symbol imports, and doc references:

- **`read_frontmatter.py`** — 99 lines. Hand-rolled mini-YAML parser (intentionally no PyYAML; see L26 comment in the old file). Only non-handoff reference was a single bullet in `references/frontmatter-schema.md:398` listing it as "Read-only parser" — doc mention, not invocation. Bullet removed with the delete.
- **`extract_section.py`** — 84 lines. ATX-heading-based section extractor. Zero external references; the only grep hits pointed at a **locally defined** `extract_section` function inside `inject_includes.py` (same symbol name, entirely separate implementation — not an import). No doc mention anywhere.

Both prior handoffs tagged these as "Used by: Skills" in speculative inventories, but the actual grep showed zero callers. Dead code within the plugin.

## Docs

- **`references/hook-conventions.md §3`** — new "Shared modules" subsection documents the `markdown.py` + `common.py` convention: what each module exports, which PEP-723 header carries `pyyaml`, and the rule that new scripts must not reintroduce per-script `split_frontmatter` copies.
- **`references/frontmatter-schema.md`** — removed the `read_frontmatter.py` bullet.

No other docs touched. `hook-conventions.md §3.4` (in-process imports + `sys.path.insert`) remains accurate and unchanged.

# The off-by-one is still there

Reiterated from the previous handoff for continuity. `Body.content` retains a leading `\n` from the closing-fence line when a preamble is present. Given:

```
---                                 line 1
id: 3                               line 2
...                                 line 3..6
---                                 line 7
                                    line 8 (empty)
[[nonexistent-target]]              line 9
```

`Body.line_start` = 8, `Body.content` = `"\n\n[[nonexistent-target]]\n"`, `Body.content.splitlines()` = `["", "", "[[nonexistent-target]]"]`. The wikilink reports as `line 10` (= `line_start + i` with `i=2`) instead of `line 9`.

Preserved deliberately — same rule as the prior handoff, "no quiet bug fixes". The fix is a standalone follow-up:

1. Strip the leading newline in `_locate_preamble` (return `body_offset` advanced past it, OR lstrip in `parse`/`extract_body`). Simultaneously change `body_line_start` formula from `3 + raw_lines` to `2 + raw_lines` so `line_start + 0` points at the actual first body line.
2. Validate that `validate_body`'s `line_start + i` iteration now reports the correct line.
3. Check no test fixtures or docs bake in the buggy line numbers.
4. Loud commit message, minor version bump.

The fix also fixes `Body.extract_headings()`'s line numbers (same convention). They'd shift together.

# Verification approach

Same synthetic fixture as the prior handoff, rebuilt fresh:

```
/tmp/a4-md-smoke/a4/
├── usecase/1-ok.md   # clean file; includes `# Heading one` in body
├── task/10-t.md      # status: ready (intentionally wrong — task enum is different)
└── idea/20-bad.md    # status: promoted, promoted: []
```

Per-file checks run in the session:

- `python3 -m py_compile` on all 7 scripts (common, markdown, validate_frontmatter, validate_body, validate_status_consistency, refresh_implemented_by, a4_hook) — all OK.
- `uv run validate_frontmatter.py /tmp/.../a4` → reports task's enum-violation + missing-required kind (expected — task uses different enum).
- `uv run validate_body.py /tmp/.../a4` → 3 files scanned, no body-convention violations.
- `uv run validate_status_consistency.py /tmp/.../a4` → 1 mismatch on `idea/20-bad.md` (expected).
- `uv run refresh_implemented_by.py /tmp/.../a4 --dry-run` → reports `usecase/1-ok: implemented_by [] → ['task/10-t']` (expected — task 10 implements UC 1).
- `uv run allocate_id.py /tmp/.../a4` → `21` (= max(1,10,20)+1).
- `uv run allocate_id.py /tmp/.../a4 --list` → 3 lines, ids 1/10/20 with paths.
- `uv run allocate_id.py /tmp/.../a4 --check` → clean exit.
- Direct `markdown` API exercise via `python3 -c "import markdown; ..."`: `parse`, `extract_preamble`, `extract_body`, `Body.extract_headings()` all return the expected shapes.

Dispatcher end-to-end was **not** exercised this session (no real workspace reachability). Still the highest-value next test — see [§What's left](#whats-left).

# What's left

## Scripts still in the unshared regime

Six scripts remain untouched by the shared-module refactor. Revised priority list after this session:

| Script | External `uv run` call sites | Notes |
|---|---|---|
| `transition_status.py` | 12 | Biggest migration target. Has its own `split_frontmatter` (17 internal call sites returning `(fm, raw_fm, body)` tuple), `rewrite_frontmatter_scalar(raw_fm, ...)`, `write_file(path, raw_fm, body)`. Pattern matches `refresh_implemented_by.py` exactly — use `parse` for read, keep `raw` for surgical rewrites, `lstrip()` body on write. Care needed across supersedes cascade paths. |
| `drift_detector.py` | 3 | Has local `def split_frontmatter(path) -> tuple[dict, str]` used 6×. |
| `index_refresh.py` | 3 | Has local `def split_frontmatter(path) -> tuple[dict, str]` used 3×. |
| `inject_includes.py` | 1 | Has a locally defined `def extract_section(text, heading)` (same name as the deleted `extract_section.py`, but independent — survived the prune). |
| `a4_hook.py` | N/A (dispatcher) | Already uses shared modules transitively. No further changes unless structural. |

The previously-listed `read_frontmatter.py` and `extract_section.py` are gone, so eight-minus-two = six remaining.

**Recommended next step** still: either tackle `transition_status.py` (biggest, highest overlap, clearest pattern) or do the two small 3-call-site scripts (`drift_detector`, `index_refresh`) first as a warmup. The user opened `transition_status.py` in the IDE mid-session — soft signal that it is the intended next target.

## Optional: `validate_body` off-by-one fix

Still the standalone loud-commit follow-up. After this session the off-by-one is also present in `Body.extract_headings()` (same convention), so fixing it simultaneously fixes both. See [§The off-by-one is still there](#the-off-by-one-is-still-there).

## Other parked follow-ups (carried)

Unchanged from the prior handoff:

1. `transition_status.py --sweep` SessionStart hook.
2. `compass` wrapper.
3. SessionStart `systemMessage` for status-consistency-only output.
4. Observe the dispatcher in a real workspace.
5. Hard-fail surfacing design.
6. Test harness for the dispatcher. With `markdown.py` and `common.py` stable, a `tests/` sibling directory can import `a4_hook` and call subcommand functions with patched stdin/env. No subprocess fixturing needed.
7. Stop budget elasticity.

# Design decisions worth remembering

1. **Markdown parsing lives in its own module.** `common.py` is NOT where `parse` / `Preamble` / etc. live. They went to `markdown.py`. Rationale: single responsibility, and "common" was becoming a grab-bag.

2. **"Preamble" is the a4 term for YAML frontmatter.** User directive. Class is `Preamble`, not `Frontmatter`. Accept the terminology; do not second-guess in future handoffs.

3. **`extract_preamble` and `extract_body` do not go through `parse`.** User directive. Shared private helpers `_locate_preamble` + `_load_yaml` exist precisely so each entry point pays only the cost it needs. Do not collapse this.

4. **`Body.extract_headings()` is an instance method, not a module function.** User directive. The method body references `Heading` and `_ATX_HEADING_RE` by name; these are defined after `Body` in source order, which is fine because Python resolves names at call time.

5. **The off-by-one is still preserved.** Same rule as the prior handoff — no quiet bug fixes, fix lives in a standalone loud commit. This now applies symmetrically to `Body.extract_headings()` line numbers.

6. **Dead-code scripts are deleted, not archived or moved.** `read_frontmatter.py` and `extract_section.py` had zero callers; keeping them would be speculative. If someone needs them later, git restore is trivial. Do not pre-emptively move them to an `archive/` or similar location.

7. **Version bump is patch, not minor.** Deleted files had no known external callers; the rest of the change is internal refactor with byte-identical CLI output. Consumers see nothing. Patch bump is honest.

8. **Module name `markdown`** does not conflict with the PyPI `markdown` package in practice. `uv run <sibling>.py` prepends the scripts directory to `sys.path[0]`, so `from markdown import ...` resolves to our local module regardless of pypi-installed state. Worth noting if a future dep pulls in `markdown`.

# Explicitly untouched

- **`plugins/a4/hooks/hooks.json`** — invocation lines unchanged.
- **`hooks/*.sh`** — unchanged.
- **Skills and commands under `plugins/a4/`.** None touched. All 42-ish `uv run scripts/<name>.py` call sites for the surviving scripts continue to work.
- **Other plugins in the marketplace.** Only `a4` bumped — `1.14.0 → 1.14.1`.
- **`transition_status.py`, `drift_detector.py`, `index_refresh.py`, `inject_includes.py`** — four untouched self-contained scripts.

# Key files to re-read on the next session

- **`plugins/a4/scripts/markdown.py`** — small, read top-to-bottom. `_locate_preamble` docstring explains the algorithm; `Body` docstring explains the preserved off-by-one.
- **`plugins/a4/scripts/common.py`** — trimmed surface.
- **`plugins/a4/references/hook-conventions.md §3`** — new "Shared modules" subsection is authoritative for the convention.
- **`plugins/a4/scripts/transition_status.py`** — likely next migration target; scan its local `split_frontmatter` (line 129), `rewrite_frontmatter_scalar` (160), `write_file` (192) and the 17 internal call sites. Treat `refresh_implemented_by.py`'s post-session `_parse` shim as the template.
- **Previous handoff** `2026-04-25_0350_scripts-common-extraction.md` — the design rationale for the shared module approach, rejected alternatives, and the original ParsedMarkdown API this session replaced.

# Outstanding parked threads

- **`a4-hook-automation`** (this thread) — open. Next: migrate one or more of the remaining six scripts, or do the loud off-by-one fix.
- **`uc-status-transition-system`** — formally concluded.
- **`idea.promoted` / `brainstorm.promoted` materialization** — still open, unrelated.
- **`a4-redesign`, `experiments-slot`, `idea-slot`, `decision-slot-unification`** — unaffected.
