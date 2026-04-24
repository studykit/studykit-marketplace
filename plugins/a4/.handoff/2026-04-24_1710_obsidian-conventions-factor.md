---
timestamp: 2026-04-24_1710
topic: a4-redesign
previous: 2026-04-24_1700_frontmatter-schema-and-validator.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_1710. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: Obsidian conventions factoring (ADR Item 6 closed)

Topic thread: `a4-redesign` — continues from `.handoff/2026-04-24_1700_frontmatter-schema-and-validator.md` (frontmatter schema reference + validator). This session closes ADR Next Step **"Obsidian markdown conventions doc"** (Item 6) by consolidating the inlined Wiki Update Protocol across three SKILLs into one shared reference. Thread now has only one ADR item and the compass redesign left open.

Pre-handoff commit: **`1eb7d922c`** — `docs(a4): factor Obsidian conventions into shared reference` (5 files, +135 / −26).

## Primary read for next session

1. **`plugins/a4/references/obsidian-conventions.md`** — the new shared reference for body-level markdown conventions. Wikilink / embed syntax, footnote audit trail format, full Wiki Update Protocol (when / how / defer / close guard), `updated:` bump rules. Pairs with `frontmatter-schema.md` (frontmatter-side counterpart).
2. **`plugins/a4/skills/usecase/SKILL.md`** lines 88–96 (§ **Obsidian Conventions**) — pointer section that replaces the inlined Obsidian Markdown Conventions + Wiki Update Protocol sections (formerly ~25 lines).
3. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — Next Steps list now has Item 6 `[x]`. Remaining open ADR items: **12 (Obsidian dataview reference snippets)**. Compass redesign is separately open.
4. This handoff.

---

## What this session accomplished

One pre-handoff commit: **`1eb7d922c`**.

### One new file

**`plugins/a4/references/obsidian-conventions.md`** (~125 lines). Structure:

- **Scope** — wiki / issue / spark family applicability; legacy directories out of scope (mirrors `frontmatter-schema.md` scope).
- **Link syntax (body)** — table of canonical forms (`[[path]]`, `[[path#Section]]`, `![[path]]`, `![[path#Section]]`, aliases); explicit contrast with frontmatter path format.
- **Footnote audit trail** — inline `[^N]` marker, `## Changes` section format, full example.
- **Wiki Update Protocol** — when to update (issue state changes, not time), how to update (4-step procedure), deferring via review item with `wiki_impact:`, close-guard semantics.
- **Bumping `updated:`** — wiki pages bump on every substantive change; issue files bump on status transitions or body changes.
- **Cross-references** — `frontmatter-schema.md`, `allocate_id.py`, `drift_detector.py`, `validate_frontmatter.py`, ADR.

### Three SKILL edits

- **`usecase/SKILL.md`** — deleted the two inlined sections (`## Obsidian Markdown Conventions` + `## Wiki Update Protocol`, formerly lines 88–112). Replaced with one `## Obsidian Conventions` section (8 lines) that points at the reference and lists the three rules this skill invokes below. Skill-internal phrases like "per the Wiki Update Protocol" (e.g., §3a nudge procedure, Wrap Up step 5) are preserved — the reader has already been pointed at the canonical location.
- **`arch/SKILL.md`** — two targeted edits:
  1. Line 39 (Wiki Page Schema section): "shared across the a4 plugin — mirror of SKILL.md in `usecase`" → "at `${CLAUDE_PLUGIN_ROOT}/references/obsidian-conventions.md` (shared across `usecase`, `arch`, and `plan`)".
  2. Line 204 (File Writing Rules): "See the Wiki Update Protocol reference below." — **this was a broken pointer with no target section**; replaced with a direct link to the new reference.
- **`plan/SKILL.md`** — line 38 (Plan Wiki Schema): one-sentence mention rewired to the new reference.

### ADR update

`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md` Next Steps Item 6 flipped from `[ ]` to `[x]` with a done note citing: reference doc location, factored skills (usecase 2-sections → 1-pointer; arch 2 rewires incl. the broken link; plan 1-sentence), and the cross-link with `frontmatter-schema.md`.

### diff stat

```
plugins/a4/references/obsidian-conventions.md  | +125 (new file)
plugins/a4/skills/usecase/SKILL.md             |  +9 / −25
plugins/a4/skills/arch/SKILL.md                |  +2 / −2
plugins/a4/skills/plan/SKILL.md                |  +1 / −1
plugins/a4/a4/2026-04-23-spec-...decide.md     |  +1 / −1
total                                          | +135 / −26
```

---

## Design decisions worth flagging

Record here so the next session doesn't relitigate.

1. **Factoring scope was intentionally tight: the three SKILLs named in the ADR (usecase, arch, plan) only.** Other skills that mechanically use `wiki_impact` / footnote markers (`auto-bootstrap`, `spark-decide`, `drift`, `compass`, `auto-usecase`) do **not** inline the protocol — they just reference the mechanics per their own workflows. They were left alone. If future work wants every protocol mention repointed at the reference, that's a separate pass.
2. **Skill-internal workflow prose stayed in the SKILLs.** Lines like `usecase/SKILL.md` §3a ("append a footnote marker + `## Changes` entry as described in the Wiki Update Protocol") or `arch/SKILL.md` Phase 3 Domain Model modifications (step-by-step procedure) are **skill-specific procedural guidance** that happens to invoke the protocol at a specific workflow point. These were preserved — they tell the reader "at this step, do the protocol thing." The reference answers "what is the protocol thing." Different audiences, different purposes.
3. **Cross-link style between the two reference docs.** `obsidian-conventions.md` links to `frontmatter-schema.md` via `[frontmatter-schema.md](./frontmatter-schema.md)` (clickable relative link). SKILLs link to both via `${CLAUDE_PLUGIN_ROOT}/references/<file>.md` (variable-expansion path, non-clickable in plain markdown but correctly resolvable by the harness). `frontmatter-schema.md` itself uses repo-relative paths in its Cross-references section (non-clickable). Mixed but consistent within each file; don't retrofit.
4. **Aliases mentioned but de-emphasized.** `[[path|display]]` syntax is documented in the reference with a "use sparingly" note — the pipe character needed prose treatment (not a table cell) because `|` inside backticks can still confuse some markdown table parsers. No strong convention; just a known tool.
5. **"Never a review item" rule on footnote payloads is explicit.** The footnote wikilink must point at the **causing issue** (UC, task, decision, architecture section heading — the last one is valid, per `arch/SKILL.md` Phase 3 example `[[architecture#SessionService]]`). Review items surface in the close guard but are **not** what the wiki records as "why this section changed." This was already the rule across both originating SKILLs; the reference doc states it explicitly now.
6. **One broken pointer fixed in passing.** `arch/SKILL.md` line 204 said "See the Wiki Update Protocol reference below" but no such section existed below it (the skill didn't inline the protocol like usecase did). Factoring naturally resolved this by replacing the pointer with a real link. Not worth a separate commit.
7. **No plugin version bump.** Following precedent from commits `72f62ac24`, `393304e57`, `537be88c8`, `851bc096a` (the previous session's validator commit) — single-item doc/reference additions do not bump `marketplace.json`. Holding the line.
8. **`usecase/references/session-closing.md` was NOT modified.** That file (line 58) says "per the Wiki Update Protocol" — a by-name reference inside a skill-internal sub-reference. It's reached from within the skill's Wrap Up flow, and the reader has already seen the top-of-skill pointer to the new canonical location. Modifying it would be scope creep. Same reasoning applies to other "per the Wiki Update Protocol" phrases inside the three main SKILLs.
9. **Spark files explicitly out of protocol scope.** The reference doc's Scope section clarifies: spark files (`spark/*.brainstorm.md`, `spark/*.decide.md`) use wikilinks in body prose but are append-only session artifacts and do **not** follow the wiki update protocol. This matches existing skill behavior (the `spark-decide` in-situ nudge, closed in the 2026-04-24_1638 handoff, updates **wiki pages**, not spark files).
10. **Frontmatter-side vs body-side split is the organizing principle.** `frontmatter-schema.md` = what goes in YAML. `obsidian-conventions.md` = what goes in body prose. They cross-link at the point where body-vs-frontmatter confusion is most likely (path format: `[[usecase/3-...]]` in body, `usecase/3-...` in frontmatter). Keep the two files' scopes clean — don't duplicate content across them.

---

## Remaining ADR Next Steps (post-session state)

From `plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`:

1. ~~Schema finalization~~ (done 2026-04-24_1700)
2. ~~Id allocator~~ (done)
3. ~~Drift detector~~ (done)
4. ~~In-situ nudge integration~~ (done — spark-decide carve-out closed 2026-04-24_1638)
5. ~~Wiki update close guard~~ (done)
6. ~~Obsidian markdown conventions doc~~ (**done this session** — Item 6 fully `[x]`)
7. ~~INDEX.md redesign~~ (done)
8. **Compass redesign** — Step 1.2 (artifact scan), Step 3 (gap diagnosis with drift detection) rewritten for the new layout. Step 0 (INDEX refresh) was already updated in a prior session.
9. ~~Skill rewrites~~ (done)
10. ~~Spark skill alignment~~ (done)
11. ~~README rewrite~~ (done — from an earlier handoff on this thread)
12. **Obsidian dataview reference snippets** — canonical dataview blocks as reference material. Seed code already in `plugins/a4/scripts/index_refresh.py`.

Also still open (tracked in prior handoffs, not an ADR Next Step):

- **`.handoff/INDEX.md`** — topic-grouped dashboard driven by `scripts/topic_references.py`. Now 12 handoffs under `plugins/a4/.handoff/` for the `a4-redesign` thread (this session being the 12th). Deferred 9 sessions running. Thread has only 2 items left (8, 12) before it can wrap — revisiting this dashboard question at thread close is worth considering.

### Recommended next session

One ADR item left plus the compass redesign. In decreasing priority:

1. **Item 12 — Obsidian dataview reference snippets.** Smallest of the two. Document the canonical dataview query blocks already living in `plugins/a4/scripts/index_refresh.py` (seven sections: Wiki pages, Stage progress, Open issues, Drift alerts, Milestones, Recent activity, Spark) as reference snippets under `plugins/a4/references/obsidian-dataview.md` (or similar filename — match the existing `frontmatter-schema.md` / `obsidian-conventions.md` naming). The source code already carries the exact queries; the task is documentation-first.
2. **Compass redesign** (separate ADR item). Step 1.2 (artifact scan) and Step 3 (gap diagnosis with drift detection) need rewriting for the new per-item layout. Higher blast radius because it touches an active skill; save for when there's appetite for it.

After Item 12 lands, the `a4-redesign` thread is effectively wrapped (with compass redesign as a separate follow-up item). A "thread-closure" handoff would be appropriate at that point, listing what's shippable end-to-end.

---

## Files intentionally NOT modified

- **Other skills referencing the protocol mechanically** — `auto-bootstrap/SKILL.md` (L250 footnote marker guidance), `spark-decide/SKILL.md` (L266 in-situ nudge, closed 2026-04-24_1638), `drift/SKILL.md`, `compass/SKILL.md`, `auto-usecase/SKILL.md`. They use `wiki_impact` and footnote markers but do not inline the Wiki Update Protocol as a named section. Out of scope for this factoring. Leave until they actually duplicate the canonical content — none do today.
- **`usecase/references/session-closing.md`** — mentions "per the Wiki Update Protocol" (line 58) and other protocol-related wording. Skill-internal sub-reference; reader reaches it through the skill's Wrap Up flow and has already seen the canonical pointer. Rewiring this would be scope creep.
- **`plugins/a4/scripts/validate_frontmatter.py`** — no changes. Body-level conventions are not something the validator enforces; the validator only touches frontmatter.
- **`plugins/a4/scripts/drift_detector.py`** — no changes. Already implements the close-guard and orphan-marker detection that the new reference describes; the reference documents behavior, not vice versa.
- **`plugins/a4/.claude-plugin/marketplace.json`** — version not bumped. See design decision 7.
- **`plugins/a4/README.md`** — the reference is an internal authoring convention, not a user-facing feature.
- **Prior `.handoff/*.md`** files — all carry DO NOT UPDATE banners. The previous handoff's "two ADR items left: 6, 12" phrasing is now stale (now just "one ADR item left: 12") but we don't retrofit.

---

## Working-tree state at handoff time

Pre-handoff commit: **`1eb7d922c`** — `docs(a4): factor Obsidian conventions into shared reference` (5 files, +135 / −26). Working tree clean after that commit, save for this handoff file.

Branch state before this handoff's commit: `main` is 10 commits ahead of `origin/main` (8 before this session + 1 pre-session from the previous session's handoff + 1 pre-handoff commit this session). Will be 11 after this handoff-file commit.

Changes bundled into this handoff's own commit:

```
new file:   plugins/a4/.handoff/2026-04-24_1710_obsidian-conventions-factor.md   # this file
```

---

## Files to read first next session

1. **`plugins/a4/references/obsidian-conventions.md`** — the new canonical reference for body-level conventions.
2. **`plugins/a4/references/frontmatter-schema.md`** — the frontmatter-side counterpart (from the previous session). Read together with obsidian-conventions.md to see the full split.
3. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — Next Steps list to confirm which items are still open. Only Item 12 + Compass redesign remain.
4. This handoff.
5. **Prior handoff `2026-04-24_1700_frontmatter-schema-and-validator.md`** — immediate predecessor; context on the schema doc that this session pairs with.
6. **If tackling Item 12 (dataview snippets):** `plugins/a4/scripts/index_refresh.py` contains the canonical query blocks (seven sections). That's the primary source. Also skim `plugins/a4/skills/index/SKILL.md` for how the script is invoked.
7. **If tackling Compass redesign:** `plugins/a4/skills/compass/SKILL.md` — specifically Step 1.2 (artifact scan) and Step 3 (gap diagnosis). Also `plugins/a4/scripts/drift_detector.py` for the Layer-2 integration point referenced in Step 3.

---

## Explicitly rejected / not done this session

- **Rewiring every "per the Wiki Update Protocol" phrase.** Only the top-of-section pointers needed updating. In-flow references stayed — they read correctly once the reader has seen the pointer. See design decision 2 and 8.
- **Factoring `auto-bootstrap`, `spark-decide`, `drift`, `compass`, `auto-usecase`.** They reference mechanics, not the named protocol as a factorable section. Out of scope. See design decision 1.
- **Bumping `marketplace.json`.** Precedent holds. See design decision 7.
- **Merging `obsidian-conventions.md` and `frontmatter-schema.md` into one big reference.** The body-vs-frontmatter split is the organizing principle; keep them separate. See design decision 10.
- **Documenting advanced Obsidian features.** Aliases got one prose mention; other advanced syntax (block references `^`, transclusion edge cases, dataview query syntax) are intentionally omitted. Item 12 will cover dataview separately.

---

## Non-goals for next session

- Do not merge the two reference docs. They are deliberately split on the body-vs-frontmatter axis.
- Do not retrofit skill prose beyond the three SKILLs factored this session. If a different skill accrues duplicated protocol content later, factor it then — don't preemptively pointer-ize files that just use the mechanics.
- Do not bolt a "validate obsidian conventions" script onto the validator. The body-level rules (footnote marker presence, Changes section format) are partially covered by the drift detector (close-guard, orphan-marker, orphan-definition); expanding to full body-convention linting is a separate decision and likely not worth the noise.
- Do not reopen the frontmatter-vs-body path-format decision. Body uses `[[usecase/3-...]]`, frontmatter uses `usecase/3-...`. Documented in both reference docs now; the split is intentional (Obsidian's wikilink parser vs dataview's YAML consumer).
