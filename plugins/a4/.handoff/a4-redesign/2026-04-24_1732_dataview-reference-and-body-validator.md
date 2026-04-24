---
timestamp: 2026-04-24_1732
topic: a4-redesign
previous: 2026-04-24_1710_obsidian-conventions-factor.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_1732. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: Dataview reference (ADR Item 12 closed) + body-convention validator

Topic thread: `a4-redesign` — continues from `.handoff/2026-04-24_1710_obsidian-conventions-factor.md` (Obsidian markdown conventions factoring). This session closes ADR Next Step **"Obsidian dataview examples"** (Item 12) and adds a companion body-level validator that the previous handoff explicitly flagged as a non-goal. With both changes, the `a4-redesign` ADR Next Steps are down to a single open item: the compass redesign.

Pre-handoff commit: **`97e53b50e`** — `docs(a4): add dataview reference and body-convention validator` (7 files, +607 / −17).

## Primary read for next session

1. **`plugins/a4/references/obsidian-dataview.md`** — new reference doc. Seven INDEX.md canonical dataview blocks (verbatim from `scripts/index_refresh.py`, with stage-progress documented as static-only), six reverse-derived relationship views (`blocks`, `implemented_by`, `justifies`, `superseded_by`, `children`, reviews-targeting), and a use-case-diagram source query. Third reference in the trio — reads together with `frontmatter-schema.md` (frontmatter side) and `obsidian-conventions.md` (body side).
2. **`plugins/a4/scripts/validate_body.py`** — new companion to `validate_frontmatter.py`. Four rules on wiki-page / issue / spark bodies: `footnote-format`, `footnote-sequence`, `footnote-review-payload`, `wikilink-broken`. Same CLI shape and exit-code semantics as the frontmatter validator.
3. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — Next Steps now has Items 6 and 12 both `[x]`, plus a new done entry for the body validator. Only **Compass redesign** is open.
4. This handoff.

---

## What this session accomplished

One pre-handoff commit: **`97e53b50e`**. Two logical changes bundled for atomicity (same ADR checklist touched by both, cross-ref updates overlap).

### Change 1 — ADR Item 12: Obsidian dataview reference

**New file `plugins/a4/references/obsidian-dataview.md`** (~190 lines). Structure:

- **Scope** — two query families (INDEX.md canonical + derived views); vault-layout assumption (vault root = repo root, hence `FROM "a4/..."`); legacy directories out of scope.
- **Keeping the INDEX.md blocks in sync** — short section flagging that `scripts/index_refresh.py` is the authoritative source for the first family; the validator does not police drift, so authors must keep both in step manually.
- **INDEX.md canonical blocks** — seven subsections (Wiki pages / Stage progress / Open issues / Drift alerts / Milestones / Recent activity / Spark). Six carry a dataview block verbatim from the script's string literals; **Stage progress** is documented as static-only because it mixes wiki-page presence with cross-folder issue aggregates.
- **Derived views** — six subsections mapping each forward relationship in `frontmatter-schema.md` §Relationships-are-forward-only to a reverse-derived dataview block. Each query uses a literal folder-prefixed path (e.g., `"usecase/3-search-history"`) as a placeholder rather than `this.file.*` — see design decision 2.
- **Use case diagram source** — one TABLE query feeding UC/actors/depends_on; dataviewjs-based mermaid rendering intentionally kept out.
- **Cross-references** — sibling reference docs + `index_refresh.py` + `drift_detector.py` + ADR.

**Supporting edits:**

- `plugins/a4/references/obsidian-conventions.md` Cross-references — added `obsidian-dataview.md` pointer.
- `plugins/a4/references/frontmatter-schema.md` Cross-references — added `obsidian-conventions.md` pointer (a prior asymmetry: that doc already referenced frontmatter-schema but not vice versa) plus `obsidian-dataview.md`. Fixed in the same pass.
- `plugins/a4/scripts/index_refresh.py` module docstring — added a paragraph declaring `obsidian-dataview.md` as the mirror reference and requiring hand sync on changes.
- ADR Item 12 flipped `[ ]` → `[x]` with a done note covering the reference doc contents, cross-links, sync-requirement docstring, and the `issue-links.md` removal (see Change 3).

### Change 2 — Body-convention validator (reversal of prior non-goal)

**New file `plugins/a4/scripts/validate_body.py`** (~270 lines).

Four rules, narrowly scoped on purpose:

- **`footnote-format`** — wiki-page `[^N]: ...` definition lines must match the canonical shape `[^N]: YYYY-MM-DD — [[target]]`. Em dash is U+2014, single-spaced; no trailing content after the wikilink.
- **`footnote-sequence`** — labels are integers in strict monotonic order starting at 1, in file order. Gaps and out-of-order labels are flagged with expected-vs-actual position messaging.
- **`footnote-review-payload`** — payload wikilink must **not** resolve to a `review/*` item. Matches `obsidian-conventions.md` line 60 ("Never a review item"). Supports both folder-prefixed (`review/5-...`) and bare basename forms via the shared issue index.
- **`wikilink-broken`** — every body wikilink in wiki pages, issue bodies, and spark files must resolve to an existing file in the workspace. Section refs (`#heading`) and aliases (`|display`) are stripped before resolution.

Same CLI shape as `validate_frontmatter.py`: `uv run validate_body.py <a4-dir> [file] [--json]`, exit `2` on any violation, `0` clean. Self-contained uv script; pyyaml is the sole runtime dependency.

**ADR update** — new done `[x]` Next Steps entry (immediately below Item 12) recording the decision, scope, and the three explicitly-out-of-scope rules (see design decision 5).

**Cross-references updated** — `obsidian-conventions.md` adds the validator to its Cross-references list; `frontmatter-schema.md` mentions the sibling script in its Validator behavior section.

### Change 3 — Removed `plugins/a4/references/issue-links.md`

Stale legacy file from the `think → a4` rename (`d50d2dea8`). Described an ID-to-GitHub-issue mapping workflow (`A4/issues.yml`, `FR-1`/`STORY-1` ID naming) that has zero live references in the plugin and conflicts with the current ADR model (lowercase `a4/`, integer IDs from `allocate_id.py`, no GitHub integration). Only mentions of `FR-1`/`STORY-1`-style IDs in the repo live under `a4/archive/` (explicitly legacy). Removal is documented in the ADR Item 12 done note.

### diff stat

```
plugins/a4/references/obsidian-dataview.md                 | +190 (new file)
plugins/a4/scripts/validate_body.py                        | +270 (new file)
plugins/a4/references/issue-links.md                       |  −16 (deleted)
plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md |  +3 / −1
plugins/a4/references/frontmatter-schema.md                |  +4 / −0
plugins/a4/references/obsidian-conventions.md              |  +2 / −0
plugins/a4/scripts/index_refresh.py                        |  +5 / −0
total                                                      | +607 / −17
```

---

## Design decisions worth flagging

Record here so the next session doesn't relitigate.

1. **Dataview scope: six in-use blocks + six reverse-derived + UC-diagram source.** The ADR's wording ("open issues by milestone, reverse-derived `blocks`/`implemented_by`/`superseded_by` views, UC diagram source, drift alert count") was read as a non-exhaustive list of examples. The actual set is: (a) every dataview block that `index_refresh.py` writes today (six; stage-progress has none), (b) reverse views for every forward relationship in `frontmatter-schema.md` §Relationships-are-forward-only (six, including `justifies`, `children`, and reviews-targeting that the ADR did not explicitly list), and (c) the UC-diagram TABLE. "Open issues by milestone" is not given a dedicated block — the existing Milestones and Open-issues blocks together cover it.
2. **Reverse-derived queries use hardcoded path literals, not `this.file.*`.** Mixed vault layouts (repo-root-as-vault vs. `a4/`-as-vault) plus dataview's list-contains string-vs-list-member semantics make generic `this.file.folder + "/" + this.file.name` patterns brittle. The reference doc documents this choice under "Path-format placeholder" and shows each query with a realistic example literal (e.g., `"usecase/3-search-history"`) that users swap on paste. Cleaner than hiding the customization behind dataview idioms that may or may not work.
3. **Mermaid/dataviewjs intentionally excluded from the UC-diagram section.** The reference gives a TABLE query that produces diagram-source rows; mermaid rendering from those rows requires dataviewjs + JavaScript execution permission in Obsidian's dataview settings. That's an authoring choice, not a project convention. The reference flags the requirement and stops there.
4. **Frontmatter vs body path format does *not* get its own dataview snippet.** The split is already documented in both sibling reference docs; repeating it in a dataview snippet would bloat without new information.
5. **Body validator deliberately narrow — four rules, not seven.** The previous handoff's "Non-goals" named a `validate_obsidian_conventions` script as "not worth the noise" and partially covered by `drift_detector.py`. This session reversed that by scoping tight. Rules covered (1) footnote canonical format, (2) label monotonicity, (3) payload-not-a-review-item, (4) wikilink resolution. Rules intentionally **not** covered:
   - `## Changes` section placement at file bottom — weak signal, low value against authors' obvious intent.
   - `updated:` bump consistency vs. footnote changes — requires git-history awareness; out of scope for a pure syntax linter.
   - Bare frontmatter-format paths (`usecase/3-...` without brackets) accidentally typed into body prose — high false-positive risk (they render identically to inline code in some viewers and are legitimate prose in discussions of the schema itself).

   The handoff's non-goal reversal is documented in the ADR's new body-validator done note. If any of the three excluded rules becomes worth enforcing later, this is the place to start.
6. **Fixture-based smoke test, not a committed test suite.** The session validated `validate_body.py` against a hand-rolled `mktemp -d` fixture that exercises all four rules plus a clean-path baseline (`actors.md` passes silent). All four violations triggered with correct line numbers and messages; exit code was 2; `--json` output parsed. No test file was committed because there's no existing test harness in the plugin, and bolting one on for a single script is premature. If a future session adds tests for any of the `scripts/*.py` files, redo the body-validator fixture as the first test case.
7. **Same CLI shape as `validate_frontmatter.py`.** Positional `<a4-dir>` + optional `<file>` + `--json` flag + exit `2` on violations. This matches `validate_frontmatter.py` exactly so the two can be invoked interchangeably by hooks/skills without special-casing either. If a future skill wires both into a pre-commit hook or similar, the identical interface is already the plan.
8. **No plugin version bump.** Holding the pattern from `72f62ac24`, `393304e57`, `537be88c8`, `851bc096a`, `1eb7d922c`. Single-feature doc + script additions do not bump `marketplace.json`. If the body validator later gets wired into a skill (changing skill behavior), that skill wiring is where a version bump would live.
9. **`issue-links.md` removal was not a separate commit.** Combined into the main pre-handoff commit because (a) its removal is documented inside the ADR Item 12 done note (authorial judgment: dataview reference + stale-doc cleanup are the same "docs housekeeping" unit) and (b) splitting would produce a trivial 16-line deletion commit that is more noise than signal. Verified before deletion: grep for `issue-links`, `issues.yml`, `FR-1`, `STORY-1` across the live plugin returns zero hits (only `a4/archive/*.md` uses those ID formats, which is already flagged as legacy).
10. **Reference-doc naming stays `obsidian-dataview.md` (not `obsidian-dataview-examples.md`).** Matches the two-word kebab-case pattern of `obsidian-conventions.md`, `frontmatter-schema.md`. The ADR's phrasing ("Obsidian dataview examples") is a section title, not a filename convention.

---

## Remaining ADR Next Steps (post-session state)

From `plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`:

1. ~~Schema finalization~~ (done 2026-04-24_1700)
2. ~~Id allocator~~ (done)
3. ~~Drift detector~~ (done)
4. ~~In-situ nudge integration~~ (done — spark-decide carve-out closed 2026-04-24_1638)
5. ~~Wiki update close guard~~ (done)
6. ~~Obsidian markdown conventions doc~~ (done 2026-04-24_1710)
7. ~~INDEX.md redesign~~ (done)
8. **Compass redesign** — Step 1.2 (artifact scan), Step 3 (gap diagnosis with drift detection) rewritten for the new layout. Step 0 (INDEX refresh) was already updated in a prior session.
9. ~~Skill rewrites~~ (done)
10. ~~Spark skill alignment~~ (done)
11. ~~README rewrite~~ (done — from an earlier handoff on this thread)
12. ~~Obsidian dataview examples~~ (**done this session**)
13. ~~Body-level convention validator~~ (**done this session** — added as a new `[x]` item below Item 12)

Also still open (tracked in prior handoffs, not an ADR Next Step):

- **`.handoff/INDEX.md`** — topic-grouped dashboard driven by `scripts/topic_references.py`. Now 13 handoffs under `plugins/a4/.handoff/` for the `a4-redesign` thread (this session being the 13th). Deferred 10 sessions running. Thread has a single remaining ADR item (Compass redesign); revisiting this dashboard question at thread close is increasingly worth it.

### Recommended next session

**Compass redesign** is the only ADR item left.

- `plugins/a4/skills/compass/SKILL.md` — Step 1.2 (artifact scan) and Step 3 (gap diagnosis) still use the pre-ADR layout (topic × stage grid). Rewrite for the per-item wiki+issue layout.
- Layer-2 integration: Step 3 should invoke `plugins/a4/scripts/drift_detector.py` rather than the pre-ADR gap heuristics. The drift detector already exists and handles close-guard / stale-footnote / orphan-marker / orphan-definition / missing-wiki-page.
- Consider wiring `validate_frontmatter.py` and `validate_body.py` into Step 3 as well — they're the other two "inconsistencies to surface" surfaces. Or leave them to `/a4:validate` (which doesn't exist yet; also a possible follow-up).

This is higher blast radius than the two doc/script additions this session — compass is an active skill with callers. The handoff from 2026-04-24_1710 already noted this: "save for when there's appetite for it." After compass lands, the `a4-redesign` thread can wrap with a thread-closure handoff listing shippable end-to-end.

---

## Files intentionally NOT modified

- **Skills that reference the protocol mechanically** — `usecase/SKILL.md`, `arch/SKILL.md`, `plan/SKILL.md`, `auto-bootstrap/SKILL.md`, `spark-decide/SKILL.md`, `drift/SKILL.md`, `compass/SKILL.md`, `auto-usecase/SKILL.md`, `index/SKILL.md`. None of them gained a pointer at `obsidian-dataview.md` or `validate_body.py`. The reference doc trio is discovered via the existing pointers from SKILLs → `obsidian-conventions.md` / `frontmatter-schema.md`, which already cross-link to the new files. Wiring any skill to run `validate_body.py` is a behavior change, not in scope here.
- **`plugins/a4/skills/index/SKILL.md`** — describes how `index_refresh.py` is invoked; did not gain an `obsidian-dataview.md` pointer because the SKILL documents the script's behavior, not the reference doc's existence. Readers who need the query syntax already look at `obsidian-conventions.md` → `obsidian-dataview.md`.
- **`plugins/a4/.claude-plugin/marketplace.json`** — version not bumped. See design decision 8.
- **`plugins/a4/README.md`** — reference docs are internal authoring convention; no user-facing surface.
- **Prior `.handoff/*.md`** files — all carry DO NOT UPDATE banners. The previous handoff's "Non-goals for next session" listed a validate-obsidian-conventions script as not-worth-the-noise; we reversed that in this session. The reversal lives in the ADR and this handoff, not in a retrofit of the prior handoff.
- **`plugins/a4/scripts/read_frontmatter.py`** — unchanged. Already a pure read-only parser; the new validator duplicates `split_frontmatter` locally because every script in `scripts/` keeps its own self-contained copy (pattern from `validate_frontmatter.py`, `drift_detector.py`, `index_refresh.py`). A future refactor could factor them into a shared helper module, but that's a cross-cutting change with its own call for review.

---

## Working-tree state at handoff time

Pre-handoff commit: **`97e53b50e`** — `docs(a4): add dataview reference and body-convention validator` (7 files, +607 / −17).

Branch state before this handoff's commit: `main` is 12 commits ahead of `origin/main` (10 before this session + 1 pre-session handoff from the previous session + 1 pre-handoff commit this session). Will be 13 after this handoff-file commit.

Changes bundled into this handoff's own commit:

```
new file:   plugins/a4/.handoff/2026-04-24_1732_dataview-reference-and-body-validator.md   # this file
```

---

## Files to read first next session

1. **`plugins/a4/references/obsidian-dataview.md`** — new canonical reference for dataview query patterns.
2. **`plugins/a4/scripts/validate_body.py`** — new validator script. Read alongside `validate_frontmatter.py` to see the sibling shape.
3. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — Next Steps list. Only Compass redesign remains.
4. This handoff.
5. **Prior handoff `2026-04-24_1710_obsidian-conventions-factor.md`** — immediate predecessor; also lists "validate obsidian conventions script" as a *non-goal* that this session reversed. Read both the non-goal there and design decision 5 here to understand why.
6. **If tackling Compass redesign:** `plugins/a4/skills/compass/SKILL.md` — specifically Step 1.2 (artifact scan) and Step 3 (gap diagnosis). Also `plugins/a4/scripts/drift_detector.py` (Layer-2 integration point), and now `validate_frontmatter.py` + `validate_body.py` (additional inconsistency surfaces that Step 3 could consume).

---

## Explicitly rejected / not done this session

- **"Open issues by milestone" as its own dataview block.** The ADR mentioned it as an example; the existing Milestones and Open-issues canonical blocks together cover the need. See design decision 1.
- **Generic `this.file.*`-based reverse-derived queries.** Vault-layout and `contains()` semantics make them fragile. See design decision 2.
- **Wiring `validate_body.py` into any skill, hook, or pre-commit.** Script-only delivery. Wiring is a separate decision for when the script has seen real use and the interface is stable.
- **Test suite for the new validator.** Smoke-tested against a temp fixture; no committed tests. See design decision 6. If a future session establishes a test harness for `scripts/*.py`, the validator's fixture is the obvious first case.
- **Shared helper module for `split_frontmatter` and friends.** Every script in `scripts/` still carries its own copy. Consistent with the prior precedent — refactor is a cross-cutting change that needs its own review cycle.

---

## Non-goals for next session

- Do not bolt the three excluded body-validator rules (Changes-section placement, `updated:`-bump consistency, bare-path-in-body detection) onto the validator without evidence that their false-positive profiles are acceptable. See design decision 5.
- Do not retrofit `this.file.*`-based path matching into the reverse-derived dataview blocks. The placeholder literal approach is explicit on purpose.
- Do not re-split `obsidian-conventions.md` / `obsidian-dataview.md` / `frontmatter-schema.md` into one big "obsidian reference". The three-way split (body / dataview / frontmatter) is the organizing principle; each cross-links to the others.
- Do not bundle the body validator into `validate_frontmatter.py` or rename the pair. The two-script split mirrors the two-doc split (frontmatter-schema.md + obsidian-conventions.md) and lets hooks pick either surface independently.
- Do not bump `marketplace.json` for the dataview ref or the body validator alone. Wait for a behavior change (skill wiring, new `/a4:validate` command, etc.) to justify a version bump.
