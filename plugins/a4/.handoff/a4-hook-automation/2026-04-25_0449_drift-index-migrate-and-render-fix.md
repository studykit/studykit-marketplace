---
timestamp: 2026-04-25_0449
topic: a4-hook-automation
previous: 2026-04-25_0415_markdown-module-and-cli-prune.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_0449. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

Continued the scripts-modularization thread from the prior handoff. Three deliberate moves:

1. **Migrate `drift_detector.py` to shared modules** — drop its local `split_frontmatter` (6 call sites), route through `markdown.extract_preamble` / `extract_body` via a local `_fm` shim.
2. **Migrate `index_refresh.py` to shared modules** — same pattern, 3 call sites of `split_frontmatter`.
3. **Rendering fix in `index_refresh.render_section`** — insert a blank line between the `<!-- static-fallback-start -->` HTML comment and the static-fallback table content. Obsidian's dataview blocks were failing to render because the adjacent table without a leading blank line broke markdown parsing of the whole section.

Also: **decided NOT to migrate `inject_includes.py`** after honest analysis — it has no `split_frontmatter`, no `import yaml`, and migrating its section-extraction to `markdown.Body.extract_headings()` would introduce behavior changes (fence-skip semantics, whole-file frontmatter stripping). Removed from the migration backlog.

Two commits land on top of `9106da177` (last commit before this session):

- `19a7fa093` — refactor: byte-identical migration of drift_detector + index_refresh.
- `a73270152` — fix: blank line before static-fallback content.

a4 1.14.1 → **1.14.2** (refactor) → **1.14.3** (rendering fix).

Thread topic `a4-hook-automation` retained.

# What shipped this session

## `drift_detector.py` — migrated

Six call sites of the old local `split_frontmatter` are gone. New surface:

```python
from common import WIKI_KINDS
from markdown import extract_body, extract_preamble

def _fm(path: Path) -> dict:
    """Preserves the pre-shared-module `split_frontmatter(path)[0]` contract:
    every caller `.get()`s fields and tolerates an empty mapping."""
    return extract_preamble(path).fm or {}
```

Call-site mapping:

| Old site | New |
|---|---|
| `discover_wiki_pages` | `if _fm(md).get("kind") in WIKI_KINDS` |
| `detect_wiki_drift` | `body = extract_body(path).content` |
| `detect_close_guard_drift` (fm read) | `fm = _fm(path)` |
| `detect_close_guard_drift` (wiki body read) | `body = extract_body(wiki_path).content` |
| `existing_fingerprints` | `fm = _fm(path)` |
| `compute_next_id` | `raw = _fm(md).get("id")` |

**`WIKI_KINDS` now imported** from `common` (frozenset — membership-test only; no iteration-order dependency here).

**`ISSUE_FOLDERS` kept local** as `("usecase", "task", "review", "decision")` — intentionally narrower than `common.ISSUE_FOLDERS` (which includes `"idea"`). An explanatory comment is inline. Widening is a separate semantic decision, not a refactor:

- `discover_issues` (used for wikilink resolution): adding `idea/` would stop `[[idea/<n>-<slug>]]` wikilinks from being flagged stale.
- `compute_next_id`: adding `idea/` would prevent a theoretical id collision if an idea holds the current workspace max id.

Both changes would be "quiet bug fixes" if folded into the refactor commit — deferred by design.

**`import yaml`** still present (used directly by `yaml.safe_dump` in `build_review_item`).

## `index_refresh.py` — migrated

Three call sites of `split_frontmatter` replaced with the same `_fm` shim pattern. All three needed only the preamble dict:

| Old site | New |
|---|---|
| `discover_wikis` | `fm = _fm(path)` |
| `discover_issues` | `fm = _fm(md)` |
| `discover_sparks` | `fm = _fm(md)` |

**`ISSUE_FOLDERS` now imported** from `common` (identical tuple: `("usecase", "task", "review", "decision", "idea")`).

**`WIKI_KINDS` kept local** as an ordered tuple with inline comment. This is a different rationale from drift_detector's `ISSUE_FOLDERS` divergence — here the local copy is a **different type** (tuple, not frozenset):

```python
# Local ordered tuple — iteration order drives the Wiki-pages table
# rendering. `common.WIKI_KINDS` is a frozenset (membership-test only),
# so we cannot reuse it here without destabilizing output.
WIKI_KINDS: tuple[str, ...] = (
    "context", "domain", "architecture", "actors", "nfr", "plan", "bootstrap",
)
```

The Wiki-pages table renders rows in `WIKI_KINDS` order (`for kind in WIKI_KINDS: …`). Swapping to `common.WIKI_KINDS` (a frozenset with implementation-defined iteration order) would destabilize the output. A cross-script unification would require either:

- promoting `common.WIKI_KINDS` to an ordered tuple (with a small O(n) `in`-cost for other callers), or
- adding a second exported ordered sequence like `common.WIKI_KIND_ORDER`.

Neither is done here — kept local is fine for now.

**`import yaml` removed.** No direct `yaml.*` calls remain. PEP-723 `pyyaml>=6.0` **retained** for the transitive `markdown.parse` dep, matching the `allocate_id.py` pattern from the prior handoff.

**Pyright noise.** `index_refresh.py:38` shows a pre-existing dead import (`field` from `dataclasses` never used). Noticed but **not fixed** this session — discipline is to keep refactor commits tight; a standalone "dead-import cleanup" is a fine follow-up but not worth folding in.

## `render_section` — rendering fix (separate commit)

Committed separately (`a73270152`) because it intentionally changes output, whereas the refactor above is byte-identical.

```diff
     parts.append(f"<!-- static-fallback-start: {marker_id} -->")
+    parts.append("")
     parts.append(static)
     parts.append(f"<!-- static-fallback-end: {marker_id} -->")
```

**Observed symptom** (user-reported): Obsidian's dataview blocks in `INDEX.md` were not rendering live. A markdown table that begins on the line immediately after an HTML comment (without a blank line above) is not recognized as a table by many parsers, and the malformed block cascaded: the preceding ```dataview``` fence was also not rendered.

**Fix scope.** Only the leading blank (between `start` marker and `static`) was added. The trailing `<!-- static-fallback-end: … -->` still abuts the last line of the static content — the user confirmed only the leading blank was needed; adding a symmetric trailing blank is an easy follow-up if ever necessary.

**Affects 8 sections** (wiki-pages, stage-progress, open-issues, drift-alerts, milestones, recent-activity, open-ideas, spark). All regenerated on next `index_refresh.py` run.

## `inject_includes.py` — explicitly NOT migrated

Analyzed but rejected. Rationale (recorded here so the next session does not redo the analysis):

- **No `split_frontmatter`** and **no `import yaml`** in the file. The refactor's primary targets are absent.
- Its `extract_section(text, heading)` slices line ranges between ATX headings; it is not what `markdown.Body.extract_headings()` provides (which returns heading metadata, not section bodies).
- The local `HEADING_RE` differs semantically from `markdown._ATX_HEADING_RE`: no closing-`#` support (`# Title #` would capture `Title #` here vs `Title` in markdown.py).
- Its `extract_section` does **not** skip fenced code blocks. `markdown.Body.extract_headings` does. Migration would silently flip this.
- Its whole-file embed (`![[file]]` without heading) includes frontmatter in the injected content. Switching to `markdown.extract_body` would silently strip frontmatter.

Net: a migration would be at least three behavior changes packaged as a refactor. Rejected on "no quiet bug fixes". If `inject_includes` needs any of those fixes, file them as explicit loud-commit follow-ups, not as part of shared-module migration.

**Removed from the scripts-migration backlog** (see [§What's left](#whats-left)).

## Verification

Same style as the prior handoff. Two synthetic fixtures built from scratch:

- `/tmp/a4-drift-smoke/a4/` — context wiki with 4 drift triggers (orphan-marker, orphan-definition, stale-footnote, missing-wiki-page), seeded `idea/30-seed.md` to verify that drift_detector's local `ISSUE_FOLDERS` still excludes idea/ from next-id calculation (expected: 22..25 not 31..34).
- `/tmp/a4-index-smoke/a4/` — one of each folder (usecase, task, review w/ drift source, decision, idea, spark.brainstorm).

Checks executed:

- `python3 -m py_compile` on both migrated scripts → OK.
- drift_detector: `--dry-run --json` output is **byte-identical** to a pre-refactor `git show HEAD:plugins/a4/scripts/drift_detector.py` run on the same fixture (diff was empty once `Installed …` stderr noise was stripped).
- drift_detector: real-write run produced ids 22..25 (confirming idea/30 exclusion). Second run dedup-suppressed all 4 drifts. Close-guard correctly did not fire when the wiki had the required citation.
- index_refresh: `--dry-run` output is byte-identical to a pre-refactor run (modulo the `generated_at` timestamp). Real write produced a valid `INDEX.md` with all 8 sections.
- index_refresh (post-rendering-fix): manual inspection confirms the blank line appears between `<!-- static-fallback-start: wiki-pages -->` and the `| Page | Present | Updated |` table row.

Dispatcher end-to-end was **not** exercised this session (still the highest-value next test — carried from prior handoff).

# What's left

## Scripts still in the unshared regime

Down from 6 to 1 (we migrated 2 this session and removed `inject_includes` from the list):

| Script | External `uv run` call sites | Notes |
|---|---|---|
| `transition_status.py` | 12 | Biggest remaining target. Has own `split_frontmatter` (17 internal call sites returning `(fm, raw_fm, body)` tuple), `rewrite_frontmatter_scalar(raw_fm, ...)`, `write_file(path, raw_fm, body)`. Pattern matches `refresh_implemented_by.py` exactly — use `parse` for read, keep `raw` for surgical rewrites, `lstrip()` body on write. Care needed across supersedes cascade paths. |

`inject_includes.py` is removed from this list — see [§`inject_includes.py` — explicitly NOT migrated](#inject_includespy--explicitly-not-migrated).

`a4_hook.py` (dispatcher) already uses shared modules transitively — no structural changes pending.

## Optional: `validate_body` off-by-one fix

Unchanged from prior handoff. Still applies symmetrically to `Body.extract_headings()` line numbers. Standalone loud commit when done.

## Other parked follow-ups (carried from prior handoff, unchanged)

1. `transition_status.py --sweep` SessionStart hook.
2. `compass` wrapper.
3. SessionStart `systemMessage` for status-consistency-only output.
4. Observe the dispatcher in a real workspace.
5. Hard-fail surfacing design.
6. Test harness for the dispatcher. `markdown.py` and `common.py` are stable; a sibling `tests/` directory can import `a4_hook` and call subcommand functions with patched stdin/env.
7. Stop budget elasticity.

## New follow-ups opened this session

- **Widen drift_detector's `ISSUE_FOLDERS`** to include `"idea"`, or unify with `common.ISSUE_FOLDERS`. Flag as a semantic decision (affects wikilink resolution + next-id). Suggested as a loud commit.
- **Unify `WIKI_KINDS` ordering.** If a future migration wants iteration-order for other callers, promote `common.WIKI_KINDS` to an ordered tuple (keep a frozenset locally in membership-only sites). Not blocking.
- **Pre-existing dead import in `index_refresh.py:38`** (`field` from `dataclasses`). Trivial standalone cleanup.
- **Symmetric trailing blank line in `render_section`** (before the `<!-- static-fallback-end -->`). Not needed for current rendering, file as a cosmetic follow-up if noticed elsewhere.

# Design decisions worth remembering

1. **`_fm` shim is the idiomatic migration pattern for old `split_frontmatter[0]`-only call sites.** `validate_status_consistency.py`, `drift_detector.py`, and `index_refresh.py` all define a local `def _fm(path) -> dict: return extract_preamble(path).fm or {}` to preserve the old `{}`-on-failure contract. For scripts that need body+fm together, use `markdown.parse(path)` via a local adapter (e.g., `refresh_implemented_by._parse`).

2. **`WIKI_KINDS` in `common.py` is a frozenset by deliberate contract — membership test only.** If iteration order matters for a caller's output, keep a local ordered tuple (see `index_refresh.py`). This divergence is acceptable until a second caller needs order, at which point promote a tuple (with or without also exporting the frozenset for membership-only callers).

3. **`drift_detector.ISSUE_FOLDERS` is intentionally narrower than `common.ISSUE_FOLDERS`.** The local tuple preserves pre-idea-slot behavior. Widening has real semantic impact; it is a decision, not a cleanup.

4. **Refactor commits must be byte-identical.** The `render_section` rendering fix was committed **separately** (`a73270152`) from the refactor commit (`19a7fa093`), even though both touch `index_refresh.py`. Future-you reviewing the diff can trust that `19a7fa093`'s output did not change.

5. **`inject_includes.py` is out of the shared-module migration scope.** It has no yaml/split_frontmatter. Attempting to unify its heading/section extraction with `markdown.py` requires accepting three behavior changes (fence-skip, closing-`#`, whole-file frontmatter strip). Leave standalone; fix behaviors individually if desired, as loud commits.

6. **Version bumps stayed patch-level.** 1.14.1 → 1.14.2 (refactor) → 1.14.3 (rendering fix). Refactor had byte-identical output — patch is honest. Rendering fix changed output but is a bug fix, still patch.

# Explicitly untouched

- **`plugins/a4/hooks/hooks.json`** — unchanged.
- **`hooks/*.sh`** — unchanged.
- **Skills and commands under `plugins/a4/`** — none touched. All `uv run scripts/drift_detector.py` / `index_refresh.py` call sites in `skills/drift/SKILL.md`, `skills/auto-bootstrap/SKILL.md`, `skills/compass/SKILL.md`, `skills/validate/SKILL.md` continue to work unchanged.
- **`transition_status.py`, `inject_includes.py`** — not migrated (former by scheduling, latter by deliberate decision).
- **`references/hook-conventions.md §3 Shared modules`** — already documents the `markdown.py` + `common.py` convention in generic terms. No update was needed; per-script divergences (WIKI_KINDS tuple, ISSUE_FOLDERS narrowing) are inline comments in the scripts, not convention-level rules.
- **`references/frontmatter-schema.md`** — not touched.

# Key files to re-read on the next session

- **`plugins/a4/scripts/drift_detector.py`** — see `_fm` shim (L90-ish), the `ISSUE_FOLDERS` divergence comment near the top, and the 6 migrated call sites.
- **`plugins/a4/scripts/index_refresh.py`** — see `_fm` shim, the `WIKI_KINDS` local-tuple comment, and `render_section` with the new blank-line emit.
- **`plugins/a4/scripts/markdown.py`** — unchanged this session; still the canonical reference for parse/extract_preamble/extract_body/Body.extract_headings.
- **`plugins/a4/scripts/common.py`** — unchanged this session.
- **`plugins/a4/scripts/transition_status.py`** — likely next migration target. Scan its local `split_frontmatter`, `rewrite_frontmatter_scalar`, `write_file` (around lines 129 / 160 / 192) and the 17 internal call sites. `refresh_implemented_by.py`'s `_parse` / `_write_file` pair is the template.
- **Previous handoff** `2026-04-25_0415_markdown-module-and-cli-prune.md` — the design rationale for the markdown module extraction and the prune of dead-code CLIs this session built on.

# Outstanding parked threads

- **`a4-hook-automation`** (this thread) — open. Next: `transition_status.py` migration, or any of the follow-ups enumerated above.
- **`uc-status-transition-system`** — formally concluded.
- **`idea.promoted` / `brainstorm.promoted` materialization** — still open, unrelated.
- **`a4-redesign`, `experiments-slot`, `idea-slot`, `decision-slot-unification`** — unaffected.
