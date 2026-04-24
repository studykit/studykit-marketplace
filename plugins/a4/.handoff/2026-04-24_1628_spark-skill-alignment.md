---
timestamp: 2026-04-24_1628
topic: a4-redesign
previous: 2026-04-24_1615_readme-and-compass-redesign.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_1628. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: Spark skill alignment (ADR Next Step 7 — root-cause closure)

Topic thread: `a4-redesign` — continues from `.handoff/2026-04-24_1615_readme-and-compass-redesign.md` (README rewrite + compass redesign). This session closes **Item 7 (Spark skill alignment)**, which is the **root cause** that triggered the entire `a4-redesign` thread six sessions ago. The status-field collision that originally surfaced in `spark/*.md` frontmatter (doc-state `status: draft | final` vs. spark-lifecycle `status: open | promoted | discarded`) is now resolved via per-type lifecycle vocabularies — the same pattern already used by issue types.

Pre-handoff commit: **`393304e57`** — `docs(a4): align spark skill frontmatter with wiki+issue schema` (6 files, +27 / −12).

## Primary read for next session

1. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — authoritative spec-as-wiki+issues ADR. Next Steps list now has Items 2, 5, 6, 7, 9 marked `[x]` and partial-done for "In-situ nudge integration" and "Wiki update close guard". Remaining fully-open items: 1, 3, 4, 8.
2. **`plugins/a4/a4/2026-04-24-skill-naming-convention.decide.md`** — naming ADR (unchanged this session).
3. **`plugins/a4/skills/spark-brainstorm/SKILL.md`** and **`plugins/a4/skills/spark-decide/SKILL.md`** — canonical templates now carry full wiki+issue schema. Both are what skills emit on save.
4. **`plugins/a4/skills/spark-decide/references/adr-template.md`** — final-state ADR form; mirrors `spark-decide/SKILL.md` at Phase 5 output.
5. **`plugins/a4/scripts/index_refresh.py`** — `SPARK_TERMINAL` is now a flavor-aware dict (see Design decisions §3).
6. This handoff.

---

## What this session accomplished

One pre-handoff commit: **`393304e57`**.

### The core schema change

Per-type `status:` vocabularies (same pattern as issue types — `usecase`, `task`, `review`, `decision` already have distinct vocabularies per the ADR):

| Kind | Status values |
|------|---------------|
| brainstorm | `open \| promoted \| discarded` |
| decide | `draft \| final \| superseded` |

Both sparks also gained:

- `pipeline: spark` — matches the pre-existing `pipeline:` convention on the plugin's own ADRs.
- `created:` + `updated:` — replaces legacy single `date:` field; aligns with issue schema where both fields carry meaning (activity timestamps drive the Recent Activity section of INDEX).

Brainstorm-specific addition:

- `promoted: []` — forward-direction list of paths this brainstorm was promoted to (e.g., `[spark/<decide-file>, usecase/<n>-<slug>]`). **Named `promoted`, not `graduated_to`** — the ADR's rejected-alternatives cell passing-referenced `graduated_to`, but this session chose `promoted` because it reads coherently with `status: promoted` ("status is promoted, promoted to where → this list"). The ADR's one prose mention was updated in the same commit so the ADR and skills are lexically consistent.

Decide-specific addition:

- `supersedes: []` — paths to prior `decide` files this one replaces. The `supersedes` relationship is already defined in the ADR's structural-relationships table; adding it to the decide template simply plumbs it through.

### File-by-file changes in `393304e57`

1. **`plugins/a4/skills/spark-brainstorm/SKILL.md`** — frontmatter template (inside the File Format code fence) rewritten. Inline YAML comments describe the enum values and when `promoted:` gets filled. No behavioral changes to the skill prose — the Situation Assessment / Technique Selection / Facilitation Guidelines / Wrapping Up flow is unchanged. Only the emitted frontmatter schema changed.
2. **`plugins/a4/skills/spark-decide/SKILL.md`** — initial-file-content template (after Phase 1 Problem Framing) rewritten with the new schema. The other `status:` mentions in the file (L96 "keep the `status: draft` marker until wrap-up", L243 "change `status: draft` to `status: final`") were intentionally left as-is because `draft` is still the working-state value under the new schema — the semantics only extend (new `superseded` value added, `pipeline:` and relationship fields introduced), they do not change for the `draft → final` flow.
3. **`plugins/a4/skills/spark-decide/references/adr-template.md`** — final-output template (what the file looks like after Phase 5 finalize). Mirrors the SKILL.md initial template but with `status: final` as the shown value.
4. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — two edits:
   - Rejected-alternatives row: `graduated_to` → `promoted` (one-word lexical sync).
   - Next Steps Item 7: `[ ]` → `[x]` with a long inline *Done* note capturing the per-type vocabularies, the new fields, the rename rationale, and the files touched. The note explicitly carves out the in-situ nudge for spark-decide as remaining under a **different** Next Step.
5. **`plugins/a4/scripts/index_refresh.py`** — two behavior-affecting changes:
   - `SPARK_TERMINAL` changed from `{"promoted", "discarded"}` (flat set) to a flavor-aware dict: `{"brainstorm": {"promoted", "discarded"}, "decide": {"final", "superseded"}}`. This fixes a pre-existing latent bug where a legacy decide with `status: final` (the prior doc-state value) was classified as non-terminal and would have appeared in "open sparks" forever.
   - Dataview query in `section_spark`: `WHERE !status OR status = "open"` → `WHERE !status OR status = "open" OR status = "draft"`. The Obsidian dataview block doesn't know the flavor of a row, so we enumerate the non-terminal values across both flavors (`open` = new brainstorm open; `draft` = new decide working state). Missing-status fallback preserved for legacy files.
6. **`plugins/a4/skills/index/SKILL.md`** — Spark-row description in the section table updated from "where status is missing or `open`" to "excluding terminal states (brainstorm: `promoted`/`discarded`; decide: `final`/`superseded`)".

### Validation

`uv run scripts/index_refresh.py a4/ --dry-run` on the plugin's own workspace executes cleanly. Output Spark section shows "open 0" because `plugins/a4/a4/` is legacy layout (ADR files sit at root, not under `spark/`) — per the ADR's "no migration for legacy" decision. Dataview query in rendered output contains the new `OR status = "draft"` clause.

---

## Design decisions worth flagging

These shaped the rewrite — recording so the next session doesn't relitigate.

1. **Per-type status vocabularies, not a separate lifecycle field.** The original conflict could have been resolved by adding a second field (e.g., `status: draft|final` for doc-state plus `lifecycle: open|promoted|discarded` for spark-lifecycle). Rejected because the ADR already establishes per-type `status:` vocabularies for issues (usecase `draft|implementing|done|blocked`; task `pending|implementing|complete|failing`; review `open|in-progress|resolved|dismissed`; decision `final`). Extending the same pattern to brainstorm and decide is the consistent move. Reader mental load stays the same: "the `type:` field tells you what vocabulary `status:` draws from."
2. **`promoted` over `graduated_to` as the forward-link field name.** The ADR's rejected-alternatives cell used `graduated_to` as an example name when arguing against adding `origin:` to usecase. That mention was not normative — chose `promoted` in implementation because it pairs semantically with `status: promoted` and is shorter. Lexically synced the ADR in the same commit so future searches converge on one name.
3. **`SPARK_TERMINAL` as flavor-aware dict, not a union.** Simpler alternative: `SPARK_TERMINAL = {"promoted", "discarded", "final", "superseded"}` (union) works because the values don't collide across flavors. Chose flavor-aware because (a) it matches the per-type style of `TERMINAL_STATUSES` for issues just above it, (b) if a future status value did collide across flavors, the union would silently misclassify.
4. **Dataview query enumerates non-terminal values instead of negating terminals.** `WHERE !status OR status = "open" OR status = "draft"` is more brittle than `WHERE status != "promoted" AND status != "discarded" ...` but preferred because: (a) positive filters are readable, (b) under the new schema there are only two non-terminal values total across both flavors, (c) adding a new spark flavor in the future would require updating this query anyway regardless of style.
5. **No in-situ wiki-update nudge added to spark-decide this session.** The Next Step note "spark-decide still pending" for the nudge integration technically belongs to a different ADR item ("In-situ nudge integration"), which is marked `[x]` but with the spark-decide carve-out. Keeping Item 7 strictly scoped to "frontmatter schema alignment" (which is how the ADR itself phrased the step) lets that other item be closed cleanly in a future session without a dependency chain.
6. **No plugin version bump.** Precedent from the prior session (README+compass rewrite, commit `72f62ac24`) landed a comparable-scope change without bumping `marketplace.json`. Not bumping here too. If the user wants to bump across multiple closed Next Steps at once, that's a separate commit.
7. **Legacy files stay as-is.** Reaffirmed from the main ADR's Rejected Alternatives: no migration tooling. `plugins/a4/a4/*.decide.md` (the plugin's own ADRs, including the one edited this session) live in legacy layout — they use `date:` not `created:`/`updated:`, and they're at workspace root rather than under `spark/`. The new schema applies only to new workspaces and new outputs going forward.

---

## Remaining ADR Next Steps (post-session state)

From `plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md` — open items after this session:

1. **Schema finalization round** — per-type lifecycle vocabularies (now fully locked for all types including sparks), YAML date typing (for dataview), comment/log section format for issues, exact YAML grammar for path references. Target doc: `plugins/a4/references/frontmatter-schema.md`.
2. ~~Id allocator~~ (done — prior session)
3. ~~Drift detector~~ (done — prior session)
4. **In-situ nudge integration** — marked `[x]` but with "`spark-decide` still pending" carve-out. Adding the nudge step to spark-decide's Wrapping Up phase would fully close this item.
5. ~~Wiki update close guard~~ (done — prior session)
6. **Obsidian markdown conventions doc** — `plugins/a4/references/obsidian-conventions.md` to deduplicate Wiki Update Protocol sections inlined in `usecase/SKILL.md`, `arch/SKILL.md`, `plan/SKILL.md`.
7. ~~INDEX.md redesign~~ (done)
8. ~~Compass redesign~~ (done — prior session)
9. ~~Skill rewrites~~ (done — prior session)
10. ~~Spark skill alignment~~ (**done this session**)
11. ~~README rewrite~~ (done — prior session)
12. **Obsidian dataview reference snippets** — canonical dataview blocks as reference material. Seed code already in `scripts/index_refresh.py`.

Also:

- **`.handoff/INDEX.md`** — topic-grouped dashboard driven by `scripts/topic_references.py`. Deferred 6 sessions running; the `a4-redesign` thread now has 9 handoffs under `plugins/a4/.handoff/` (this session being the 9th, one past the prior handoff's count). This was a second-tier candidate in the prior handoff.

### Recommended next session

The `a4-redesign` thread is **functionally complete** with this session — the root-cause Item 7 is closed and every ADR Next Step is either done or carved out as a narrow follow-up. Three reasonable next sessions, ordered by decreasing coupling to a4-redesign:

1. **Close the "spark-decide nudge" carve-out** (part of ADR Item "In-situ nudge integration"). Small, bounded work: add a wrap-up step in `spark-decide/SKILL.md` after the decision-reviewer agent runs, asking "does this decision require a wiki update?" Using the already-loaded decision context, open a review item with `wiki_impact:` if yes. Pattern to copy: whatever `usecase/` and `arch/` SKILLs do (the prior session confirmed their nudge integration is working). After this, the In-situ nudge item is cleanly `[x]`.
2. **Item 1 — Schema finalization** (`plugins/a4/references/frontmatter-schema.md`). Now that all types (including sparks) have locked lifecycle vocabularies, this is a consolidation pass: collect the informal schema definitions currently scattered across the main ADR prose into one reference doc. Serves as the authoritative schema spec for future skill rewrites.
3. **Item 3 — Obsidian markdown conventions doc** (`plugins/a4/references/obsidian-conventions.md`). Three SKILLs (`usecase`, `arch`, `plan`) currently inline a Wiki Update Protocol section each. Factor to one reference doc and replace inline copies with a pointer.

Second-tier:

- **`.handoff/INDEX.md`** dashboard — 9 handoffs on one thread is enough to justify a dashboard.
- **Item 12 — Obsidian dataview reference snippets** — document the query patterns already in `index_refresh.py`.

---

## Files intentionally NOT modified

- **`plugins/a4/.handoff/*.md`** — all prior handoffs carry `DO NOT UPDATE` banners. Two of them (`2026-04-23_2119` at L41 and L84) reference `graduated_to` as part of their historical record; those references are **correct for the state at that time** and must not be retroactively edited to say `promoted`.
- **`plugins/a4/a4/*.decide.md` other than `2026-04-23-spec-as-wiki-and-issues.decide.md`** — the plugin's own other ADRs (`2026-04-12-think-pipeline-restructuring.decide.md`, `2026-04-24-skill-naming-convention.decide.md`) use the legacy layout by design (plugin's own workspace predates its own redesign). Don't retrofit them to the new schema.
- **`plugins/a4/README.md`** — spark skill schema is not surfaced at README level (only skill catalog); no mention to update. Leaving untouched.
- **`plugins/a4/.claude-plugin/plugin.json`** (none present anyway — versioning is at marketplace level). Not bumping version (see design decision 6).
- **`plugins/a4/skills/spark-decide/SKILL.md` Wrapping Up section** — did not add the wiki-update nudge here; it is the carve-out and belongs to a follow-up session (see Design decision 5 and Recommended next session).

---

## Working-tree state at handoff time

Pre-handoff commit: **`393304e57`** — `docs(a4): align spark skill frontmatter with wiki+issue schema` (6 files, +27 / −12). Working tree clean after that commit, save for this handoff file.

Branch state before this handoff's commit: `main` is 18 commits ahead of `origin/main` (= 17 before prior handoff-file commit + 1 pre-handoff commit). Will be 19 after this handoff-file commit.

Changes bundled into this handoff's own commit:

```
new file:   plugins/a4/.handoff/2026-04-24_1628_spark-skill-alignment.md   # this file
```

---

## Files to read first next session

1. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — Next Steps list; note that Item 7 is now `[x]` and the thread is effectively complete.
2. **`plugins/a4/skills/spark-brainstorm/SKILL.md`** and **`plugins/a4/skills/spark-decide/SKILL.md`** — post-session schema. Read alongside the ADR's Frontmatter Schema section (the `### Per-type schemas` block) to confirm the per-type pattern.
3. **`plugins/a4/scripts/index_refresh.py`** — if the next session touches the INDEX view, note the flavor-aware `SPARK_TERMINAL` dict.
4. This handoff — narrative wrapper.
5. **Prior handoff `2026-04-24_1615_readme-and-compass-redesign.md`** — immediate predecessor on the thread.
6. **If tackling the "spark-decide nudge" carve-out (Recommended Next Session 1):** `plugins/a4/skills/usecase/SKILL.md` and `plugins/a4/skills/arch/SKILL.md` Wrapping Up sections — pattern to mirror.
7. **If tackling Item 1 (schema finalization):** the main ADR's `### Frontmatter schema` section is already the de facto draft — extraction and consolidation, not fresh authoring.

---

## Explicitly rejected / not done this session

- **Plugin version bump.** Prior session precedent; not bumping without a batch reason.
- **Migrating the plugin's own legacy `a4/` ADRs to the new schema.** Legacy-stays-as-is per ADR.
- **Adding the in-situ wiki-update nudge to spark-decide.** Different ADR Next Step item; kept scope tight to frontmatter schema alignment.
- **Creating `plugins/a4/references/frontmatter-schema.md`.** That's Item 1 — not this session's item.
- **Editing prior handoffs to reflect the `graduated_to` → `promoted` rename.** They are point-in-time snapshots; banner says do not edit. The ADR (a living document) is the one that got the rename.

---

## Non-goals for next session

- Do not re-touch the spark SKILL files or their templates without a new substantive reason — they were just rewritten.
- Do not re-open the `promoted` vs `graduated_to` naming; the lexical sync is final.
- Do not add a `lifecycle:` field (or any second status-like field) to sparks — the per-type `status:` vocabulary IS the resolution.
- Do not expand spark-decide's Wrapping Up to include a wiki-update nudge unless explicitly doing the In-situ nudge carve-out (it's bounded work but bundle it with that item, not with another).
