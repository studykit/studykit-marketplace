---
timestamp: 2026-04-24_1813
topic: a4-redesign
previous: 2026-04-24_1751_task-rename-and-spec-folder.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_1813. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: `.handoff/<topic>/` subfolder layout + `topic_references.py` retirement

Topic thread: `a4-redesign` — continues from `plugins/a4/.handoff/a4-redesign/2026-04-24_1751_task-rename-and-spec-folder.md`. Note that this is the first handoff on the thread that actually *lives* inside a topic subfolder — the prior 14 were moved as part of this session.

The session opened with a discussion of whether `.handoff/INDEX.md` (deferred 11 sessions running) should finally be built. The conclusion was that the problem an INDEX would solve — topic grouping and thread navigation — is better solved by filesystem-level nesting. `topic_references.py` (the would-be INDEX driver) was also retired in the same pass.

Pre-handoff commits:

- **`ea5e7387e`** — `refactor(handoff): topic-folder layout, drop topic_references.py`. 15 files; the 14 handoff renames into `a4-redesign/` + deletion of `plugins/a4/scripts/topic_references.py` (−138 lines). The accompanying skill-doc edits and version bump were **not** included in this commit because the `Edit`-based changes were in the working tree but never staged. Caveat below.
- **`57673bf6e`** — `refactor(handoff): apply topic-folder path in skill docs, bump a4 to 1.0.2`. Companion commit that lands the three missed edits: both skill SKILL.md files and the marketplace.json version bump. 3 files, +10 / −14.

## Primary read for next session

1. **`plugins/a4/skills/handoff/SKILL.md`** — plugin-scoped `/a4:handoff` skill. Write path is now `<project-root>/.handoff/<topic-slug>/<TIMESTAMP>_<filename-slug>.md`. Previous-handoff lookup is a simple directory listing of the topic subfolder, no frontmatter scan. The `topic_references.py --list-topics` invocation block is gone; `ls <project-root>/.handoff/` is the listed equivalent.
2. **`global/skills/handoff/SKILL.md`** — global `/handoff` skill. Step 3 Directory rule now ends with a "nest by topic" sentence; File Format section describes `topic` as both a frontmatter field *and* a folder name (same value, same source of truth; frontmatter kept as in-file context so single files remain identifiable).
3. **`plugins/a4/.handoff/a4-redesign/`** — 15 files now (14 prior + this handoff). The parent `.handoff/` contains only this one subdirectory.
4. **`.claude-plugin/marketplace.json`** — a4 at 1.0.2. Skill-behavior change: the `/a4:handoff` write path structure changed.
5. This handoff.

## Scope of the intent-before-action discussion

Two questions were debated before executing:

1. **Is an INDEX.md needed at all?** Prior handoffs had written it in as a Still-Open item and deferred it 11 sessions running. The discussion concluded: no, and probably not ever on this thread. Single-topic corpus gave the dashboard no variance; `ls` + sortable filenames + `previous:` chain already covered navigation; and the 11-session deferral was itself evidence that the felt pain never materialized.
2. **Folder-per-topic as the alternative.** The user proposed moving handoffs into topic-named subfolders instead of building INDEX. The advantages (filesystem-encoded grouping, no script maintenance, no new doc-drift surface) outweighed the migration cost (one `git mv` pass + two skill-doc edits).

After the direction was set, one mis-framing got corrected mid-design: my initial plan labeled the a4 skill's `<project-root>/.handoff/` reference as "drift" against the reality of files sitting at `plugins/a4/.handoff/`. The user clarified that the a4 skill's target is the **end-user's project** when the plugin is installed, not the plugin repo itself; the actual `plugins/a4/.handoff/` usage during plugin development comes from the global `/handoff` skill in subtree-scoped mode, not from `/a4:handoff`. No drift. The revised plan kept `<project-root>/.handoff/` in the a4 skill intact and only added the `<topic-slug>/` layer.

## What this session accomplished

### Change 1 — Move 14 handoffs into `a4-redesign/` subfolder

`git mv plugins/a4/.handoff/*.md plugins/a4/.handoff/a4-redesign/` for all 14 files, done one-by-one so every move is reported as a rename (100% similarity) in git log, preserving history.

Files moved:

```
2026-04-23_2119_a4-rename-and-compass-index-dashboard.md
2026-04-24_0143_a4-wiki-issue-model-locked.md
2026-04-24_0233_handoff-scripts-and-task-rename.md
2026-04-24_1433.md
2026-04-24_1451.md
2026-04-24_1524.md
2026-04-24_1602_plugin-rename-and-naming-adr.md
2026-04-24_1615_readme-and-compass-redesign.md
2026-04-24_1628_spark-skill-alignment.md
2026-04-24_1638_spark-decide-nudge-carveout.md
2026-04-24_1700_frontmatter-schema-and-validator.md
2026-04-24_1710_obsidian-conventions-factor.md
2026-04-24_1732_dataview-reference-and-body-validator.md
2026-04-24_1751_task-rename-and-spec-folder.md
```

Legacy-5 note. The five oldest handoffs (`2026-04-23_2119`, `2026-04-24_0143`, `2026-04-24_1433`, `2026-04-24_1451`, `2026-04-24_1524`) have no `topic:` frontmatter — they predate the topic-threading convention. Under the DO NOT UPDATE policy their frontmatter cannot be retrofitted, but **content** unambiguously places them on the `a4-redesign` thread (they discuss the same rename/pipeline work the rest of the thread continues). Moved into `a4-redesign/` on content grounds; the missing frontmatter is accepted as a historical irregularity. The `previous:` chain is unaffected because `previous:` values are bare filenames, not paths.

### Change 2 — Retire `plugins/a4/scripts/topic_references.py`

`git rm plugins/a4/scripts/topic_references.py` (−138 lines). The script's responsibilities collapse to shell primitives once the folder encodes the topic:

| Former mode | Replacement |
|---|---|
| `--list-topics` | `ls <handoff-dir>/` |
| `<dir> <topic>` (topic filter) | scope is one folder; no filter needed |
| `--with-handoffs` (inverse by path) | no equivalent — was low-signal on this corpus |
| `--filter <prefix>` | filesystem filter |

On this corpus the extractor was already producing mostly false positives — the 9-handoff topic filter returned 7 paths, and most of them were wikilink examples (`[[path]]`, `[[target]]`, `architecture`) rather than genuine cross-references. Handoffs reference real files with **plain absolute paths**, which the wikilink/injection-marker regex never matched. Retiring is strictly loss-free.

### Change 3 — `global/skills/handoff/SKILL.md` — topic-folder rule

Two edits:

- **Step 3 Directory** — existing rule about subtree vs repo-root `.handoff/` preserved verbatim. Appended a "nest by topic" sentence: final path is `<handoff-dir>/<topic>/<TIMESTAMP>_<slug>.md`, create the `<topic>/` subdir if it doesn't exist.
- **File Format / `topic` and `previous` bullets** — replaced the "list the target `.handoff/` directory and read each file's frontmatter" lookup with "list the `<handoff-dir>/<topic>/` subdirectory (the topic name is the folder name, so no frontmatter scan is needed)." The `previous:` bullet likewise shifted to "most recent file in the `<topic>/` subdirectory by timestamp prefix."

No changes to the Banner, Output, or the "scope to area of work" logic itself.

### Change 4 — `plugins/a4/skills/handoff/SKILL.md` — topic-folder rule

Five edits:

- Frontmatter `description` — `<project-root>/.handoff/` → `<project-root>/.handoff/<topic>/`.
- Step 1 "Final file path" line — `<project-root>/.handoff/<TIMESTAMP>_<filename-slug>.md` → `<project-root>/.handoff/<topic-slug>/<TIMESTAMP>_<filename-slug>.md`.
- Step 1 "Ensure ... exists" line — same `<topic-slug>/` insertion.
- Step 2 entirely reshaped. Was: scan `<project-root>/.handoff/*.md`, parse each file's frontmatter, match on `topic:`, pick max timestamp. Now: list `<project-root>/.handoff/<topic-slug>/`, pick max timestamp (no frontmatter parse). The `topic_references.py --list-topics` command block was replaced by a single sentence pointing at `ls <project-root>/.handoff/`.
- Step 6 "Write to ..." line — same `<topic-slug>/` insertion.

Nothing touched outside those five hotspots. Step 3 (project doc updates), Step 4 (embed directives), Step 5 (inject_includes), Step 7 (commit) left as-is.

### Change 5 — `.claude-plugin/marketplace.json` — a4 1.0.1 → 1.0.2

The `/a4:handoff` skill's write-path structure changed, which per the ADR's versioning heuristic ("skill wiring is where a version bump would live") qualifies as a skill-behavior bump. Patch version because the change is internal refactor — no new user-facing features.

### diff stat (aggregate across both commits)

```
 .claude-plugin/marketplace.json                                           |   2 +-
 global/skills/handoff/SKILL.md                                            |   6 +-
 plugins/a4/scripts/topic_references.py                                    | 138 --------------------
 plugins/a4/skills/handoff/SKILL.md                                        |  16 ++-
 plugins/a4/.handoff/{ => a4-redesign}/2026-04-23_2119_...md               |   0 (14 renames total, 100% similarity)
 plugins/a4/.handoff/{ => a4-redesign}/2026-04-24_0143_...md               |   0
 ... (12 more rename lines omitted) ...
 18 files changed, 16 insertions(+), 152 deletions(-)
```

## Caveat — commit `ea5e7387e` message overstates its contents

The earlier commit's message describes "updated both skill variants ... bumps the a4 plugin to 1.0.2." Those edits were in the working tree (from `Edit` tool calls) but never `git add`-ed, so only the `git mv` / `git rm` operations (auto-staged) landed in `ea5e7387e`. The companion commit `57673bf6e` lands the three missed files.

Not amended per "do not amend prior commits" policy; the inconsistency is documented here instead. Any future code-archaeologist reading just `git log --oneline` should treat `ea5e7387e` + `57673bf6e` as a two-part unit describing one refactor.

## Design decisions worth flagging

Record here so the next session doesn't relitigate.

1. **Folder-per-topic over INDEX.md.** INDEX.md was deferred 11 sessions running — the deferral itself was the signal that the felt problem doesn't exist on this corpus. Single-topic corpus gives any dashboard zero variance, and per-topic subfolders + `ls` already deliver the grouping the dashboard would have shown. INDEX was considered and rejected, not postponed.
2. **Keep `topic:` frontmatter despite folder-encoded topic.** The frontmatter `topic:` is now redundant with the containing folder name. Retained anyway because (a) a handoff file opened in isolation (out of its folder) stays identifiable, (b) drift detection between folder name and frontmatter value is cheap future work, (c) removing it would be a lossy change for trivial savings. Next session should *not* revisit — the decision to keep is settled.
3. **Legacy-5 moved into `a4-redesign/` on content grounds.** The five pre-frontmatter handoffs are unambiguously `a4-redesign` thread content but cannot have their frontmatter retrofitted. Moving based on content interpretation was chosen over (a) an `_untagged/` bucket (pointless purity), (b) leaving them in root (consistency break). They're now indistinguishable from frontmatter-annotated siblings in the same folder, and navigation through `previous:` works.
4. **`topic_references.py` retired, not "updated for folder awareness."** The script's core value was frontmatter-based grouping, which is now filesystem-level. Retaining a folder-aware variant would be a thin shell over `ls` — not worth the surface area. Future work that actually needs machine-readable handoff indexing (e.g., a dashboard page) can re-introduce something, but it should be designed for that use case, not be a zombie version of this script.
5. **Did not rename `.handoff/` itself.** The `.handoff/` parent name stays. Considered whether the dot-prefix (hidden by default in many tools) was still the right call; concluded yes — handoffs are an artifact of the work process, not primary documentation, and the hidden convention matches the style of `.github/`, `.vscode/`, etc. No churn reason.
6. **Skill doc contains `<topic-slug>/` literally, not a placeholder that would be substituted at runtime.** A future reader might expect the skill to show example instantiated paths. But `<topic-slug>` is the same placeholder grammar already used for `<TIMESTAMP>` and `<filename-slug>` elsewhere in the doc — consistent placeholder-brackets convention.
7. **Plugin a4 skill target audience remains the plugin's end user.** The `<project-root>/.handoff/` path in the a4 skill refers to the user's project that installs the plugin, not to `plugins/a4/.handoff/` within this repo. The current repo's `plugins/a4/.handoff/` entries are plugin-developer-authored and come from the global `/handoff` skill's subtree rule, not from `/a4:handoff`. Two different paths serving two different audiences — no conflict.
8. **Historical references to `topic_references.py` inside prior handoffs left untouched.** 15+ mentions across 11 prior handoffs. DO NOT UPDATE policy applies; those are point-in-time records of sessions where the script still existed. Same principle as the previous session's preservation of `plugins/a4/a4/` references in prior handoffs post-folder-rename.

## Remaining ADR Next Steps

From `plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md` Next Steps:

1. ~~Schema finalization~~ (done 2026-04-24_1700)
2. ~~Id allocator~~ (done)
3. ~~Drift detector~~ (done)
4. ~~In-situ nudge integration~~ (done 2026-04-24_1638)
5. ~~Wiki update close guard~~ (done)
6. ~~Obsidian markdown conventions doc~~ (done 2026-04-24_1710)
7. ~~INDEX.md redesign~~ (done)
8. **Compass redesign** — still the only open item.
9. ~~Skill rewrites~~ (done)
10. ~~Spark skill alignment~~ (done)
11. ~~README rewrite~~ (done)
12. ~~Obsidian dataview examples~~ (done 2026-04-24_1732)
13. ~~Body-level convention validator~~ (done 2026-04-24_1732)

**Also closed this session (not an ADR item but a long-running "Still open" in prior handoffs):**

- **`.handoff/INDEX.md`** — was listed under "Also still open" across 12 prior handoffs. Concluded this session that it is not needed; folder-per-topic replaces the navigation value an INDEX would have provided. This item should **not** reappear in future handoffs' Still-Open lists.

### Recommended next session

**Compass redesign** — the last ADR Next Step.

- `plugins/a4/skills/compass/SKILL.md` Step 1.2 (artifact scan) and Step 3 (gap diagnosis) still use the pre-ADR topic × stage grid. Rewrite for the per-item wiki+issue layout (see `plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md`).
- Step 3 should invoke `plugins/a4/scripts/drift_detector.py` (which already covers close-guard / stale-footnote / orphan-marker / orphan-definition / missing-wiki-page) rather than reimplementing gap heuristics.
- Consider wiring `validate_frontmatter.py` and `validate_body.py` into Step 3 — they surface a different class of inconsistency (schema / body-convention) that a compass pass could reasonably report. Alternatively, leave them for a potential future `/a4:validate` skill (does not exist yet).

After Compass lands, a thread-closure handoff on `a4-redesign` becomes appropriate. No new thread is queued.

## Files intentionally NOT modified

- **`plugins/a4/.handoff/a4-redesign/*.md`** — all 14 prior handoffs moved unchanged (100% similarity renames). DO NOT UPDATE policy: historical `topic_references.py` references and pre-topic-folder path descriptions remain as point-in-time snapshots.
- **`plugins/a4/scripts/inject_includes.py`, `extract_section.py`, `allocate_id.py`, `drift_detector.py`, `validate_frontmatter.py`, `validate_body.py`, `index_refresh.py`** — none referenced `topic_references.py`. No import edges to repair. All remaining handoff-adjacent scripts untouched.
- **`plugins/a4/spec/*.decide.md`** — the ADRs. No decision-record changes in this session (the folder-layout choice is plumbing, not a spec decision).
- **`plugins/a4/references/*`** — reference docs unaffected. Their scope is `a4/` workspace convention, not handoff infrastructure.
- **`plugins/a4/skills/plan/`, `compass/`, `spark/`, `think/`, `review/`, etc.** — none interact with the handoff directory layout.
- **`.claude-plugin/plugin.json`** — per repo CLAUDE.md, plugin.json must NOT carry a version field. Version lives in `marketplace.json`. Correct as-is.
- **`plugins/a4/README.md`** — does not describe handoff-directory layout, so no edit needed.
- **`/Users/myungo/.claude/skills/handoff/` (the install target)** — the global `/handoff` skill content updates are in `global/skills/handoff/SKILL.md` in this repo. Installation to `~/.claude/skills/handoff/` happens outside this refactor's scope.

## Working-tree state at handoff time

Two pre-handoff commits landed this session:

```
57673bf6e refactor(handoff): apply topic-folder path in skill docs, bump a4 to 1.0.2
ea5e7387e refactor(handoff): topic-folder layout, drop topic_references.py
```

Branch state: `main`. With this handoff's own commit, main will be 17 commits ahead of `origin/main` (14 before this session + 2 pre-handoff commits this session + 1 handoff-file commit).

Changes bundled into this handoff's own commit:

```
new file:   plugins/a4/.handoff/a4-redesign/2026-04-24_1813_topic-folder-layout.md   # this file
```

## Files to read first next session

1. **`plugins/a4/skills/handoff/SKILL.md`** — to confirm the `/a4:handoff` layout is what you expect before invoking it.
2. **`global/skills/handoff/SKILL.md`** — same, for the global `/handoff` skill.
3. **`plugins/a4/.handoff/a4-redesign/`** — 15 files, chronological by filename prefix.
4. This handoff.
5. **If tackling Compass redesign**: `plugins/a4/skills/compass/SKILL.md` Step 1.2 + Step 3, `plugins/a4/scripts/drift_detector.py`, and both validators (`validate_frontmatter.py`, `validate_body.py`) as additional inconsistency surfaces that Step 3 could consume.

## Explicitly rejected / not done this session

- **Build `.handoff/INDEX.md`.** See design decision 1.
- **Update `topic_references.py` to scan topic subfolders instead of retiring it.** Retired outright; a future dashboard should be designed fresh, not a zombie.
- **Amend `ea5e7387e` to include the missed skill-doc edits.** Amending is disallowed; the companion commit `57673bf6e` + this handoff's caveat serve as the record.
- **Drop the `topic:` frontmatter field now that the folder name carries the topic.** Kept as redundant cross-check. Design decision 2.
- **Retrofit `topic:` frontmatter into the 5 legacy handoffs.** DO NOT UPDATE policy applies.
- **Rename `.handoff/` to something without the leading dot.** See design decision 5.
- **Edit historical `topic_references.py` mentions inside prior handoffs.** DO NOT UPDATE.
- **Separate-commit each of the 5 changes.** Two commits instead of one was a staging-ordering accident, not a decomposition choice. If the `git add` had caught everything, one commit would have been the plan — all five sub-changes share a single "move to folder-per-topic layout" rationale.

## Non-goals for next session

- Do not re-introduce INDEX.md. The decision was to replace the INDEX need with folder layout, not to defer INDEX again.
- Do not re-introduce `topic_references.py` or a near-variant. If handoff indexing becomes necessary later, design for the specific downstream consumer, don't revive.
- Do not revisit the `topic:` frontmatter keep-vs-drop question. Kept; future session should not re-open.
- Do not rebase or squash `ea5e7387e` and `57673bf6e` together. The split is now part of the repo's git history; the caveat in this handoff documents it.
- Do not bump `marketplace.json` again for this handoff-file commit. Docs-only commits (adding a handoff snapshot) do not bump. The bump for the skill-behavior change already happened in `57673bf6e`.
- Do not treat the `.handoff/INDEX.md` item as re-open if it somehow resurfaces in future handoffs. It's closed as "not needed."
