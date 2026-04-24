---
timestamp: 2026-04-24_2033
topic: decision-slot-unification
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_2033. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

Collapse the redundant decision-record slots that had grown up in parallel: `a4/spark/<YYYY-MM-DD-HHmm>-<slug>.decide.md` (spark-decide output, draft|final|superseded) and `a4/decision/<id>-<slug>.md` (issue-tracker ADR slot, same status enum). The two had nearly identical frontmatter; the validator schema even had a post-hoc "Asymmetry with `decision/` folder issues" rationalization. User confirmed the duplication was an accidental LLM-accumulated artifact, not a designed distinction, and that `a4/decision/` is actively used as the ADR home.

Resolved by making `/a4:spark-decide` write directly into `a4/decision/<id>-<slug>.md` as a first-class issue. The spark/ folder now holds only brainstorm files. Session trace (Options Considered, Research Findings, Evaluation, Discussion Log) stays in the same decision file with heavy sections wrapped in `<details>` — the user chose "B1" (single file with collapse) over "B2" (sidecar subfolder) over "C" (explicit promote flow).

# Decisions made

1. **Retire the `spark/*.decide.md` slot.** A single decision lives in exactly one file at `a4/decision/<id>-<slug>.md` regardless of whether it came from `/a4:spark-decide` or direct authoring.
2. **B1 = inline session trace.** All phases of the spark-decide session end up in the same decision file. `<details><summary>…</summary>` collapses Discussion Log and per-option raw excerpts so the file stays scannable.
3. **No research sidecars.** The `a4:api-researcher` agent now returns its findings as a markdown subsection (`### Option N: <name>`) in its response; spark-decide inserts that subsection into the decide file's `## Research Findings` at the next checkpoint. No `a4/<topic-slug>.decide.research-*.md` files, no research-index file.
4. **Slash command + user interface unchanged.** `/a4:spark-decide` remains the invocation. Skill name, triggers, argument hint all stay the same. Only the output location and frontmatter shape change.
5. **Id allocation on file creation.** spark-decide runs `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "<workspace>/a4"` after Problem Framing (Phase 1) to reserve a global monotonic id before writing the initial file.
6. **Topic → `title:` direct mapping.** The old `topic:` field in spark-decide frontmatter becomes `title:` on the decision issue. `type:` and `pipeline:` fields are dropped entirely (the `decision/` folder location already classifies the file).
7. **Wiki-nudge footnote payload updated.** On finalize, wiki page footnotes now point at `[[decision/<id>-<slug>]]` (not `[[spark/<decide-basename>]]`). Deferred review items likewise set `target: decision/<decision-id>-<slug>`.

# Rejected alternatives (discussed)

- **Remove `a4/decision/` entirely and keep spark/<>.decide.md as the canonical ADR slot.** Dismissed because the user confirmed `decision/` is actively used.
- **Keep both slots with a promote flow (spark/<>.decide.md draft → decision/ final via a new `/a4:decide-promote` skill).** Dismissed because it doubles the decision surface area and risks drift between a session-trace file and a canonical-summary file.
- **B2 = sidecar folder `a4/decision/<id>-<slug>/*.md` for research and discussion log.** Dismissed by the user after weighing it against B1. Main concern: introduces a folder-form-for-some, file-form-for-others asymmetry that the 2026-04-24-experiments-slot ADR had already rejected for the analogous `task/poc/` sidecar case. (Markdown-contract erosion reason does *not* apply here — research is markdown — but the asymmetry concern does.)

# What changed (11 files, commit `7d383f5b4`)

**Skill + agent contract**
- `skills/spark-decide/SKILL.md` — Working File Path, Initial File Content, Phase 3 Research, Wrapping Up wiki-nudge paragraphs all rewritten for the new target. Allocate-id step added at file creation. Footnote/review-target payloads updated to `decision/<id>-<slug>`.
- `skills/spark-decide/references/adr-template.md` — Frontmatter swapped (`id`/`title`/`related` in, `type`/`pipeline`/`topic` out). Header line becomes `# <topic>` (no "Decision Record:" prefix).
- `skills/spark-decide/references/research-report.md` — Full rewrite. Describes the inline-subsection contract instead of the old sidecar + index convention. Includes the agent's markdown template with `<details>` for raw excerpts.
- `skills/spark-brainstorm/SKILL.md` L98 — `promoted:` example updated from `[spark/<decide>, usecase/<n>-<slug>]` to `[decision/<id>-<slug>, usecase/<id>-<slug>]`.

**Schema + conventions**
- `references/frontmatter-schema.md` — "Spark decide" per-type section removed. Spark family row collapsed to brainstorm-only. `supersedes` applies-to column reduced to `decision` only. `promoted` targets list no longer mentions `spark/decide`. Path-reference grammar note tightened to say only `.brainstorm` stays in spark filenames. Decision section gained a paragraph noting that spark-decide output arrives through this same schema. Sources list updated.
- `references/obsidian-conventions.md` L13 — Spark files bullet now says `spark/*.brainstorm.md` only, with a historical-note parenthetical about the retirement.

**Top-level doc**
- `README.md` — layout diagram `{brainstorm,decide}` → `brainstorm`; skills table entry for spark-decide reads `Solution discovery facilitator; writes an ADR as a4/decision/<id>-<slug>.md`.

**Dashboard + validator**
- `skills/index/SKILL.md` L58 — Spark section description narrowed to brainstorm-only terminal-state filter.
- `scripts/validate_frontmatter.py` — `spark_decide` `Schema` entry removed. `detect_type` no longer returns `spark_decide` for `folder == "spark"` with `type: decide`; such files now detect as `None` (unknown, passed through silently). The existing `decision` schema is already a superset for spark-decide's needs, so no new entry was required.
- `scripts/index_refresh.py` — `SPARK_TERMINAL` drops the `decide` key; `SparkItem.flavor` only recognizes `.brainstorm`.

**Version**
- `.claude-plugin/marketplace.json` — a4 plugin `1.3.0` → `1.4.0`.

# Explicitly untouched

- `plugins/a4/spec/*.decide.md` — these are the plugin's own hand-authored meta-ADRs, **not** `/a4:spark-decide` output. User called this out explicitly. They continue to use the legacy pre-redesign naming and are not migrated by this change. Whether to migrate them to the new decision-issue shape (with id allocation etc.) is a separate topic if ever raised.
- `/a4:spark-decide` invocation string in other skills' SKILL.md — `arch/SKILL.md:213`, `compass/SKILL.md:72`, `idea/SKILL.md:115`, `spark-brainstorm/SKILL.md:129` still reference the slash command. These remain correct because the slash command name did not change.
- Agents — a cross-check of `agents/*.md` for spark/decide references found none that needed updating (domain-updater's `<topic-slug>.usecase.history.md` is a different artifact).

# Validation performed

- `uv run scripts/validate_frontmatter.py` on a synthetic workspace containing one `decision/1-test.md` and one `spark/2026-04-24-1530-test.brainstorm.md` — both pass with `OK — 2 file(s) scanned, no violations.`
- `uv run scripts/index_refresh.py --dry-run` on an empty workspace renders the full template (Spark section shows `(open 0)` / `*No open sparks.*` correctly).
- AST parse check on both edited Python scripts.

# Plausible follow-ups (not done; user has not requested)

1. **decision-reviewer agent review.** The agent (`plugins/a4/agents/decision-reviewer.md`) evaluates decision records. It was never inspected during this session for compatibility with the new frontmatter/body shape. It likely already works because the criteria it checks (completeness, bias, rationale, rejection clarity, reversibility, actionability) are body-level, not frontmatter-level — but a sanity read is prudent if spark-decide is exercised for real.
2. **Existing `spark/*.decide.md` migration path.** If a real a4 workspace out there has shipped decide files in `spark/`, they will validate as `type: decide` files in a spark folder with no schema to match them — `detect_type` now returns `None` for them, so they pass silently (the validator treats "no matching schema" as "don't validate", not "error"). This is benign for new workspaces but may leave old ones with orphaned files that no tool touches. A `/a4:spark-decide-migrate` cleanup skill could be written if the pattern surfaces in practice; deliberately deferred per the same "mechanical and infrequent" rationale as `/a4:idea-promote` and `/a4:spike-archive`.
3. **`decision/` body template / validator.** There is no body-level schema for decision issues today — the frontmatter validator checks frontmatter only, `validate_body.py` handles wiki pages only. If the project wants to enforce the presence of Context / Decision / Rejected Alternatives sections in decision issues, that would be a new validator. Low priority.
4. **Plugin spec folder alignment.** `plugins/a4/spec/*.decide.md` continue to use the pre-redesign convention (spark-decide frontmatter with `type: decide, pipeline: spark, topic:`). If the plugin-authoring convention ever unifies with the new decision-issue shape, migration is trivial (rename + reshape frontmatter) but would be a deliberate editorial decision, not a mechanical sweep.

# Key files to re-read on the next session

- `plugins/a4/skills/spark-decide/SKILL.md` — authoritative contract for the new flow.
- `plugins/a4/references/frontmatter-schema.md` §Decision — the shared frontmatter target.
- `plugins/a4/skills/spark-decide/references/research-report.md` — the api-researcher output contract.
- `plugins/a4/scripts/validate_frontmatter.py` L127-onwards — confirms spark-family schemas (only brainstorm survives).

# Outstanding parked threads (unrelated to this session)

None that surfaced this session. Prior threads (`a4-redesign`, `experiments-slot`, `idea-slot`) are in their own handoff subdirectories and are unaffected by these edits.
