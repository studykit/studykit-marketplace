---
timestamp: 2026-04-24_1602
topic: a4-redesign
previous: 2026-04-24_1524.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_1602. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: plugin rename (think→a4) + skill-naming convention ADR

Topic thread: `a4-redesign` — continues from `.handoff/2026-04-24_1524.md` (a4/INDEX.md redesign). This session was a meta round triggered by reading all six prior handoffs on the thread: the accumulated skill-naming inconsistency (`think-`, `auto-`, `spark-`, `a4-`, bare) was surfaced, a 3-axis mental model was agreed, and the full rename landed as the **1.0.0 migration milestone**.

## Primary read for next session

1. **`plugins/a4/a4/2026-04-24-skill-naming-convention.decide.md`** — the new authoritative ADR for skill naming. Read this before adding any future skill.
2. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — the spec-as-wiki+issues ADR (rejected-alternatives entry at line ~303 updated to reflect the `a4-handoff` anti-pattern under the new plugin name and to cross-reference the new ADR).

This handoff is the narrative wrapper around the rename.

---

## What this session accomplished

One commit: `d50d2dea8` — `feat(a4)!: rename plugin think→a4 and restructure skill naming (a4 1.0.0)` (76 files, +349 / −208). Breaking change marker (`!`) because all invocation paths change.

### Plugin rename

- Directory: `plugins/think/` → `plugins/a4/` (git rename, 100% similarity on most files)
- `.claude-plugin/marketplace.json` entry: `name: "think"` → `"a4"`, `source: "./plugins/think"` → `"./plugins/a4"`, version `0.20.0` → `1.0.0`, keywords rewritten
- `plugins/a4/.claude-plugin/plugin.json` — `name: "a4"`, description rewritten
- `plugins/a4/.codex-plugin/plugin.json` — `name: "a4"`, `displayName: "a4"`, description + keywords rewritten (version `0.9.1` retained — codex has its own scheme)
- `.agents/plugins/marketplace.json` — entry updated

### Skill renames (5)

Directories moved via `git mv plugins/a4/skills/<old> plugins/a4/skills/<new>`:

| Old | New | Reason |
|-----|-----|--------|
| `think-usecase` | `usecase` | Interactive default; drop mode prefix (was stutter `/think:think-*`) |
| `think-arch` | `arch` | " |
| `think-plan` | `plan` | " |
| `a4-drift` | `drift` | Scope redundant — plugin is now `a4`; drop scope prefix |
| `a4-index` | `index` | " |

Unchanged (already compliant with the 3-axis convention):

- `auto-usecase`, `auto-bootstrap` — mode prefix, no stutter
- `spark-brainstorm`, `spark-decide` — pipeline prefix (2-stage pipeline)
- `handoff`, `compass` — bare orchestration skills
- `web-design-mock` — grandfathered (not discussed this session; appears to be a cross-cutting mock generator, bare prefix is fine)

### Invocation mapping

All skills now invoked as `/a4:<skill>`:

```
/a4:usecase          (was /think:think-usecase)
/a4:arch             (was /think:think-arch)
/a4:plan             (was /think:think-plan)
/a4:auto-usecase     (was /think:auto-usecase)
/a4:auto-bootstrap   (was /think:auto-bootstrap)
/a4:spark-brainstorm (was /think:spark-brainstorm)
/a4:spark-decide     (was /think:spark-decide)
/a4:drift            (was /think:a4-drift)
/a4:index            (was /think:a4-index)
/a4:handoff          (was /think:handoff)
/a4:compass          (was /think:compass)
/a4:web-design-mock  (was /think:web-design-mock)
```

### New ADR

**`plugins/a4/a4/2026-04-24-skill-naming-convention.decide.md`** — documents:

1. The 3-axis mental model: **mode** (interactive / autonomous) × **scope** (which internal pipeline) × **orchestration** (cross-cutting).
2. The `think` → `a4` rename rationale (plugin scope = workspace; aligning names cascades simplifications).
3. Prefix rules going forward:
   - No plugin-name prefix, ever.
   - Bare = interactive default; `auto-` = autonomous variant.
   - Pipeline prefix (`<pipeline>-`) only when the pipeline has ≥2 stages.
   - Orchestration = bare name.
4. Full old→new skill name mapping.
5. Rejected alternatives: keep `think` name, use `guided-` prefix, keep `a4-` on maintenance skills, verb-first naming, split version bump choices.

Filename follows the plugin's own `a4/` pre-ADR convention (`<date>-<slug>.decide.md`), matching `2026-04-12-think-pipeline-restructuring.decide.md` and `2026-04-23-spec-as-wiki-and-issues.decide.md`. The plugin's own `a4/` intentionally predates its own redesign and does not use the new per-item-file layout.

### Reference updates

Bulk `sed` replacements across active files (not handoffs, not historical ADRs):

- `/think:think-<X>` → `/a4:<X>` (stutter compound first)
- `/think:<X>` → `/a4:<X>` for all other invocations
- `skills/think-<X>` → `skills/<X>` (path references in prose)
- `skills/a4-<X>` → `skills/<X>` (path references in prose)
- `plugins/think/` → `plugins/a4/`
- Bare `think-usecase`, `think-arch`, `think-plan`, `a4-drift`, `a4-index` → stripped prefix
- `subagent_type: "think:<X>"` → `"a4:<X>"` (agent type namespace)
- `Skill({ skill: "think:<X>" })` → `"a4:<X>"` (compass.SKILL.md dynamic invocations)
- Prose: `think plugin` → `a4 plugin`, `the think pipeline` → `the a4 pipeline`, `think-pipeline` (tag) → `a4-pipeline`

### External references updated

- `global/skills/handoff/SKILL.md` — path hint `plugins/think/.handoff/` → `plugins/a4/.handoff/`

---

## Files intentionally NOT modified

### Point-in-time snapshots (immutable by contract)

- `plugins/a4/.handoff/*.md` — all six prior handoffs carry `DO NOT UPDATE THIS FILE` banners. Their contents reference the old `plugins/think/`, `/think:think-*`, etc. — these are accurate historical records and must not be rewritten. The new ADR makes the rename traceable.

### Historical ADR

- `plugins/a4/a4/2026-04-12-think-pipeline-restructuring.decide.md` — the original pipeline-structure ADR. Filename retains `think-pipeline-restructuring` because that is what the topic was literally called at the time. Rewriting the filename would be revisionist.

### Historical version references

- `plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md` — annotations like `*Done 2026-04-24 (think 0.18.0)*` retained verbatim. The plugin was literally called `think` at that version; rewriting to `a4 0.18.0` would misstate history. Future annotations (if any) should use `a4 <version>` post-1.0.0.

### Archive

- `a4/archive/co-think-code.impl-plan.md` (project-root `a4/archive/`) — archive material, not a plugin-internal file.

---

## Known pre-existing README staleness (not fixed this session)

`plugins/a4/README.md` has issues that predate this session and were **not** addressed by the rename. Noting here so a future session can tackle them deliberately:

1. **Skill table is missing 3 entries** — `drift`, `index`, and `handoff` were added in think 0.19.0 / 0.20.0 / earlier, but the table still lists only 9 skills. Table names themselves are correct (post-rename), just incomplete.
2. **"Document Layout" section describes the pre-ADR aggregated-stage-file model** — references `a4/<topic-slug>.usecase.md`, five-icon INDEX vocabulary, `reflected_files` frontmatter, etc. None of this matches the spec-as-wiki+issues ADR. Rewriting this section to match the new per-item + wiki-page model is a natural companion to the compass redesign.
3. **Description line** at top reads "Co-thinking plugin — usecase/spec/implementation-plan design, autonomous code execution, brainstorming, decision-making, and GitHub automation." — retained from the original. A tighter description focused on `a4/` workspace management would match the new plugin identity but was not rewritten this session.

Fixing these is out of scope for the rename session and should be batched with the compass redesign (ADR Next Step 6) or a focused README-rewrite session.

---

## Next Steps (from ADR + new ADR, post-session state)

The a4-redesign ADR's Next Steps are unchanged by this session (naming is orthogonal). The open items remain:

1. **Schema finalization** — per-type lifecycle vocabularies, YAML date typing, comment/log section format, path reference grammar. → `plugins/a4/references/frontmatter-schema.md` or equivalent.
2. ~~Drift detector~~ (done 1451)
3. **Obsidian markdown conventions doc** — `plugins/a4/references/obsidian-conventions.md` to deduplicate Wiki Update Protocol sections inlined in `usecase/SKILL.md`, `arch/SKILL.md`, `plan/SKILL.md`.
4. **`.handoff/INDEX.md`** — topic-grouped dashboard driven by `scripts/topic_references.py`. Deferred 4 sessions running; the thread now has 7 handoffs under `plugins/a4/.handoff/` (including this one), making the INDEX's value increasingly tangible.
5. ~~a4/INDEX.md redesign~~ (done 1524)
6. **Compass redesign** — Steps 1.2 (artifact scan) and 3 (gap diagnosis with drift detection) rewritten for the new layout. Step 0 INDEX refresh is already done. `legacy note` at the top of Steps 1–3 in `compass/SKILL.md` flags exactly what needs rewriting. **README Document Layout rewrite pairs naturally here.**
7. **Spark skill alignment** — `spark-brainstorm` and `spark-decide` still need their own lifecycle frontmatter. The status-field conflict that originally triggered the entire redesign is still unresolved in the spark files themselves.
8. **Obsidian dataview reference snippets** — seed material now exists in `scripts/index_refresh.py`.

**New follow-up from this session:**

9. **README rewrite** — see "Known pre-existing README staleness" above. Best bundled with item 6 (compass redesign) since both touch the same "what does the current layout look like" narrative.

Recommended ordering for the next concrete session: **Compass redesign (item 6)** + README Document Layout rewrite (item 9, same scope). Both are long-overdue and growing in friction the longer they sit.

---

## Design decisions made during the rename

These shaped the execution but were judgment calls worth flagging:

1. **Commit as a single squash (76 files)** rather than per-sub-rename. Rationale: the 1.0.0 boundary is the "before/after" marker; splitting would force consumers to checkout intermediate states that are partially migrated. One breaking commit is cleanest.

2. **Version bump to 1.0.0** (not 0.21.0). The breaking rename is a natural semver major milestone; 1.0.0 also signals the convention lock-in. Per ADR Rejected Alternatives, 0.21.0 was considered and rejected.

3. **`auto-` prefix retained.** Considered symmetric rename `auto-usecase` → `usecase` and bare `usecase` → `guided-usecase` for axis symmetry. Rejected: would force new "guided-" vocabulary that users have to learn. Asymmetric (bare = interactive default, `auto-` = variant) is the minimal framing.

4. **`a4-handoff` example in the 2026-04-23 ADR's rejected alternatives.** The original example was `think-handoff` (because `think` was the plugin name and the stutter was the point). With the rename, `think-handoff` no longer stutters — but `a4-handoff` does, under the same principle. Updated the example to `a4-handoff` and added a cross-reference to the new naming-convention ADR. The principle is unchanged; only the instantiation moved.

5. **Handoff files retained verbatim.** `plugins/a4/.handoff/*.md` still contain `plugins/think/`, `/think:think-*`, etc. This is correct per the handoff contract ("point-in-time snapshot, never edit"). Anyone reading a handoff from 2026-04-23 sees what the plugin looked like on 2026-04-23.

6. **Historical ADR filename kept.** `2026-04-12-think-pipeline-restructuring.decide.md` retained as-is even inside `plugins/a4/a4/`. The topic was literally named that. Renaming the file would misstate history.

7. **Codex plugin version unchanged** (`0.9.1`). Different versioning scheme from claude's 1.0.0 bump. The codex plugin predates this repo's marketplace versioning and advances on its own cadence. Not bumped unless there's a codex-specific change to track.

8. **`plugin.json` detected as delete+add rather than rename** by git. Similarity fell below git's threshold because the file is small (~3 lines changed out of ~4). Purely cosmetic in `git log`; the content transition is coherent.

---

## Breaking change scope for downstream consumers

Anyone who has installed or referenced this plugin must migrate:

- **Installation path** — marketplace entry renamed from `think` to `a4`; source is `./plugins/a4`. Any user configuration that pins `think` needs updating.
- **Invocation paths** — every `/think:<X>` becomes `/a4:<X>` (with some skill slugs also shortened; see mapping above).
- **Subagent types** — `Agent(subagent_type: "think:<agent>")` becomes `"a4:<agent>"`. Important for any code outside this repo that spawns these agents.
- **Script paths** — `plugins/think/scripts/*.py` is now `plugins/a4/scripts/*.py`. Hook configurations or external shell scripts calling these paths must update.
- **`.handoff/` location hint** — not functionally breaking (the global handoff skill still works with any directory), but the canonical example now points to `plugins/a4/.handoff/`.

No compatibility shim was added — per ADR, this is a breaking migration milestone, not a gradual deprecation.

---

## Files to read first next session

1. **`plugins/a4/a4/2026-04-24-skill-naming-convention.decide.md`** — the authoritative naming ADR. Read before adding any new skill.
2. **`plugins/a4/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — the underlying spec-as-wiki+issues ADR. Next Steps section lists the remaining work; note that item 6 (compass redesign) is the current bottleneck and grows in awkwardness the longer it sits.
3. **This handoff** — narrative wrapper.
4. **`plugins/a4/skills/compass/SKILL.md`** — Steps 1–3 still carry the legacy note from the 1524 session. Rewriting these is the next concrete work.
5. **`plugins/a4/README.md`** — see "Known pre-existing README staleness" above; rewrite naturally pairs with compass redesign.
6. **`plugins/a4/.handoff/2026-04-24_1524.md`** — prior handoff on this thread.

---

## Explicitly rejected / not done this session

- **Renaming `auto-*` skills for axis symmetry.** Considered `auto-usecase` → `usecase` with `usecase` (current) becoming `guided-usecase`. Rejected: new "guided-" vocabulary adds complexity without solving a real problem. Bare = interactive / `auto-` = autonomous is cleaner.
- **Renaming `spark-*` skills.** Pipeline prefix is justified (2 stages share it). No change.
- **Verb-first naming scheme.** Considered `draft-usecase`, `check-drift`, `refresh-index`. Rejected: collapses the mode/scope/orchestration axes into a verb dimension, losing information.
- **Rewriting handoff files or historical ADR filenames.** Intentional preservation of history.
- **Updating "think 0.18.0" annotations to "a4 0.18.0".** The plugin was literally named `think` at that version; rewriting would misstate.
- **Building a compatibility shim or `think` → `a4` alias.** 1.0.0 is a hard migration milestone per ADR decision.
- **Fixing the README Document Layout section** (pre-ADR content). Out of scope — belongs with the compass redesign.
- **Adding `drift`, `index`, `handoff` to the README skill table.** Pre-existing staleness, not introduced by the rename; flagged for future session.
- **Codex plugin version bump.** Different versioning scheme; no codex-specific changes this session.

---

## Non-goals for next session

- Do not partially un-rename anything to "smooth the transition" — the 1.0.0 boundary is intentional. If a caller breaks, the caller updates; a shim would defeat the migration.
- Do not reintroduce `think-`, `a4-`, or any plugin-name prefix on new skills. The naming ADR forbids it.
- Do not edit prior handoff files to say `plugins/a4/` — they are snapshots.
- Do not rewrite the historical ADR filename `2026-04-12-think-pipeline-restructuring.decide.md`.
- Do not bump a4 past 1.0.0 without new functionality. 1.0.0 is the rename lock-in; the next substantive feature (compass redesign, spark alignment, etc.) triggers 1.1.0.

---

## Working-tree state at handoff time

Pre-handoff state: working tree clean after commit `d50d2dea8`. No non-handoff changes pending at step 2 — step 2 was skipped.

Changes bundled into this handoff's commit (step 5):

```
new file:   plugins/a4/.handoff/2026-04-24_1602_plugin-rename-and-naming-adr.md    # this file
```

Branch state: `main` is 15 commits ahead of `origin/main` before this handoff's commit; will be 16 commits ahead after.
