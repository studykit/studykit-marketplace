---
timestamp: 2026-04-24_1700
topic: a4-redesign
previous: 2026-04-24_1638_spark-decide-nudge-carveout.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_1700. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: frontmatter schema reference + validator (ADR Item 1 closed)

Topic thread: `a4-redesign` — continues from `.handoff/2026-04-24_1638_spark-decide-nudge-carveout.md` (spark-decide in-situ wiki nudge). This session closes ADR Next Step **"Schema finalization round"** (Item 1) with both a reference doc and an enforcing validator. Thread now has only two ADR items and the compass redesign left open.

Pre-handoff commit: **`851bc096a`** — `docs(a4): add frontmatter schema reference and validator` (3 files, +720 / −1).

## Primary read for next session

1. **`plugins/a4/references/frontmatter-schema.md`** — the new single source of truth for frontmatter rules. Lenient ONLY on unknown fields; strict on everything else. Also carries a "Known deferred items" section listing what Item 1 still leaves soft.
2. **`plugins/a4/scripts/validate_frontmatter.py`** — uv-style script (pyyaml) implementing every rule from the doc. Single-file / workspace / `--json` modes. Exit 2 on violation, 0 clean.
3. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — Next Steps list now has Item 1 `[x]`. Remaining open ADR items: **6 (Obsidian markdown conventions doc)**, **12 (Obsidian dataview reference snippets)**. Compass redesign is separately open.
4. This handoff.

---

## What this session accomplished

One pre-handoff commit: **`851bc096a`**.

### Two new files

1. **`plugins/a4/references/frontmatter-schema.md`** (~180 lines). Sections:
   - **Scope** — wiki / issue / spark families; legacy `plugins/a4/a4/*.decide.md` explicitly out of scope.
   - **Universal rules** — ids (monotonic global int), path references (plain string, no brackets, no `.md`; `.decide`/`.brainstorm` retained because they're part of the filename base), dates (`YYYY-MM-DD` YAML-native), empty collections (`[]` or omit), forward-only relationships.
   - **Structural relationship fields table** — consolidates `depends_on`, `implements`, `target`, `wiki_impact`, `justified_by`, `supersedes`, `promoted`, `parent`, `related` with direction + applicable-to + meaning.
   - **Per-type schemas (7)** — wiki, usecase, task, review, decision, spark-brainstorm, spark-decide. Each a table of field / required / type / values-or-format.
   - **Validator behavior** — single severity (all = error, exit 2), unknown fields ignored, hook wiring explicitly separate.
   - **Known deferred items** — (a) issue comment/log section format, (b) stricter enums for `framework` (decision) / `source` (review).
   - **Cross-references** — to ADR, allocator, drift detector, spark SKILLs.

2. **`plugins/a4/scripts/validate_frontmatter.py`** (~360 lines). Shape:
   - uv script header (`requires-python >= 3.11`, `pyyaml >= 6.0`).
   - `SCHEMAS` dict of 7 `Schema` dataclasses keyed by detected file-type name.
   - `detect_type(rel, fm)` — workspace-relative path + frontmatter dict → type key (`wiki` / `usecase` / `task` / `review` / `decision` / `spark_brainstorm` / `spark_decide`) or None (silently skipped).
   - Nine violation rules: `missing-required`, `enum-violation`, `type-mismatch` (int, date, list), `path-format`, `wiki-ref-unknown`, `kind-filename-mismatch`, `id-collision`, `missing-frontmatter` (only for files in `usecase/` / `task/` / `review/` / `decision/` / `spark/`).
   - CLI: `validate_frontmatter.py <a4-dir> [file] [--json]`. Positional `file` validates only that file (and skips workspace-wide id-uniqueness check).

### ADR update

`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md` Next Steps line for "Schema finalization round" (L309) changed from `[ ]` to `[x]` with a done note listing: schema doc location, validator location, validator scope, and the remaining deferred items (comment/log format + stricter enums). Frontmatter `updated:` left at `2026-04-24` (unchanged — already today).

### Validation sanity-check

Ran the validator against a constructed `/tmp/a4-test/` workspace seeded with 10 intentional violations spread across 6 files (wiki kind/filename mismatch, missing-required, wrong-enum, bad date, bracketed path, `.md` path, missing-frontmatter, unknown wiki ref, id collision across usecase/task). Validator caught **10/10** and exited 2. Ran also against `plugins/a4/a4/` (the plugin's own ADR directory) — 3 legacy `.decide.md` files correctly skipped because their root-level kind-less frontmatter does not match any type detector. Clean-workspace behavior verified via single-file mode on a valid wiki page (exit 0).

---

## Design decisions worth flagging

Record here so the next session doesn't relitigate.

1. **Single severity. No `--strict` / `--lenient` flag.** Every rule violation is an `error`. Exit 2 on any violation, 0 clean. **User explicitly confirmed this in chat** after I proposed a two-tier (warn/error) design — the argument was "warning이든 error든 결국은 LLM이 볼꺼 같은데" plus "required 누락도 항상 수정해야 하는 문제" plus "enum 값은 항상 맞춰야함". The only leniency retained is: **unknown fields are silently ignored**. Everything else is strict.
2. **`decision/` issue `status:` enum is `draft | final | superseded`.** The ADR body had sketched only `final`, but `draft` was added this session on user ask ("draft 상태 필요") because long ADRs are authored over time. `superseded` follows from the existing `supersedes:` relationship; `draft` fills the authoring gap. Schema doc line is the single source of truth now — don't re-narrow this enum without a new reason.
3. **`decision/` issue `updated:` is optional.** Schema doc lists `updated` as optional on decisions (unlike usecases / tasks / reviews where it's required). Rationale: decisions enter at `draft`, authors iterate, then commit to `final` — `updated:` bumps naturally during that iteration but is not load-bearing if the decision is small and lands in one sitting.
4. **Legacy `date:` field intentionally NOT mentioned in the schema doc.** **User explicitly removed this reference from the doc** ("legacy date field는 언급 하지 않는 걸로"). The doc now only names `created`, `updated`, and spark session timestamps. Treat legacy `date:` as an invisible carry-over — it does not exist per the schema and the validator does not recognize it.
5. **No universal `draft` across all types.** Each type has its own initial-state vocabulary with intentionally different semantics: `draft` (authoring content) for usecase / decision / spark-decide; `pending` (queued for execution) for task; `open` (awaiting triage) for review / spark-brainstorm. Collapsing these to a shared `draft` would conflate distinct workflow intents. **User raised then accepted this position** after the hook-validation angle — universalizing `draft` would not actually solve mid-authoring hook fires (because required-field absence is the real issue, not status value).
6. **Hook wiring is OUT OF SCOPE this session.** Claude Code has no "finalize" or "commit" hook event — available events are `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreCompact`, `Notification`. "Commit gate" semantically maps to a **git pre-commit hook** (external to Claude Code). The validator deliberately exits with 0/2 so ANY caller — Claude Code hook, git pre-commit, manual, skill-internal — can decide blocking vs notify vs ignore. Do not bolt hook config onto the validator; that's a separate decision.
7. **No plugin version bump.** Following precedent from commits `72f62ac24`, `393304e57`, `537be88c8` — single-item doc/script additions do not bump `marketplace.json`. Holding the line.
8. **Legacy files stay legacy.** `plugins/a4/a4/*.decide.md` (the plugin's own ADRs) — including the main spec-as-wiki+issues ADR — are the authoring spec, not output of an a4 skill. They are explicitly out of scope per the schema doc's "Scope" section, and the validator's `detect_type` returns None for them (root-level files without `kind: <wiki-kind>`). Do not retrofit their frontmatter to satisfy the schema.
9. **`files:` field on task is NOT validated as an a4 path reference.** The ADR example shows `files: [src/render.ts, src/render.test.ts]` — source-code paths, not a4 cross-references. The validator treats `files` as an unknown field (silently ignored). If you want list-of-strings validation for it later, add a new field category; don't shoehorn it into `path_list_fields`.
10. **Id collision check is inline, not delegated to `allocate_id.py --check`.** The schema doc originally said "delegated to allocator" but the validator grew its own `validate_id_uniqueness` pass to keep the one-script-one-call UX. `allocate_id.py --check` still works; they just overlap on this rule. Keep them consistent if either changes.

---

## Validator behavior quick reference

Nine rules, all `error`:

| Rule | Trigger |
|------|---------|
| `missing-required` | required field absent, `None`, or empty-string |
| `enum-violation` | value not in allowed set for a known enum field |
| `type-mismatch` | int field not int (or bool), date field not `date`/`YYYY-MM-DD`, list field not list |
| `path-format` | path reference has `[[`/`]]` brackets or `.md` suffix, or is empty |
| `wiki-ref-unknown` | `wiki_impact` entry not in `{context, domain, architecture, actors, nfr, plan, bootstrap}` |
| `kind-filename-mismatch` | wiki `kind:` value disagrees with file stem |
| `id-collision` | same integer `id:` appears in two or more issue files |
| `missing-frontmatter` | file in `usecase/` / `task/` / `review/` / `decision/` / `spark/` has no YAML block |
| *(unknown field)* | **NOT a rule** — unknown fields are silently ignored |

Exit codes: `0` clean, `1` argparse/usage error (e.g., nonexistent `a4-dir`, single-file outside the workspace), `2` any violation.

CLI shapes:

```
uv run plugins/a4/scripts/validate_frontmatter.py <a4-dir>
uv run plugins/a4/scripts/validate_frontmatter.py <a4-dir> <file-inside-a4-dir>
uv run plugins/a4/scripts/validate_frontmatter.py <a4-dir> --json
```

Single-file mode skips the workspace-wide id-uniqueness pass (it would require scanning everything anyway).

---

## Remaining ADR Next Steps (post-session state)

From `plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`:

1. ~~Schema finalization~~ (**done this session** — Item 1 fully `[x]`)
2. ~~Id allocator~~ (done)
3. ~~Drift detector~~ (done)
4. ~~In-situ nudge integration~~ (done — spark-decide carve-out closed 2026-04-24_1638)
5. ~~Wiki update close guard~~ (done)
6. **Obsidian markdown conventions doc** — `plugins/a4/references/obsidian-conventions.md`. Three SKILLs (`usecase`, `arch`, `plan`) currently inline a Wiki Update Protocol section each. Factor to one reference doc, replace inline copies with a short pointer + link. *Lower blast radius because it's documentation; extraction pass only.*
7. ~~INDEX.md redesign~~ (done)
8. **Compass redesign** — Step 1.2 (artifact scan), Step 3 (gap diagnosis with drift detection) rewritten for the new layout. Step 0 (INDEX refresh) was already updated in a prior session.
9. ~~Skill rewrites~~ (done)
10. ~~Spark skill alignment~~ (done)
11. ~~README rewrite~~ (done — from an earlier handoff on this thread)
12. **Obsidian dataview reference snippets** — canonical dataview blocks as reference material. Seed code already in `plugins/a4/scripts/index_refresh.py`.

Also still open (tracked in prior handoffs, not an ADR Next Step):

- **`.handoff/INDEX.md`** — topic-grouped dashboard driven by `scripts/topic_references.py`. Now 11 handoffs under `plugins/a4/.handoff/` for the `a4-redesign` thread (this session being the 11th). Deferred 8 sessions running. The `a4-redesign` thread has only 3 items left (6, 8, 12) before it can wrap — revisiting this dashboard question at thread close is worth considering.

### Deferred within Item 1 (documented in schema doc)

Item 1 is marked `[x]` but two sub-items remain soft, captured in the schema doc's "Known deferred items" section:

1. **Issue comment/log section format.** Body-level `## Log` convention is referenced in the ADR but entry format (prefix, timestamp granularity, author attribution) is not locked. Revisit when a skill ends up writing `## Log` entries programmatically and needs a canonical format.
2. **Stricter enums for open-ended fields.** `framework` (on decision) and `source` (on review) are currently open strings because the full value sets haven't been enumerated. Revisit once more review-agent `source:` values have landed in practice.

Neither blocks anything today; both will surface naturally as the respective skills mature.

### Recommended next session

Two ADR items left plus the compass redesign. In decreasing priority:

1. **Item 6 — Obsidian markdown conventions doc** (`plugins/a4/references/obsidian-conventions.md`). Factoring pass: consolidate the Wiki Update Protocol sections inlined in `usecase/SKILL.md`, `arch/SKILL.md`, `plan/SKILL.md` into one reference doc, replace inline copies with a short pointer + link. Lower blast radius (docs only), and the source material already exists.
2. **Item 12 — Obsidian dataview reference snippets**. Smallest of the three. Document the query patterns already living in `plugins/a4/scripts/index_refresh.py` as reference snippets under `plugins/a4/references/`.
3. **Compass redesign** (separate ADR item). Step 1.2 (artifact scan) and Step 3 (gap diagnosis with drift detection) need rewriting for the new per-item layout. Higher blast radius because it touches an active skill; save for when there's appetite for it.

After Items 6 and 12 land, the `a4-redesign` thread is effectively wrapped. A "thread-closure" handoff would be appropriate then, listing what's shippable end-to-end and what's intentionally left soft.

---

## Files intentionally NOT modified

- **`plugins/a4/scripts/allocate_id.py`** — no changes. Its `--check` mode overlaps with the new validator's `id-collision` rule but that's fine; two entry points for the same invariant is not a problem.
- **`plugins/a4/scripts/drift_detector.py`** — no changes. Already consumes `wiki_impact` and `source` which are now canonically documented in the schema doc.
- **`plugins/a4/scripts/read_frontmatter.py`** — no changes. It's a minimal frontmatter reader (no PyYAML), kept lean by design. The validator uses `yaml.safe_load` directly and does not reuse this reader because list/dict parsing semantics differ.
- **`plugins/a4/skills/*/SKILL.md`** — no changes. Skills don't call the validator from their wrap-up steps yet; that's a hook-wiring concern left for a future session (see design decision 6).
- **`plugins/a4/a4/*.decide.md`** (except the main ADR's Next Steps line) — legacy authoring files, out of scope per the schema doc.
- **`plugins/a4/README.md`** — validator is an internal enforcement tool, not a user-facing feature worth surfacing at README level.
- **`plugins/a4/.claude-plugin/marketplace.json`** — version not bumped. See design decision 7.
- **Prior `.handoff/*.md`** files — all carry DO NOT UPDATE banners. Not retrofitting, even where phrasing is now stale (e.g., prior handoff's "three ADR items left: 1, 6, 12" is now "two ADR items left: 6, 12").

---

## Working-tree state at handoff time

Pre-handoff commit: **`851bc096a`** — `docs(a4): add frontmatter schema reference and validator` (3 files, +720 / −1). Working tree clean after that commit, save for this handoff file.

Branch state before this handoff's commit: `main` is 7 commits ahead of `origin/main` (6 before this session + 1 pre-handoff commit). Will be 8 after this handoff-file commit.

Changes bundled into this handoff's own commit:

```
new file:   plugins/a4/.handoff/2026-04-24_1700_frontmatter-schema-and-validator.md   # this file
```

---

## Files to read first next session

1. **`plugins/a4/references/frontmatter-schema.md`** — the canonical schema. Universal rules + 7 per-type tables + validator behavior + known deferred items.
2. **`plugins/a4/scripts/validate_frontmatter.py`** — implements the doc. Read `SCHEMAS` dict to see exact required/enum/field-category mapping; read `validate_file` to see rule order.
3. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — Next Steps list to confirm which items are still open.
4. This handoff.
5. **Prior handoff `2026-04-24_1638_spark-decide-nudge-carveout.md`** — immediate predecessor; context on the in-situ nudge integration that this session builds alongside.
6. **If tackling Item 6 (obsidian conventions doc):** `plugins/a4/skills/usecase/SKILL.md` Wiki Update Protocol section, `plugins/a4/skills/arch/SKILL.md` "Wiki Page Schema" + "File Writing Rules" sections, any inline Wiki Update Protocol text in `plugins/a4/skills/plan/SKILL.md`. Factor into one doc at `plugins/a4/references/obsidian-conventions.md`.
7. **If tackling Item 12 (dataview snippets):** `plugins/a4/scripts/index_refresh.py` has the canonical query blocks already.
8. **If wiring the validator into a hook:** re-read design decision 6 of this handoff. Claude Code has no native "finalize"/"commit" event; `PostToolUse` (per write, noisy mid-authoring), `Stop` (turn boundary, practical), or a git pre-commit hook (external, cleanest "commit gate") are the realistic options. Pick based on noise tolerance.

---

## Explicitly rejected / not done this session

- **Two-mode validator (`--strict` / `--lenient`).** Proposed and rejected by the user. See design decision 1.
- **Severity tiers (warn vs error).** Proposed and rejected. See design decision 1.
- **Universal `draft` status across all types.** Proposed and rejected. See design decision 5.
- **Validating legacy `plugins/a4/a4/*.decide.md`.** Out of scope per the schema doc. Validator skips them naturally.
- **Validating `files:` field on tasks as a4 path references.** See design decision 9.
- **Retrofitting skills to call the validator.** Hook wiring is deferred. See design decision 6.
- **Bumping `marketplace.json`.** Precedent holds. See design decision 7.
- **Documenting the legacy `date:` frontmatter field in the schema doc.** User explicitly removed this. See design decision 4.

---

## Non-goals for next session

- Do not reopen the severity-tier debate on the validator. Single-severity design is final until a real operational need (not a speculative one) forces a revisit.
- Do not narrow `decision/` `status:` back to `{final, superseded}` — `draft` is load-bearing for author-over-time decisions.
- Do not restore mentions of the legacy `date:` field in the schema doc.
- Do not universalize `draft` across types. Task's `pending` and review's `open` mean different things from an authoring `draft`.
- Do not add hook configuration alongside the validator. Hook wiring is a distinct decision that may end up in plugin settings, `.claude/settings.local.json`, or a git pre-commit hook — don't preempt that choice by hard-coding a hook call in the validator.
- Do not merge `allocate_id.py` and `validate_frontmatter.py`. The allocator has a narrow, hot-path job (compute next id); the validator is diagnostic. Keeping them separate preserves the allocator's simplicity.
