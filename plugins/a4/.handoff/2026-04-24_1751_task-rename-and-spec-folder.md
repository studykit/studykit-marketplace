---
timestamp: 2026-04-24_1751
topic: a4-redesign
previous: 2026-04-24_1732_dataview-reference-and-body-validator.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_1751. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: iu-implementer → task-implementer rename + `plugins/a4/a4/` → `plugins/a4/spec/` folder rename + IU residue cleanup

Topic thread: `a4-redesign` — continues from `.handoff/2026-04-24_1732_dataview-reference-and-body-validator.md` (dataview reference + body-convention validator). This session is a cleanup pass triggered by the user noticing a terminology inconsistency in the ADR — pulled the thread and found residual `iu-implementer` / `IU` references from before the plan→task rename (earlier continuation round of the same ADR), plus the long-standing `plugins/a4/a4/` self-referential folder name. No new ADR items opened; the single remaining Next Step (Compass redesign) is still open.

Pre-handoff commit: **`9b3ff6894`** — `refactor(a4): rename iu-implementer→task-implementer and a4/→spec/` (13 files, +46 / −52).

## Primary read for next session

1. **`plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md`** — ADR file moved from `plugins/a4/a4/`. Next Steps list unchanged: only **Compass redesign** is open. Item 12 done note received a one-line rename trailer recording `iu-implementer → task-implementer`. Two factual-consistency edits inside the ADR body: Success Criteria #1 now says `UC, task, review finding` (was `UC, IU, review finding`); relationships table now says `implements | task → UC | Task delivers these UC(s)` (was `IU → UC | IU delivers …`).
2. **`plugins/a4/agents/task-implementer.md`** — renamed from `iu-implementer.md`. `name:` frontmatter field updated. File content itself was already task-terminology — the frontmatter `name` was the only still-stale surface.
3. **`plugins/a4/skills/plan/SKILL.md` + `plan/README.md` + `plan/references/planning-guide.md`** — the plan skill was the main IU residue location. `SKILL.md` description, status vocabulary descriptions, Step 2.2 header, `subagent_type: "a4:iu-implementer"` invocations (×2), and Agent Usage section all switched to `task-implementer`. `README.md` PlantUML diagram had ~17 IU→task renames including swimlane alias `|iu| → |ti|`. `planning-guide.md` had 8 residual IU mentions in Foundation Unit Validation + Shared File Integration sections (example tables now use `task 1`/`task 2`/`task 7` instead of `IU-1`/`IU-2`/`IU-7`).
4. **`plugins/a4/references/obsidian-dataview.md` + `obsidian-conventions.md` + `frontmatter-schema.md`** — two changes each: (a) all `plugins/a4/a4/*.decide.md` path references swapped to `plugins/a4/spec/*.decide.md`, (b) the "Legacy files (…, `visual-claude/a4/`) are out of scope" callouts were **deleted entirely** from each Scope section. Scope sections now stand on their own without explicit legacy exclusions.
5. This handoff.

---

## What this session accomplished

One pre-handoff commit: **`9b3ff6894`**. Five logical changes bundled because they are all narrow cleanups following the same ADR; splitting would produce five trivial commits and the "why" is shared across them (terminology consistency post-plan→task rename).

### Change 1 — ADR terminology consistency fix

**`plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md`** (3 edits):

- Line 34 (Success Criteria #1): `each UC, IU, review finding, and decision` → `each UC, task, review finding, and decision`.
- Line 143 (Structural relationships table): `| \`implements\` | IU → UC | IU delivers these UC(s) |` → `| \`implements\` | task → UC | Task delivers these UC(s) |`.
- Line 317 (Item 12 done note trailer): appended `Agent renamed from \`iu-implementer\` → \`task-implementer\` in the 2026-04-24_1732-follow-up cleanup.` so the ADR's own log matches the filesystem.

These two prose inconsistencies survived the plan→task rename (covered in the third Discussion Log continuation of this ADR). Per-type schema section (Task) and directory layout section were already correct — only Success Criteria and the relationship table had missed the sweep.

### Change 2 — Agent rename `iu-implementer` → `task-implementer`

**File move.** `git mv plugins/a4/agents/iu-implementer.md plugins/a4/agents/task-implementer.md` (preserves git blame history — rename detected with 99% similarity).

**Frontmatter.** `name: iu-implementer` → `name: task-implementer` in the renamed file. Body of the agent file was already task-terminology (the frontmatter was the only stale surface).

**All references (6 files updated).**
- `plugins/a4/README.md` line 43 — Agents table row and purpose column.
- `plugins/a4/agents/test-runner.md` line 90 — Target Mapping bullet.
- `plugins/a4/skills/plan/SKILL.md` (7 spots) — frontmatter `description`, status-semantics list (`implementing` + `failing`), Step 2.2 header, `subagent_type: "a4:iu-implementer"` (×2), Commit Points, Agent Usage.
- `plugins/a4/skills/plan/README.md` line 8 — Current behavior sentence.

Verified via `grep -rn "iu-implementer"` → only remaining live mention is the ADR Item 12 done-note rename trailer (see Change 1), which is intentional history.

### Change 3 — IU concept residue in the plan skill

**`plugins/a4/skills/plan/references/planning-guide.md`** (8 spots).
- Line 136 (Foundation Unit Validation): `create a dedicated IU for it` → `create a dedicated task for it`.
- Lines 178, 182, 183 (Shared File Integration narrative): all `IUs` → `tasks`.
- Line 188 (Contributing IUs column header) → `Contributing tasks`.
- Lines 190–192 (example rows): `IU-1 / IU-2 / IU-6 / IU-7` → `task 1 / task 2 / task 6 / task 7`. The `task N` form is plain prose, not wikilink — these are illustrative shared-integration examples, not cross-references to real task files in any specific workspace.

**`plugins/a4/skills/plan/README.md`** (~17 spots in the PlantUML workflow diagram).
- Line 3 (Current Notes paragraph): `Delegates IU implementation to per-IU subagents` → `Delegates task implementation to per-task subagents`.
- Line 18 (swimlane declaration): `|#AliceBlue|iu| IU subagent (sonnet)` → `|#AliceBlue|ti| task-implementer subagent (sonnet)`. Two-letter swimlane alias `|iu|` changed to `|ti|` (task-implementer) for consistency with agent name.
- Line 117 (swimlane switch) — `|iu|` → `|ti|` (the only other use of the alias in the diagram).
- All other IU-as-concept mentions inside the diagram (`IUs with file mappings + unit test paths`, `Step 5: IU Implementation`, `Identify ready IUs`, `per IU file mappings`, `Independent IUs run in parallel`, `Track IU results`, `Every 3 IUs?`, `More ready IUs?`, `IU failure summaries`, `All IUs done`, `Identify affected IUs`, `Reset affected IUs to "pending"`, `IU statuses`) → all `task/tasks`.

The rest of `planning-guide.md` continues to use "unit" as a generic concept word (Unit Derivation Strategy, Unit Sizing Guidelines, Foundation Unit Validation, etc.). This is a deliberate scope limit — see design decision 1.

### Change 4 — Folder rename `plugins/a4/a4/` → `plugins/a4/spec/`

**File move.** `git mv plugins/a4/a4 plugins/a4/spec`. Three ADR files moved with history intact:
- `2026-04-12-think-pipeline-restructuring.decide.md` (100% similarity)
- `2026-04-23-spec-as-wiki-and-issues.decide.md` (98% — also received the Change 1 edits)
- `2026-04-24-skill-naming-convention.decide.md` (100%)

**Rationale.** The folder was named `a4/` to echo the workspace convention, which made `plugins/a4/a4/` read as "the a4 plugin's own a4 workspace". Two problems: (a) the path is literally self-referential (`a4/a4/`), which is noise when navigating; (b) the files in it are ADR authoring docs, not output of an a4 skill — they don't follow the new schema (they're the *authority* for the new schema). Naming the folder `spec/` makes the content type explicit — it's the plugin's spec/decision-record directory, not a live a4 workspace. All the "Legacy files are out of scope" language throughout references/ was signaling exactly this distinction; after the rename, that language becomes redundant (see Change 5).

**Path references updated (8 spots in 4 files).**
- `plugins/a4/README.md` line 54 — Document Layout intro sentence.
- `plugins/a4/references/obsidian-dataview.md` lines 16, 192 — Scope line (later deleted in Change 5) and Cross-references entry.
- `plugins/a4/references/obsidian-conventions.md` lines 15, 127 — Scope line (later deleted) and Cross-references entry.
- `plugins/a4/references/frontmatter-schema.md` lines 3, 17, 249 — intro sentence, Scope legacy-files line (later deleted), and Sources section entry.

**Verified.** No remaining `plugins/a4/a4/` live references outside `.handoff/*.md` (which carry DO NOT UPDATE banners and intentionally retain the historical path). No scripts hardcode the path — validators (`validate_frontmatter.py`, `validate_body.py`), index refresh, drift detector all accept `<a4-dir>` as an argument.

### Change 5 — Remove "Legacy files" callouts from reference Scope sections

Three one-line deletions, one per reference doc:

- `plugins/a4/references/obsidian-dataview.md` — `Legacy directories (plugins/a4/spec/*.decide.md, visual-claude/a4/) are out of scope.` Removed. Preceding paragraph already establishes the vault target via `FROM "a4/..."`.
- `plugins/a4/references/obsidian-conventions.md` — `Legacy files under plugins/a4/spec/*.decide.md and visual-claude/a4/ are out of scope, consistent with frontmatter-schema.md.` Removed. The Scope bullet list already defines "files written into the a4/ workspace" as the applicable surface.
- `plugins/a4/references/frontmatter-schema.md` — `Legacy files (visual-claude/a4/, this plugin's own plugins/a4/spec/*.decide.md) are not covered by this schema — they predate the model and are intentionally left as-is.` Removed. Validator naturally skips files without a recognized `kind:` frontmatter; the exclusion is implicit.

**Why now.** Two reasons: (a) `visual-claude/a4/` is an external sibling repo at `/Users/myungo/GitHub/visual-claude` — it has no meaning to plugin users and was included only because the ADR's decision context referenced it as the legacy-content example; (b) after the folder rename, `plugins/a4/spec/` is semantically named — "this is the plugin's spec folder, not a live a4 workspace" is already self-evident, so repeating it as an explicit out-of-scope callout is noise.

**Preserved on purpose.** `visual-claude/A4/` references inside the ADR files themselves (`spec/2026-04-12-think-pipeline-restructuring.decide.md` — multiple; `spec/2026-04-23-spec-as-wiki-and-issues.decide.md` lines 298, 370, 381) stay untouched. Those are the historical decision context — the ADRs record *why* the pipeline restructuring happened (the visual-claude integration report findings were the trigger) and *why* no migration tooling was built (legacy content bounded and stable). Stripping those from ADRs would misstate the decision record.

### Change 6 — Plugin version bump

`.claude-plugin/marketplace.json` `a4` plugin: `1.0.0` → `1.0.1`. The `subagent_type: "a4:iu-implementer"` invocation path changed to `"a4:task-implementer"`, which is a skill-behavior change per ADR design decision 8 ("If the body validator later gets wired into a skill (changing skill behavior), that skill wiring is where a version bump would live"). Patch bump because the change is internal refactor — no new features.

### diff stat

```
 .claude-plugin/marketplace.json                    |  2 +-
 plugins/a4/README.md                               |  4 +--
 .../{iu-implementer.md => task-implementer.md}     |  2 +-
 plugins/a4/agents/test-runner.md                   |  2 +-
 plugins/a4/references/frontmatter-schema.md        |  6 ++--
 plugins/a4/references/obsidian-conventions.md      |  4 +--
 plugins/a4/references/obsidian-dataview.md         |  4 +--
 plugins/a4/skills/plan/README.md                   | 36 +++++++++---------
 plugins/a4/skills/plan/SKILL.md                    | 14 +++----
 .../a4/skills/plan/references/planning-guide.md    | 18 +++++-----
 ...26-04-12-think-pipeline-restructuring.decide.md |  0
 .../2026-04-23-spec-as-wiki-and-issues.decide.md   |  6 ++--
 .../2026-04-24-skill-naming-convention.decide.md   |  0
 13 files changed, 46 insertions(+), 52 deletions(-)
```

---

## Design decisions worth flagging

Record here so the next session doesn't relitigate.

1. **"IU" vs "unit" vs "task" — scoped cleanup.** The rename replaced `IU` (Implementation Unit) with `task` everywhere it was used as a reference to the per-file issue artifact or the subagent. The word `unit` (in `Unit Derivation Strategy`, `Unit Sizing Guidelines`, `Foundation Unit Validation`) was **left alone** because it refers to the general concept of "an implementation increment" — distinct from the specific artifact kind "task". Example: "a unit must be under ~500 lines" is a sizing heuristic for the conceptual implementation slice, not a schema rule for the file kind. Keeping "unit" preserves that conceptual register. If a future session decides the distinction is not worth maintaining, the sweep is purely mechanical across `planning-guide.md` and adjacent docs.
2. **Swimlane alias `|iu| → |ti|`.** The PlantUML workflow diagram in `plan/README.md` has two-letter swimlane aliases (`|tp|`, `|iu|`, `|ts|`, `|rv|`). The agent-rename change propagated naturally into `|ti|` (task-implementer). The alternative `|tk|` was considered and rejected — `|ti|` directly mirrors the agent name and the two other "matches-the-role" aliases (`|ts|` = test subagent, `|rv|` = reviewer). Only 2 occurrences of `|iu|` in the file, so the change was low-blast-radius.
3. **Folder rename `a4/ → spec/`, not `adr/` or `decisions/`.** Considered `decisions/` (explicit about content type) and `adr/` (matches industry convention). Chose `spec/` because the folder holds not just ADRs but also potential future spec-level authoring artifacts (the spec-as-wiki+issues ADR explicitly frames the folder as "the plugin's own spec"). `adr/` would pigeonhole. `decisions/` reads well but doesn't leave room for non-decision spec docs. Single-word `spec/` matches the "this is the specification for this plugin" framing that runs through the references/.
4. **Example IDs `task 1 / task 2 / task 7`, not wikilinks.** The `planning-guide.md` Shared Integration Points example table uses `task 1: initial setup + ready handler` rather than `[[task/1-initial-setup]]`. These are illustrative examples of multi-task file integration patterns, not cross-references to real files in any particular workspace. Using wikilinks would imply the reader could click through; plain prose is honest about the example being abstract.
5. **"Legacy files" callouts removed, not softened.** Considered rewording instead of deleting — e.g., "This document describes the new schema; the plugin's ADRs in `spec/` use an older frontmatter format and are not validator targets." Rejected because after the `spec/` rename, the scope of each reference doc is already self-evident from its Scope section. A rewording would still carry the same rhetorical weight as the deleted callout while being redundant. Delete and move on.
6. **ADR internal `visual-claude/A4/` references preserved.** The `spec/2026-04-12-think-pipeline-restructuring.decide.md` (5 mentions) and `spec/2026-04-23-spec-as-wiki-and-issues.decide.md` (lines 298, 370, 381) reference `visual-claude/A4/` to record the factual context of the decision (the legacy content that motivated the restructuring; the decision *not* to build migration tooling). Stripping those would misstate the decision record. Scope of Change 5 is explicitly the reference/ docs, which are forward-looking authoring guides — the ADRs are backward-looking decision records with different faithfulness constraints.
7. **Version bump to 1.0.1, not 1.0.2 despite two separate "breaking"-feeling changes.** The agent rename (subagent_type change) and the folder rename both ship in the same commit. From a SemVer perspective: the agent rename is a behavioral breaking change for anyone invoking `a4:iu-implementer` directly (only the plan skill itself does, and it was updated in-session); the folder rename is a documentation-path change that breaks any external wikilink pointing into `plugins/a4/a4/*`. Both bundled into 1.0.1 because neither has a user-facing surface that's been released yet — all of this is local development state before the 1.0.x line has been published anywhere. One bump suffices.
8. **No new ADR for the folder rename.** The rename is a cleanup decision, not a new design decision. The `spec/` naming itself doesn't introduce any convention that future plugins should follow — it's idiomatic. Creating a separate ADR would be ceremony.
9. **Single bundled commit, not five.** Considered splitting into commits per logical change (terminology / agent rename / plan-skill cleanup / folder rename / legacy-line removal / version bump). Rejected because each is a small, closely-related consistency fix, and splitting would produce five commits with substantially overlapping rationales. The commit message body lists the five logical units; the tree state is cleaner than five separately-reviewable-but-related commits.
10. **`spec/` folder is git-tracked as just files — no INDEX.md, no workspace affordances.** The plugin's `spec/` directory holds three `.decide.md` files at root with no subfolders, no INDEX.md, no per-item issue files. That matches the pre-rename state (ADRs at `a4/a4/` root) and is correct for a small folder of authoring docs. If the plugin ever grows more spec-level content (design docs, RFCs, migration notes), a richer structure can be added without revisiting this rename.

---

## Remaining ADR Next Steps (post-session state)

From `plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md` Next Steps:

1. ~~Schema finalization~~ (done 2026-04-24_1700)
2. ~~Id allocator~~ (done)
3. ~~Drift detector~~ (done)
4. ~~In-situ nudge integration~~ (done — spark-decide carve-out closed 2026-04-24_1638)
5. ~~Wiki update close guard~~ (done)
6. ~~Obsidian markdown conventions doc~~ (done 2026-04-24_1710)
7. ~~INDEX.md redesign~~ (done)
8. **Compass redesign** — Step 1.2 (artifact scan), Step 3 (gap diagnosis with drift detection) rewritten for the new layout. Step 0 (INDEX refresh) was already updated in a prior session.
9. ~~Skill rewrites~~ (done; agent renamed this session as a trailer)
10. ~~Spark skill alignment~~ (done)
11. ~~README rewrite~~ (done)
12. ~~Obsidian dataview examples~~ (done 2026-04-24_1732)
13. ~~Body-level convention validator~~ (done 2026-04-24_1732)

**Compass redesign** is the only open item. No new items opened or closed this session.

Also still open (tracked in prior handoffs, not an ADR Next Step):

- **`.handoff/INDEX.md`** — topic-grouped dashboard driven by `scripts/topic_references.py`. Now 14 handoffs under `plugins/a4/.handoff/` for the `a4-redesign` thread (this session being the 14th). Deferred 11 sessions running. Thread has a single remaining ADR item (Compass redesign); revisiting the dashboard question at thread close is increasingly worth it.

### Recommended next session

**Compass redesign** — the only ADR item left.

- `plugins/a4/skills/compass/SKILL.md` — Step 1.2 (artifact scan) and Step 3 (gap diagnosis) still use the pre-ADR layout (topic × stage grid). Rewrite for the per-item wiki+issue layout.
- Layer-2 integration: Step 3 should invoke `plugins/a4/scripts/drift_detector.py` rather than the pre-ADR gap heuristics. The drift detector already exists and handles close-guard / stale-footnote / orphan-marker / orphan-definition / missing-wiki-page.
- Consider wiring `validate_frontmatter.py` and `validate_body.py` into Step 3 as well — they're the other two "inconsistencies to surface" surfaces. Or leave them to a future `/a4:validate` (which doesn't exist yet; also a possible follow-up).

Higher blast radius than this session's cleanup pass — compass is an active skill with callers. The handoff chain has noted this as "save for when there's appetite for it" across multiple sessions. After compass lands, the `a4-redesign` thread can wrap with a thread-closure handoff.

---

## Files intentionally NOT modified

- **`plugins/a4/spec/2026-04-12-think-pipeline-restructuring.decide.md`** — contains `IU-1 / IU-14 / IU-15 / IU-16` references (lines 20, 56, 60, 151, 166, 207) describing specific implementation units from the historical visual-claude project. These are factual references to pre-rename artifact names in an external project — not renameable. The ADR is a historical decision record; retrofitting terminology would misstate history.
- **`plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md` line 381 (Discussion Log)** — `a 1214-line aggregated plan file with 16 IUs. After extracting IUs to per-file tasks, …`. This sentence *describes the rename itself* using the pre-rename terminology — changing "IUs" to "tasks" here would destroy the sentence's meaning ("After extracting tasks to per-file tasks"). The Discussion Log is a historical record of what was said at decision time; preserved verbatim.
- **`plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md` lines 298, 370** — Rejected Alternatives and Continuation log entries mentioning `visual-claude/A4/` as legacy content. Part of the decision record for why no migration tooling was built. Preserved.
- **`.handoff/*.md` files** — all carry DO NOT UPDATE banners. All 13 prior handoffs on this thread mention `plugins/a4/a4/*.decide.md` by path; those paths are no longer valid post-rename, but the handoffs are point-in-time snapshots. Do not retrofit.
- **`plugins/a4/README.md` Agents table other rows** — only the `iu-implementer` row changed. `api-researcher`, `arch-reviewer`, `decision-reviewer`, `domain-updater`, `mock-html-generator`, `plan-reviewer`, `test-runner`, `usecase-composer`, `usecase-explorer`, `usecase-reviewer`, `usecase-reviser` left as-is.
- **`plugins/a4/scripts/*`** — no script changes. Validators and detectors take paths as arguments; the folder rename and agent rename are transparent to them.
- **`plugins/a4/skills/*/SKILL.md` other than `plan/SKILL.md`** — only `plan` invokes `task-implementer`; other skills don't reference it. No skill namespace changes, no allowed-tools changes.
- **`plugins/a4/.claude-plugin/plugin.json`** — per repo-level CLAUDE.md, plugin.json must NOT carry a version field. Version lives in `marketplace.json`. No change here.
- **`global/` directory** — repo-level shared components, orthogonal to this plugin.

---

## Working-tree state at handoff time

Pre-handoff commit: **`9b3ff6894`** — `refactor(a4): rename iu-implementer→task-implementer and a4/→spec/` (13 files, +46 / −52).

Branch state before this handoff's commit: `main` is 14 commits ahead of `origin/main` (12 before this session + 1 pre-session handoff from the previous session + 1 pre-handoff commit this session). Will be 15 after this handoff-file commit.

Changes bundled into this handoff's own commit:

```
new file:   plugins/a4/.handoff/2026-04-24_1751_task-rename-and-spec-folder.md   # this file
```

---

## Files to read first next session

1. **`plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md`** — ADR in its new location. Next Steps list; confirm only Compass redesign remains open.
2. **`plugins/a4/agents/task-implementer.md`** — renamed agent, same body content.
3. **`plugins/a4/skills/plan/SKILL.md`** — the only skill that spawns `task-implementer`. Check Step 2.2 and Agent Usage section to confirm invocation paths.
4. This handoff.
5. **Prior handoff `2026-04-24_1732_dataview-reference-and-body-validator.md`** — immediate predecessor; sets context for what was "done" going into this session.
6. **If tackling Compass redesign:** `plugins/a4/skills/compass/SKILL.md` Step 1.2 + Step 3 (pre-ADR gap heuristics), `plugins/a4/scripts/drift_detector.py` (Layer-2 integration point), and both validators (`validate_frontmatter.py`, `validate_body.py`) as additional inconsistency surfaces that Step 3 could consume.

---

## Explicitly rejected / not done this session

- **Rename `task-implementer` to something more expressive** (e.g., `task-executor`, `implementer`). The existing name cleanly pairs with the `task/*.md` file kind it consumes; the `-implementer` suffix already signals its role. No churn reason.
- **Retrofit `IU` references in `spec/2026-04-12-think-pipeline-restructuring.decide.md`.** Historical ADR about the visual-claude project; `IU-1 / IU-14 / …` are factual references to artifact names that existed at that time. See Files NOT modified #1.
- **Rewrite the swimlane `|tp|` (plan orchestrator) in `plan/README.md` PlantUML to `|po|` or similar.** Only `|iu|` needed renaming because the agent name changed; `|tp|` still matches "plan (orchestrator)" fine. No shaving.
- **Split the commit into five per-change commits.** See design decision 9.
- **Create a separate ADR for the `a4/` → `spec/` folder rename.** See design decision 8.
- **Update `.handoff/*.md` historical paths to `plugins/a4/spec/`.** Snapshots carry DO NOT UPDATE banners by design.

---

## Non-goals for next session

- Do not rename the agent again. The `task-implementer` name is settled.
- Do not re-introduce "Legacy files (…) are out of scope" callouts into the reference docs. The `spec/` folder name makes the scope self-evident.
- Do not retrofit historical `IU` references in handoffs or older ADRs. Those are point-in-time records; rewriting them is revisionism.
- Do not bump `marketplace.json` again for a compass-redesign doc change alone. Pattern held: ADR edits and reference doc edits do not bump; skill-behavior or agent-interface changes do. Compass redesign that ships a new `/a4:validate` or substantially changes Compass Step 3 behavior would qualify; internal Compass doc revisions alone would not.
- Do not revisit the `unit` vs `task` distinction in `planning-guide.md`. "Unit" is deliberately kept for the general sizing-heuristic concept; "task" is the file-kind artifact. See design decision 1. Revisit only if a new use surfaces where the two conflict.
- Do not treat the remaining `.handoff/` handoff-INDEX question as blocking. It's been deferred 11 sessions and can wait until thread closure after compass lands.
