---
timestamp: 2026-04-24_1615
topic: a4-redesign
previous: 2026-04-24_1602_plugin-rename-and-naming-adr.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_1615. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: README rewrite + compass redesign (ADR Next Steps 9 & 6)

Topic thread: `a4-redesign` — continues from `.handoff/2026-04-24_1602_plugin-rename-and-naming-adr.md` (plugin rename think→a4, skill-naming ADR, 1.0.0 milestone). This session clears two of the remaining ADR Next Steps in a single pre-handoff commit (`72f62ac24`): **Item 9 (README rewrite)** and **Item 6 (compass redesign — Steps 1–3 rewritten for the new layout)**. Both touch the same "what does the current workspace layout look like" narrative, which is why the prior handoff flagged them as a natural pair.

## Primary read for next session

1. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — the authoritative spec-as-wiki+issues ADR. Its Next Steps section is the remaining-work checklist; items 9 and 6 are now done.
2. **`plugins/a4/a4/2026-04-24-skill-naming-convention.decide.md`** — the naming ADR (from the prior session). Read before adding any new skill.
3. **`plugins/a4/README.md`** — now reflects the new workspace model; scan the "Document Layout" section to see the canonical framing this session settled on.
4. **`plugins/a4/skills/compass/SKILL.md`** — now fully aligned with the new layout. Steps 1–3 are the rewrite target; Step 0 was already compliant before this session.

This handoff is the narrative wrapper around the two rewrites.

---

## What this session accomplished

One commit before the handoff: **`72f62ac24`** — `docs(a4): align README and compass with spec-as-wiki+issues layout` (2 files, +111 / −109).

### Item 9 — README rewrite (`plugins/a4/README.md`)

Four edits:

1. **Description line** — from `Co-thinking plugin — usecase/spec/implementation-plan design, autonomous code execution, brainstorming, decision-making, and GitHub automation.` to `Manages a4/ as a git-native wiki + issue tracker — usecase, architecture, and implementation-plan authoring, plus autonomous execution, brainstorming, and decision records.` The new line centers on workspace management, drops "GitHub automation" (never was a notable feature), and matches the ADR framing.
2. **Prerequisites** — `Think agents use this shared skill...` → `a4 agents use this shared skill...`. Stray rename-era leftover.
3. **Skills table** — added three missing entries: `handoff` (point-in-time session snapshot), `drift` (wiki-drift detector), `index` (regenerates `a4/INDEX.md`). Placed after `compass` to group orchestration skills together. Existing entries preserved in original order.
4. **"Document Layout" section** — full rewrite. Removed pre-ADR content (`<topic-slug>.usecase.md` / `<topic-slug>.arch.md` stage files, five-icon INDEX vocabulary, `reflected_files` frontmatter). Replaced with the new six-subsection model:
   - Intro paragraph + directory tree
   - **Wiki vs. issues** — the core duality
   - **Conventions** — global monotonic ids, `<id>-<slug>.md` naming, Obsidian markdown, forward-only relationships
   - **Wiki update protocol** — footnote markers, three entry paths, close guard
   - **Derived views** — UC diagram / auth matrix rendered on demand
   - **Workspace dashboard** — INDEX.md with 7 sections
   - **Archive** — folder = flag

Scope was deliberately **not** expanded to rewrite the Agents table — pre-existing and not flagged by the prior handoff. Left as-is.

### Item 6 — compass redesign (`plugins/a4/skills/compass/SKILL.md`)

Six edits:

1. **Removed legacy-note banner** (previously at L43–44 flagging Steps 1–3 as out of sync).
2. **Step 1.1 — Resolve the argument** (rewritten). Argument shapes now supported:
   - Specific target: integer id (`3`, `#3`), folder-qualified path (`usecase/3-search-history`, `review/6-...`), wiki basename (`context`, `domain`, `architecture`, `actors`, `nfr`, `plan`, `bootstrap`), or full `a4/…` path.
   - Free-text description → Step 2 (Fresh Start).
   - Empty argument → route by workspace state: empty `a4/` → Step 2; non-empty → Step 3 (workspace-wide diagnosis).
   - Archive restore prompt preserved.
3. **Step 1.2** — old artifact glob scan deleted. Replaced with a brief note pointing back to Step 0's `index_refresh.py` as the source of workspace state. No re-scan.
4. **Step 3 — fully rewritten as "Gap Diagnosis"**:
   - **3.1 Detect drift** — runs `drift_detector.py` at Step 3 start (per ADR: "every compass invocation runs drift detection as part of gap diagnosis"). Regenerates INDEX if new items were written.
   - **3.2 Read workspace state** — pulls from the regenerated `INDEX.md` + targeted file body read if Step 1.1 resolved a specific target.
   - **3.3 Diagnose the gap layer** — six-layer waterfall: 0) Workspace foundation (no UCs), 1) Wiki foundation (missing wiki pages), 2) Drift alerts (high priority first), 3) Open review items (non-drift, sorted by priority / created), 4) Active tasks, 5) Blocked items (trace `depends_on`), 6) Completion. Each layer routes to the owning iteration skill (`/a4:usecase iterate`, `/a4:arch iterate`, `/a4:plan iterate`) based on `target:` or `wiki_impact:`.
   - **3.4 Present diagnosis** — presentation table shifted from `Stage | Artifact | Status` to `Wiki pages | Open issues | Drift alerts | Milestones`. Recommendation form is `/a4:<skill> [iterate]`; args passed as `<target ref or 'iterate'>`.
   - **3.5 Archive suggestion** — reworked from "archive all `<topic>.*.md`" to per-item archive of a specifically-resolved closed target. Workspace-wide batch archive is no longer suggested (rare, user-driven).
5. **`argument-hint`** — `<topic slug, file path, or description of what you need>` → `<issue id, path (e.g. usecase/3-search-history), wiki basename, or free-text description>`.
6. **Step 0.3 & Step 2 intro cleanup** — Step 0.3 said "before entering Step 2" for no-argument case; with the new routing (empty args + non-empty workspace → Step 3), that text was wrong. Changed to "before entering Step 1". Step 2 intro changed from "The user has no existing artifacts or described a vague intent" to "The workspace is empty or the user described a vague intent" for vocabulary alignment.

The top-level title ("Pipeline Navigator") and the one-line description at L10 were kept — "pipeline" still refers correctly to the a4 production pipeline (usecase → arch → plan).

---

## Design decisions worth flagging

These shaped the rewrite; noting so the next session doesn't relitigate them:

1. **Empty-args routing split (Step 2 vs. Step 3).** The prior compass routed empty args → Step 2 always. New: empty + empty workspace → Step 2; empty + non-empty workspace → Step 3 (workspace-wide diagnosis, no specific target). Rationale: on an active workspace, "where am I?" is a diagnosis question, not a skill-catalog question. Step 0.3's INDEX summary still runs first either way.
2. **Drift detection embedded in Step 3.1, not optional.** Per ADR: "every compass invocation runs drift detection as part of gap diagnosis; catches accumulated drift between sessions." The standalone `/a4:drift` skill remains for mid-session manual checks, but compass does not rely on the user invoking it. Compass runs the detector in write-mode (not `--dry-run`) so new drift items materialize as reviewable files.
3. **Recommendation target passthrough.** Step 3 recommendations now pass a target ref (`review/6-...`, `usecase/3-...`, `architecture`) rather than a stage-file path. Iteration skills (`/a4:usecase iterate`, `/a4:arch iterate`, `/a4:plan iterate`) are responsible for resolving these. Verified via `argument-hint` inspection on usecase/arch/plan SKILL.md — all accept "iterate" as a mode and can be given a target.
4. **Per-item archive, not whole-topic archive.** Old compass offered `git mv a4/<topic>.*.md a4/archive/`. The new model has no topic scope; items are archived individually when their status reaches a terminal state. Compass only offers this when Step 1.1 resolved a specific target. Batch archive isn't suggested because a workspace-complete state is rare and user-driven.
5. **Six layers, not three+bootstrap.** The old waterfall had `Layer 1 UC / Layer 2 Arch / Layer 2.5 Bootstrap / Layer 3 Plan+Implementation+Testing`. The new six-layer (0: foundation / 1: wiki / 2: drift / 3: non-drift reviews / 4: active tasks / 5: blocked / 6: completion) better reflects the new data model where wiki presence, drift alerts, and review-item priority are all first-class gates. Bootstrap is subsumed — it's "wiki page missing" in Layer 1 (recommend `/a4:auto-bootstrap`) or "bootstrap has failures" which surfaces as arch-targeted review items in Layer 3.
6. **README Agents table untouched.** Pre-existing table entries (`iu-implementer`, `plan-reviewer`, `usecase-composer`, etc.) may or may not still be accurate post-skill-rewrite (ADR Next Step "Skill rewrites" is marked done but the agent roster post-rewrite was not verified this session). The handoff flagged only the Skills-table staleness explicitly; keeping Agents as a future audit.

---

## Files intentionally NOT modified

- **`plugins/a4/.handoff/*.md`** — all prior handoffs carry `DO NOT UPDATE THIS FILE` banners. Their content references the pre-rewrite compass and pre-ADR README; this is correct historical record.
- **`plugins/a4/skills/compass/SKILL.md` Step 0 (L14–40)** — already compliant with the new layout (regenerates via `index_refresh.py`). No changes needed.
- **`plugins/a4/skills/compass/SKILL.md` Step 2 tables** — skill catalog reflects current production skills correctly. Orchestration skills (`handoff`, `drift`, `index`) deliberately not added: Step 2 is "Fresh Start" (entry points for starting something new); `handoff` / `drift` / `index` are session-maintenance tools invoked contextually by `/` commands, not starting points.
- **README Agents table** — see design decision 6 above. Not in this session's scope.

---

## Remaining ADR Next Steps (post-session state)

From `plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md` — open items after this session:

1. **Schema finalization** — per-type lifecycle vocabularies, YAML date typing, comment/log section format, path reference grammar. → `plugins/a4/references/frontmatter-schema.md` or equivalent.
2. ~~Drift detector~~ (done)
3. **Obsidian markdown conventions doc** — `plugins/a4/references/obsidian-conventions.md` to deduplicate Wiki Update Protocol sections inlined in `usecase/SKILL.md`, `arch/SKILL.md`, `plan/SKILL.md`.
4. **`.handoff/INDEX.md`** — topic-grouped dashboard driven by `scripts/topic_references.py`. Deferred 5 sessions running; the `a4-redesign` thread now has 8 handoffs under `plugins/a4/.handoff/` (including this one).
5. ~~a4/INDEX.md redesign~~ (done)
6. ~~Compass redesign~~ (**done this session**)
7. **Spark skill alignment** — `spark-brainstorm` and `spark-decide` still need their own lifecycle frontmatter. The status-field conflict that originally triggered the entire redesign is still unresolved in the spark files themselves. **This is the root cause of the whole redesign thread — strongest candidate for next session.**
8. **Obsidian dataview reference snippets** — seed material already in `scripts/index_refresh.py`.
9. ~~README rewrite~~ (**done this session**)

**Recommended next session: Item 7 (Spark skill alignment).** The redesign was triggered six sessions ago by exactly this conflict (doc-state `status: draft | final` vs. spark-lifecycle `status: open | promoted | discarded` colliding in `spark/*.md` frontmatter). Every other Next Step has been addressed except this root-cause one. Closing the loop here would formally end the `a4-redesign` thread.

Second-tier candidates:

- **Item 1 (schema finalization)** — many "sketched but not locked" fields still live informally in the ADR. Formalizing them into `references/frontmatter-schema.md` would let future skill rewrites reference a single source instead of re-deriving from the ADR prose.
- **Item 3 (Obsidian conventions doc)** — `usecase`, `arch`, `plan` SKILLs each inline a Wiki Update Protocol section. Factoring out to `references/obsidian-conventions.md` would deduplicate and lock the conventions in one place.
- **Item 4 (`.handoff/INDEX.md`)** — 8 handoffs on a single thread is now enough that a dashboard has tangible value. `scripts/topic_references.py` already has seed code.

---

## Working-tree state at handoff time

Pre-handoff commit: `72f62ac24` — `docs(a4): align README and compass with spec-as-wiki+issues layout` (2 files, +111 / −109). Working tree clean after that commit.

Branch state before this handoff's commit: `main` is 16 commits ahead of `origin/main` (= 15 before prior handoff + 1 pre-handoff commit). Will be 17 after the handoff-file commit.

Changes bundled into this handoff's own commit:

```
new file:   plugins/a4/.handoff/2026-04-24_1615_readme-and-compass-redesign.md   # this file
```

---

## Files to read first next session

1. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — Next Steps section is the authoritative remaining-work list.
2. **`plugins/a4/a4/2026-04-24-skill-naming-convention.decide.md`** — naming ADR, read before touching any skill.
3. **`plugins/a4/README.md`** — post-rewrite; reflects the current workspace model.
4. **`plugins/a4/skills/compass/SKILL.md`** — post-rewrite; verify the six-layer logic still reads cleanly.
5. **This handoff** — narrative wrapper.
6. **`plugins/a4/.handoff/2026-04-24_1602_plugin-rename-and-naming-adr.md`** — prior handoff on this thread.
7. **If tackling Item 7 (Spark alignment):** `plugins/a4/skills/spark-brainstorm/SKILL.md`, `plugins/a4/skills/spark-decide/SKILL.md`, and any existing `a4/spark/*.md` files to understand the current frontmatter collision.

---

## Explicitly rejected / not done this session

- **Rewriting the README Agents table.** Out of scope; pre-existing, not in handoff-flagged staleness list.
- **Adding orchestration skills (`handoff`, `drift`, `index`) to Step 2 "Fresh Start" tables in compass.** Step 2 is entry points; these are session tools. Keeping the catalog focused.
- **Auto-committing `INDEX.md` from compass.** Step 0 explicitly does not commit — left in working tree for the user or session-closing to pick up. No change to that policy.
- **Bundling Item 7 (Spark alignment) into this session.** Two major rewrites in one session is already the cap; Spark alignment needs its own focused round — see Next Steps reasoning.
- **Editing prior handoffs to reflect the new compass / README.** They are point-in-time snapshots; banner says do not edit.
- **Verifying post-rewrite agent roster.** The README Agents table may reference agents that were renamed or removed during the "Skill rewrites" ADR Next Step (marked done). Audit is out of scope for this session.

---

## Non-goals for next session

- Do not re-touch README or compass for minor polish without a substantive reason — they were just rewritten.
- Do not add orchestration skills to compass Step 2 tables.
- Do not re-expand the compass waterfall to include a Bootstrap layer — bootstrap lives in Layer 1 (wiki missing → recommend `/a4:auto-bootstrap`) and Layer 3 (arch-targeted review items).
- Do not use `<topic-slug>` vocabulary anywhere — the single-workspace model eliminated topic scope.
