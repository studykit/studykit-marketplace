---
timestamp: 2026-04-24_2117
topic: decision-slot-unification
previous: 2026-04-24_2033_spark-decide-writes-to-decision.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_2117. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

Follow-up to the preceding `decision-slot-unification` session (which rerouted `/a4:spark-decide` output into `a4/decision/<id>-<slug>.md`). Having collapsed the slot, this session questioned whether the `/a4:spark-decide` skill itself still had reason to exist — its output had become indistinguishable from a hand-authored decision issue. Decision: **retire spark-decide entirely** and split its remaining value into two focused, smaller-surface skills. Decision authorship itself is no longer owned by any skill — users hand-write `a4/decision/<id>-<slug>.md` directly.

# Decisions made

1. **Retire `/a4:spark-decide`.** The skill folder is deleted. No deprecation shim. Slash command `/a4:spark-decide` no longer resolves.

2. **New skill `/a4:research` — standalone investigation facilitator.**
   - Output: `./research/<slug>.md` at **project root**, not under `a4/`. Explicitly decoupled from the `a4/` workspace — runs without one.
   - Filename: **slug-only**. No id, no timestamp. Collisions resolved with `-2`, `-3` suffixes.
   - Frontmatter: `topic`, `status` (`draft | final`), `mode` (`comparative | single`), `options` (comparative only), `created`, `updated`, `tags`. No `id`, no `type`, no `pipeline` — the folder location classifies the artifact.
   - Two modes: `comparative` (2+ options) runs `a4:api-researcher` in parallel, inserts each returned subsection under `## Options`; `single` (one topic) has the skill research directly via `WebSearch`/`WebFetch`/`get-api-docs`/`find-docs`, writes a flat `## Findings` section.
   - Body contract lives in `plugins/a4/skills/research/references/research-report.md`. Raw excerpts wrapped in `<details>` per the B1 single-file principle.
   - Output is a **reference** for downstream decisions — cited via `related: [research/<slug>]` from `a4/decision/<id>-<slug>.md`. Does not evaluate / score / decide.

3. **New skill `/a4:decision-review` — finalization facilitator.**
   - Input: path to a hand-drafted `a4/decision/<id>-<slug>.md`. Requires an `a4/` workspace (unlike `/a4:research`).
   - Flow: runs `a4:decision-reviewer` agent → walks 7-criteria review report with user (accept / modify / dismiss per issue) → applies revisions → flips `status: draft → final` and fills `decision:` one-liner → performs the in-situ wiki nudge (architecture / context / domain / actors / nfr) with footnote + review-item fallback per the wiki update protocol.
   - All the wrap-up logic from the old spark-decide Phase 5 + Wrapping Up lives here.

4. **api-researcher scope kept narrow.** The existing `a4:api-researcher` agent remains specifically an API/library/SDK documentation researcher (uses `get-api-docs`, `find-docs`, web fallback). `/a4:research` routes comparative API-centric options through it; for non-API-centric options (patterns, qualitative trade-offs) and for single-topic mode, `/a4:research` researches directly. The agent's description and internal contract were not changed.

5. **Decision authorship is user-owned.** No skill facilitates writing the decision itself anymore. Users hand-write `a4/decision/<id>-<slug>.md`, optionally after `/a4:research`, optionally followed by `/a4:decision-review`. The `decision` frontmatter schema in `references/frontmatter-schema.md` is unchanged from the preceding session (it was already the target).

# Rejected alternatives (discussed)

- **Keep `/a4:spark-decide` as-is (option 1).** Dismissed because post-unification the output is indistinguishable from a hand-authored decision issue, so the skill's value was entirely in *process* (facilitation scripts, parallel research, wrap-up). Most of the process value is either replicable via plain prompting (Problem Framing questions, Devil's Advocate / Reframer challenges, framework-selection matrix) or is better owned by smaller tools.
- **Slim by removing facilitation only (option 2 "slim").** Dismissed: would have kept the one-big-skill shape; the user preferred clearer separation.
- **Broaden `api-researcher` to be a general researcher (option C-2 from api-researcher scope discussion).** Dismissed: the agent's narrow scope works well and its name is clear; broadening invites scope creep.
- **Put research under `a4/research/<slug>.md`.** Dismissed: the user explicitly chose project-root `./research/`, positioning research as a workspace-level portable artifact usable even outside an `a4/` context.
- **Timestamp-based research filenames (`./research/<YYYY-MM-DD>-<slug>.md`) or id-based (`./research/<id>-<slug>.md`).** Dismissed in favor of slug-only: id allocation has no natural scope outside `a4/`, and slug-only reads cleanest in cross-references (`[[research/grpc-streaming]]`).

# What changed (18 files, commit `608a40db1`)

**New skills**
- `plugins/a4/skills/research/SKILL.md` — `/a4:research` body. Scope / input handling / file path / mode split / orchestration / wrap-up / non-goals.
- `plugins/a4/skills/research/references/research-report.md` — agent output contract (comparative per-option subsection + single-mode flat findings), checkpoint write flow.
- `plugins/a4/skills/decision-review/SKILL.md` — `/a4:decision-review` body. Pre-flight / reviewer run / walk-findings / apply revisions / finalize / wiki nudge / report.

**Deleted**
- `plugins/a4/skills/spark-decide/SKILL.md`
- `plugins/a4/skills/spark-decide/README.md`
- `plugins/a4/skills/spark-decide/references/adr-template.md`
- `plugins/a4/skills/spark-decide/references/research-report.md`
(folder `plugins/a4/skills/spark-decide/` no longer exists)

**Caller updates (4 skills)**
- `skills/spark-brainstorm/SKILL.md` L125-129 — "Handoff to Solution Discovery" section rewritten as "Handoff to Research and Decision" with two-step path: run `/a4:research <file_path>`, then hand-author `a4/decision/<id>-<slug>.md`, then `/a4:decision-review <decision_path>`.
- `skills/spark-brainstorm/README.md` L84 — plantuml diagram's trailing "Suggest handoff to spark-decide" becomes "research + decision-review".
- `skills/arch/SKILL.md` L213 — Phase 1 heavy-choice nudge rewritten to suggest `/a4:research` first, then hand-author + `/a4:decision-review`.
- `skills/arch/README.md` L50 — plantuml diagram's "Suggest spark-decide" becomes "Suggest /a4:research".
- `skills/compass/SKILL.md` L72 — Ideation skill catalog: `spark-decide` row replaced with two rows for `research` and `decision-review`.
- `skills/idea/SKILL.md` L115 — Non-Goals bullet: "`/a4:spark-decide`" replaced with "`/a4:research`". ("decide session" wording also updated to "research session".)

**Schema + conventions**
- `references/frontmatter-schema.md` — Decision section prose rewritten (L194-195) to describe the hand-authored + `/a4:research` + `/a4:decision-review` split. Historical note at L257 updated to describe the skill split (not just the slot retirement). Cross-references at L297 updated.
- `references/obsidian-conventions.md` L13 — historical note in Spark files bullet updated to mention research at project-root `./research/`.

**Top-level doc**
- `plugins/a4/README.md` — skills table: `spark-decide` row removed, `research` and `decision-review` rows added. Layout diagram: added `research/<slug>.md` at project root (below `spike/`, sibling of `a4/`) with a brief "Cited from a4/decision/ via `related: [research/<slug>]`" gloss.

**Scripts**
- `scripts/index_refresh.py` — `SparkItem.flavor` comment updated (just a comment; behavior unchanged — only `.brainstorm` was already supported).
- `scripts/validate_frontmatter.py` — **no code changes this session**. Unchanged from the preceding commit (`7d383f5b4`).

**Version**
- `.claude-plugin/marketplace.json` — a4 plugin `1.4.0 → 1.5.0`.

# Explicitly untouched

- **arch's `a4/research/<label>.md` claim-verification cache.** `arch/SKILL.md:26`, L256-259, L291 continue to reference `a4/research/<label>.md` as the destination for `a4:api-researcher` claim-verification outputs during architecture design. This predates this session and is a **different** convention from the new project-root `./research/<slug>.md`:
  - `a4/research/<label>.md` (arch-internal): short per-claim verification snippets, internal to arch, workspace-scoped.
  - `./research/<slug>.md` (new): portable long-form research artifact, cross-skill, project-root-scoped.
  They coexist. If the name collision ever surfaces as pain in practice, the cleanup options are (a) rename arch's destination to e.g. `a4/verification/<label>.md`, or (b) unify both into `./research/`. Neither is done here.
- **`plugins/a4/spec/*.decide.md`** — the plugin's own hand-authored meta-ADRs. Same explicit-untouched carve-out as in the preceding handoff; not `/a4:spark-decide` output and not migrated.
- **Agents.** `a4:api-researcher` and `a4:decision-reviewer` were not modified. Both continue to work exactly as before; only their callers changed.
- **Hooks.** `hooks/record-edited-a4.sh`, `hooks/validate-edited-a4.sh`, etc. unchanged — they scope to `a4/`, so `./research/` files are outside their scope by design.
- **`scripts/validate_frontmatter.py`** — no changes needed. `./research/` is outside `a4/`, so the validator never scans it. No research-family schema was added (user confirmed: no validation for research files).
- **Old `decision-slot-unification` handoff** — the preceding handoff file stays frozen per its own DO-NOT-EDIT banner; this new file in the same topic subdirectory chains via `previous:`.

# Verification performed

- `uv run scripts/validate_frontmatter.py` on a synthetic workspace containing `decision/1-test.md` + `spark/2026-04-24-1530-test.brainstorm.md` — both pass: `OK — 2 file(s) scanned, no violations.`
- `uv run scripts/index_refresh.py <empty-workspace>/a4 --dry-run` — renders the template cleanly; Spark section shows `(open 0)` with `*No open sparks.*` as expected.
- AST parse check on `scripts/validate_frontmatter.py` and `scripts/index_refresh.py`: both parse cleanly.
- `grep -rn "spark-decide\|spark_decide\|spark/.*\.decide"` across `plugins/a4/` and `.claude-plugin/`, excluding `.handoff/` and `spec/`: the only remaining matches are the two **intentional** historical notes in `references/obsidian-conventions.md:13` and `references/frontmatter-schema.md:257`. All active callers updated.
- Manual read of all three new SKILL.md files for consistency with the schema doc and with each other.

# Plausible follow-ups (not done; user has not requested)

1. **decision-reviewer agent sanity read.** Same carry-over from the preceding handoff. Agent was not inspected this session either. It should work because criteria are body-level, but a read-through is prudent before the first real `/a4:decision-review` run.

2. **arch's `a4/research/` convention cleanup.** See "Explicitly untouched" above. If the word "research" referring to two different shapes in two different locations becomes confusing in practice, either rename arch's destination or unify. Low priority until pain surfaces.

3. **Research referenced-from-decision grammar test.** The `research: [research/<slug>]` citation form from `a4/decision/<id>-<slug>.md` uses workspace-root-relative path convention. `frontmatter-schema.md §Path references` already allows plain strings; the validator allows unknown fields; so `related:` entries to `research/<slug>` should pass silently. Not independently tested this session. If Obsidian wikilink resolution is desired for `[[research/<slug>]]` in decision body prose, the Obsidian vault needs to include `./research/` in its root — out of scope for this plugin.

4. **Legacy `spark/*.decide.md` migration.** Unchanged carry-over from preceding handoff: if any real workspace has pre-existing spark-decide files, they now validate silently (detect_type returns `None` for `folder == "spark"` with `type: decide`). A `/a4:spark-decide-migrate` cleanup is still deferred on the "mechanical and infrequent" rationale.

5. **Body-level validator for `decision/`.** Unchanged carry-over. If `## Context / ## Decision / ## Rejected Alternatives` should be enforced in decision bodies, a new validator is required. Low priority.

6. **Rename `spark-decide-split`-style topic?** This handoff chains under `decision-slot-unification`. If future sessions in this thread continue to evolve the decide/decision/research surface, the topic name is fine. If the thread turns toward something outside decision-making (e.g., spike-task or idea-slot further evolutions), start a new topic then.

# Key files to re-read on the next session

- `plugins/a4/skills/research/SKILL.md` — the authoritative contract for `/a4:research`.
- `plugins/a4/skills/research/references/research-report.md` — the body format (comparative + single).
- `plugins/a4/skills/decision-review/SKILL.md` — the finalize + wiki-nudge pipeline.
- `plugins/a4/references/frontmatter-schema.md §Decision` — the hand-authored decision issue schema (target of `/a4:decision-review`).
- `plugins/a4/agents/decision-reviewer.md` — unchanged but now invoked exclusively by `/a4:decision-review`; the 7-criteria contract drives the walk-findings step.
- `plugins/a4/agents/api-researcher.md` — unchanged but now invoked by `/a4:research` in comparative mode only.
- `plugins/a4/README.md` — layout diagram and skills table reflect the new state.

# Outstanding parked threads (unrelated to this session)

None newly surfaced. Prior parked items (`a4-redesign`, `experiments-slot`, `idea-slot`, plus the preceding `decision-slot-unification` handoff) remain in their own subdirectories and are unaffected by these edits.
