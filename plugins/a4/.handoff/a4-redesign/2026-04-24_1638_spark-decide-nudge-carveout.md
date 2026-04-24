---
timestamp: 2026-04-24_1638
topic: a4-redesign
previous: 2026-04-24_1628_spark-skill-alignment.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_1638. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: spark-decide in-situ wiki nudge (carve-out closed)

Topic thread: `a4-redesign` — continues from `.handoff/2026-04-24_1628_spark-skill-alignment.md` (per-type `status:` vocabularies + `promoted` / `supersedes` fields). This session closes the **spark-decide carve-out** under ADR Next Step "In-situ nudge integration", which the prior handoff flagged as the smallest, most bounded follow-up. With this, every single-edit skill listed in that ADR item (`usecase`, `arch`, `spark-decide`) now carries a wiki-update nudge.

Pre-handoff commit: **`537be88c8`** — `docs(a4): add spark-decide in-situ wiki nudge` (2 files, +27 / −3).

## Primary read for next session

1. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — authoritative spec-as-wiki+issues ADR. The "In-situ nudge integration" Next Step note was updated this session to record the spark-decide closure (line ~312). Remaining fully-open items: **1 (Schema finalization round)**, **6 (Obsidian markdown conventions doc)**, **12 (Obsidian dataview reference snippets)**. All other items done.
2. **`plugins/a4/skills/spark-decide/SKILL.md`** — Wrapping Up now has six steps; step 5 is the new in-situ wiki nudge. `allowed-tools` extended with `Edit`, `Bash`, `Glob`.
3. **`plugins/a4/skills/usecase/SKILL.md` §3a** — reference pattern the new spark-decide step mirrors. Lines ~214-232.
4. **`plugins/a4/skills/arch/SKILL.md`** Wrapping Up step 4 — the wiki close guard pattern that pairs with the nudge (review items transitioning to `resolved` with non-empty `wiki_impact` get footnote verification).
5. This handoff.

---

## What this session accomplished

One pre-handoff commit: **`537be88c8`**.

### The core change

Added a new step 5 to `plugins/a4/skills/spark-decide/SKILL.md` Wrapping Up, positioned **between finalize (step 4) and path report (now step 6)**. Position rationale was explicitly confirmed by the user in chat: the nudge runs *after* `status: draft → final` so the decide file is already locked when wiki-impact reasoning happens. Deferred items produce review items in `a4/review/` — the decide file is **not** re-touched by the nudge. This asymmetry (decide file frozen; wiki edits + review items as side outputs) was explicitly OK'd and should stay that way.

### Pattern mirrored from `usecase/SKILL.md §3a`

| Aspect | usecase §3a | spark-decide step 5 |
|--------|-------------|---------------------|
| When | After each UC file is written | Once per session, after finalize |
| Discover targets | Implicit (knows what was changed in the UC) | `Glob` on `a4/*.md` to find wiki pages |
| Change-type table | Inline prose bullets | Table with 5 rows (architecture / context / actors / domain / nfr) |
| Confirm flow | Footnote `[^N]` + `## Changes` line + bump `updated:` | Same |
| Defer flow | `a4/review/<id>-<slug>.md` with `kind: gap`, `source: self`, `target: <issue>`, `wiki_impact: [...]` | Same; `target: spark/<decide-basename>` (no `.md`, retains `.decide`) |
| Skip-silently condition | Minor edits per skill judgment | Same + no wiki pages in workspace (standalone decide) |

### File-by-file changes in `537be88c8`

1. **`plugins/a4/skills/spark-decide/SKILL.md`** (+27 / −1):
   - `allowed-tools` line (file L5): added `Edit`, `Bash`, `Glob`. New: `Read, Write, Edit, Agent, Bash, Glob, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode`.
   - Wrapping Up step 4 (Finalize): added a new bullet "Bump `updated:` in frontmatter to today" — previously implicit, now explicit because the nudge can trigger further `updated:` bumps on wiki pages and the finalize bump should happen exactly once on the decide itself.
   - Wrapping Up step 5: new "In-situ wiki nudge" block (~23 lines including the change-type table, the confirm-flow sub-list, the defer-flow sub-list, and the minor-decision skip guidance).
   - Wrapping Up step 6: old step 5 "Report the path" renumbered. No content change.

2. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** (+1 / −1):
   - Next Steps line for "In-situ nudge integration" (L312): *Done* note rewritten. Previously read "Done for usecase / arch; spark-decide still pending." Now records the carve-out closure with nudge position (step 5, after finalize, before path report), the mirror-pattern reference, the review-item schema specifics, and the tool extension (`Edit`, `Bash`, `Glob`).

### Validation

Not run. The change is prose-only in markdown files consumed by the SKILL loader; there is no script or schema to exercise. `plugins/a4/scripts/index_refresh.py` was not touched and continues to pass dry-run from the prior session. The nudge step itself will be exercised the next time a user runs `/a4:spark-decide` inside an `a4/` workspace.

---

## Design decisions worth flagging

Recording so the next session doesn't relitigate.

1. **Nudge runs AFTER finalize, not before.** Alternative would have been inserting the nudge before `status: draft → final` so wiki impact could conceivably influence the decision itself. Rejected because (a) by the time the user indicates they're done, the decision is decided — re-opening it for wiki reasons would confuse the facilitation flow, (b) the deferred-review-item path already handles "we found something" without needing to roll back finalization, (c) aligns with `usecase` which nudges *after* the UC is written, not before. **User explicitly confirmed this position in chat**.
2. **Decide file is frozen at the nudge step; only wiki + review items are written.** Alternative would be writing a "nudge outcome" note into the decide's Discussion Log or a new section. Rejected because the decide represents the decision, not the propagation bookkeeping. The review item's `target: spark/<decide-basename>` already provides the reverse link. **User explicitly confirmed this asymmetry in chat** — do not revisit without new reason.
3. **`Glob` discovery, not hard-coded wiki list.** Alternative: hard-code the 5 wiki basenames (`context.md`, `actors.md`, `domain.md`, `architecture.md`, `nfr.md`) into the step. Chose `Glob a4/*.md` because (a) future wiki pages (e.g., `plan.md` if `plan` writes a wiki narrative — per ADR item "Skill rewrites" note) will be picked up automatically, (b) avoids drift between this step and any future workspace-root wiki addition. The change-type table in the step documents the five known-common targets but doesn't restrict discovery to them.
4. **`target: spark/<decide-basename>` format for deferred review items.** The `.md` is dropped per ADR's "Paths are plain strings (no brackets, `.md` omitted) for dataview compatibility." The `.decide` suffix is **kept** because it is part of the filename base, not the extension — analogous to how the brainstorm `promoted:` field example in spark-brainstorm's SKILL.md points at `spark/<decide-file>` which would similarly retain `.decide`. This was NOT exhaustively verified against an existing dataview query; if a future session finds `.decide` trips the dataview resolver, strip it at that time.
5. **`allowed-tools` minimally extended.** Added only `Edit`, `Bash`, `Glob`. Did NOT add `Grep` or `TaskCreate`/`TaskUpdate`/`TaskList` even though `usecase` carries them. Rationale: spark-decide's existing prose talks about "Track confirmed items via tasks" but already works with ambient task tooling; not this session's job to plumb that declaration. Stay scoped to the carve-out.
6. **Finalize now explicitly bumps `updated:`.** Prior wording left this implicit. Because the nudge may trigger separate `updated:` bumps on wiki pages, it is worth being explicit that the decide-side bump happens exactly once, during finalize. Not a behavioral change — any correct implementation would already do this.
7. **No plugin version bump.** Precedent from prior sessions (commits `72f62ac24`, `393304e57`): carve-out-scale changes don't bump `marketplace.json`. Holding the line. If a multi-item batch bump is desired, do it as a separate dedicated commit.
8. **Legacy files stay legacy.** `plugins/a4/a4/*.decide.md` (the plugin's own ADRs) do not need a nudge retrofit — they are the spec, not output of the spark-decide skill. Unchanged policy from prior sessions.

---

## Remaining ADR Next Steps (post-session state)

From `plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md` — open items after this session:

1. **Schema finalization round** — per-type lifecycle vocabularies (now fully locked for all types), YAML date typing, comment/log section format for issues, exact YAML grammar for path references. Target doc: `plugins/a4/references/frontmatter-schema.md`. *Consolidation pass, not fresh authoring — the main ADR's `### Frontmatter schema` section is the de facto draft.*
2. ~~Id allocator~~ (done)
3. ~~Drift detector~~ (done)
4. ~~**In-situ nudge integration**~~ (**done this session** — spark-decide carve-out closed; item now fully `[x]`)
5. ~~Wiki update close guard~~ (done)
6. **Obsidian markdown conventions doc** — `plugins/a4/references/obsidian-conventions.md` to deduplicate Wiki Update Protocol sections inlined in `usecase/SKILL.md`, `arch/SKILL.md`, `plan/SKILL.md`. *Factoring, not invention.*
7. ~~INDEX.md redesign~~ (done)
8. ~~Compass redesign~~ (done)
9. ~~Skill rewrites~~ (done)
10. ~~Spark skill alignment~~ (done)
11. ~~README rewrite~~ (done)
12. **Obsidian dataview reference snippets** — canonical dataview blocks as reference material. Seed code already in `scripts/index_refresh.py`.

Also still open (tracked in prior handoffs, not an ADR Next Step):

- **`.handoff/INDEX.md`** — topic-grouped dashboard driven by `scripts/topic_references.py`. Now 10 handoffs under `plugins/a4/.handoff/` for the `a4-redesign` thread (this session being the 10th). Deferred 7 sessions running. Worth picking up soon purely on volume.

### Recommended next session

The `a4-redesign` thread has only three ADR items left (1, 6, 12), all consolidation/documentation work. In decreasing impact:

1. **Item 1 — Schema finalization** (`plugins/a4/references/frontmatter-schema.md`). Highest-value remaining item. All per-type vocabularies are locked (usecase/task/review/decision issues + brainstorm/decide sparks); the structural-relationship fields (`supersedes`, `depends_on`, `related`, `promoted`, `blocks`, `implemented_by`) are defined; the wiki page kinds are enumerated. Extraction pass consolidating what's scattered across the ADR prose into a single reference doc. Scope-bounded: one new file, no behavioral changes.
2. **Item 6 — Obsidian markdown conventions doc** (`plugins/a4/references/obsidian-conventions.md`). Three SKILLs (`usecase`, `arch`, `plan`) currently inline a Wiki Update Protocol section each. Factor to one reference doc, replace inline copies with a short pointer + link. Lower blast radius because it's also documentation.
3. **Item 12 — Obsidian dataview reference snippets**. Smallest of the three. Document the query patterns already living in `scripts/index_refresh.py` as reference snippets.

Second-tier:

- **`.handoff/INDEX.md` dashboard** — 10 handoffs on one thread justifies this now.

After the three ADR items are closed, the entire `a4-redesign` thread is wrapped. A final "thread-closure" handoff naming what's shippable would be appropriate.

---

## Files intentionally NOT modified

- **`plugins/a4/skills/spark-decide/references/adr-template.md`** — no change. The template reflects final-state ADR frontmatter and body; the nudge runs on the wiki side, not the decide side, so the ADR template is unaffected.
- **`plugins/a4/skills/spark-brainstorm/SKILL.md`** — brainstorm is a generative skill whose output feeds into other skills. The nudge pattern only applies to skills that commit to a single-edit decision; brainstorm does not. Untouched.
- **`plugins/a4/skills/usecase/SKILL.md` / `arch/SKILL.md` / `plan/SKILL.md`** — already carry their nudge patterns per the ADR's "In-situ nudge integration" item. Untouched.
- **`plugins/a4/scripts/index_refresh.py` / `allocate_id.py` / `drift_detector.py`** — no logic change required. The drift detector already understands `wiki_impact` and `source: self`, both of which the new nudge uses.
- **`plugins/a4/.handoff/*.md`** prior handoffs — all carry `DO NOT UPDATE` banners. Not retrofitting despite any wording that's now slightly stale (e.g., prior handoff's "spark-decide still pending" phrasing).
- **`plugins/a4/README.md`** — nudge is a wrap-up mechanic inside the spark-decide skill; not surfaced at README level. Leave alone.
- **`plugins/a4/.claude-plugin/marketplace.json`** version — not bumped. See design decision 7.

---

## Working-tree state at handoff time

Pre-handoff commit: **`537be88c8`** — `docs(a4): add spark-decide in-situ wiki nudge` (2 files, +27 / −3). Working tree clean after that commit, save for this handoff file.

Branch state before this handoff's commit: `main` is 6 commits ahead of `origin/main` (= 5 before this session + 1 pre-handoff commit). Will be 7 after this handoff-file commit.

Changes bundled into this handoff's own commit:

```
new file:   plugins/a4/.handoff/2026-04-24_1638_spark-decide-nudge-carveout.md   # this file
```

---

## Files to read first next session

1. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — Next Steps list; note items 1, 6, 12 are the only open ADR-level work. The "In-situ nudge integration" item is now fully `[x]` with no carve-out.
2. **`plugins/a4/skills/spark-decide/SKILL.md`** Wrapping Up — the newly-added step 5 (wiki nudge) and the renumbered step 6 (report path). Read alongside `usecase/SKILL.md §3a` to confirm the pattern mirror.
3. This handoff — narrative wrapper.
4. **Prior handoff `2026-04-24_1628_spark-skill-alignment.md`** — immediate predecessor on the thread; captures the per-type `status:` vocabulary decisions that this session's nudge assumes.
5. **If tackling Item 1 (schema finalization):** the main ADR's `### Frontmatter schema` section is the extraction source.
6. **If tackling Item 6 (obsidian conventions doc):** `usecase/SKILL.md` Wiki Update Protocol section (lines 88-112), `arch/SKILL.md` "Wiki Page Schema" + "File Writing Rules" sections, and any inline Wiki Update Protocol text in `plan/SKILL.md`. Factor these into one doc.
7. **If tackling Item 12 (dataview snippets):** read `plugins/a4/scripts/index_refresh.py` for the canonical query blocks.

---

## Explicitly rejected / not done this session

- **Adding the nudge to `spark-brainstorm`.** Brainstorm outputs don't represent committed decisions, so there is nothing for a wiki page to reflect yet — the brainstorm-to-decide promotion is where wiki impact would surface, and that already runs through spark-decide's new step 5. Out of scope.
- **Retrofitting `plan` with a matching nudge step.** Not this session's carve-out. The ADR item's top-level language ("each single-edit skill ... etc.") covers plan, but this session's closure note is scoped to spark-decide. Separate follow-up if found missing.
- **Plugin version bump.** See design decision 7.
- **Updating `adr-template.md`.** The template reflects decide-side state only; nudge side effects land in wiki pages and review items, not in the ADR body.
- **Adding a `Grep` / `TaskCreate` / `TaskUpdate` / `TaskList` allowance to `spark-decide`.** See design decision 5.

---

## Non-goals for next session

- Do not re-touch `spark-decide/SKILL.md` Wrapping Up without a new substantive reason — the nudge was just added and the position (after finalize, before path report) is confirmed.
- Do not move the nudge before the finalize step — the post-finalize position is a deliberate design choice and was user-confirmed.
- Do not write a "nudge outcome" note into the decide's Discussion Log or any new decide-side section. The review item's `target:` field is the reverse link; the decide stays frozen.
- Do not hard-code the wiki basename list in the nudge step — `Glob` discovery is deliberate so future wiki kinds are picked up.
- Do not strip `.decide` from the `target:` path format without first confirming via an actual dataview query that it causes resolution issues.
