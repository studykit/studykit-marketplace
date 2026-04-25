---
timestamp: 2026-04-26_0103
topic: pipeline-restructure
previous: 2026-04-25_2207_pipeline-shapes-named.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-26_0103. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Pipeline restructure — Topic #15′ shipped (ADR-trigger detection)

## Session context

Continuation of the pipeline-restructure thread from `2026-04-25_2207_pipeline-shapes-named.md`. That session left three backlog items: #14 (drift_detector staleness propagation), #15 (ADR-trigger detection), and a "consideration" to extend `plugins/a4/CLAUDE.md` always-read-first list. The user picked **#15**.

Designing #15 ran as a long discussion-first thread that progressively rescoped the original signal catalog. Several signals were dropped, simplified, or reclassified mid-design:

1. **A2** ("`kind: feature` task with empty `implements:`/`justified_by:`") was first treated as a static script signal, then reframed twice. First step: noted that small features (UI tweaks, validation tweaks, roadmap-auto-generated features without a UC group) legitimately have neither anchor — A2 cannot be a binary frontmatter rule. Second step: user observed the real signal lives in **task body content**, not frontmatter — only by reading the task can the LLM tell whether a UC is missing or an ADR is missing. A2 was reclassified as **content-aware upward-propagation** (a new sub-class beyond static-A and conversational-B), to be detected by LLM-side reads at task creation/review time.

2. **A3** (supersede chain integrity) was dropped entirely once the audit found `validate_status_consistency.py` already detects both directions of mismatch (stale terminal status without supporting cross-reference, and unflipped status despite supporting cross-reference) and runs at SessionStart + PostToolUse. `transition_status.py`'s existing cascade flips the predecessor's `status: superseded` atomically when the successor reaches `final`. The proposed `--by` flag and a new drift rule were both redundant. **C2 (the A3 commit) was removed from the plan.**

3. **A4** (substantive edit without `## Changes` update) was simplified from a detection rule to an **auto-fix**. The user proposed: when `## Changes` heading is absent, just append it silently — no review item, no flood, no dedup. The temporal-staleness portion of A4 ("body changed but `## Changes` didn't follow") was deferred to Topic #14′ since it requires git/cache infrastructure.

4. **A5** (research not cited by ADR) was reframed three times. First step: the user pointed out citation cannot be detected after the fact — it has to be produced atomically at the moment of decision authoring. Second step: user wanted `research:` in **decision frontmatter** for searchability, contradicting the schema's "body prose only" rule. Third step: user wanted a stored reverse-link `cited_by:` on the research file with **both** frontmatter and body representation. Final shape: atomic four-place dual-write (`register_research_citation.py`).

5. **A6 / A7 / B7 / B8** (proposed catalog additions) were dropped as either weak signals, expensive to detect, or out of ADR-trigger scope.

After the design converged, four commits shipped Topic #15′. The original Topic #15 from the prior handoff is shipped at this scope; the part of the work that depends on temporal/git infrastructure (downstream propagation, "body changed but `## Changes` didn't follow") moves to **Topic #14′** when that is picked up.

## Topic backlog at session end

| ID | Title | Status |
|---|---|---|
| #1 | Pipeline stage 경계 | completed (session 1) |
| #2 | Wiki authorship 분배 | completed (session 1) |
| #3 | Bootstrap 위치/타이밍 + L&V owner | completed (session 1) |
| #4 | Interactive vs Autonomous skill 짝맞춤 | completed (session 2) |
| #5 | `/a4:run` 내부 seam | completed (session 2) |
| #6 | Iteration 모델 통일 | completed (session 2) |
| #7 | Brownfield/minimal 파이프라인의 1급 시민화 | completed (session 3) |
| **#15′** | **ADR-trigger detection (rescoped — A1+A4+A5+B+A2-reframed; A3 dropped)** | **completed this session** |
| #14′ (rescoped) | drift_detector staleness propagation, generalized wiki-wide (covers original #14 + A1's downstream-direction case + A4's temporal-staleness case + the `## Changes` advance → propagate-to-dependents pattern the user surfaced mid-design) | pending |
| (consideration) | `plugins/a4/CLAUDE.md` always-read-first 리스트 확장 — now also includes whether to add `adr-triggers.md` | pending |

## What shipped this session

Four commits on `main`:

| SHA | Subject | Component |
|---|---|---|
| `6d828e94d` | feat(a4): auto-fix missing `## Changes` heading on wiki pages in drift_detector | C3 (A4) |
| `0968fa53e` | feat(a4): detect missing ADR citations in architecture.md ## Changes | C1 (A1) |
| `ed372e732` | feat(a4): atomically register research → decision citations across both files | C4 (A5) |
| `a3ed11c2a` | feat(a4): catalog ADR-trigger signals + cite from skills that detect them | C5 (B + A2-reframed) |

`marketplace.json` `a4` version: 1.30.0 → **1.31.0** (bump landed in C5).

A small unrelated commit `e7d46c127 chore(prompts): clarify discuss memory boundary` is interleaved in the chain (between C4 and C5) — it is not part of Topic #15′.

### C3 — A4 auto-fix (`6d828e94d`)

**Decision.** The original A4 ("wiki page substantively edited without `## Changes` updated") split into two parts. The snapshot-detectable part (`## Changes` heading absent) was simplified to an auto-fix; the temporal part (body changed but `## Changes` didn't follow) moved to Topic #14′.

**Implementation.** `drift_detector.py` gains an `ensure_changes_section(path, dry_run)` function that scans for `^##\s+Changes\s*$` and appends an empty `## Changes` heading when missing. Runs in `main()` for each wiki page **before** detection, respects `--dry-run` (reports "would auto-fix" without mutating). The newly-empty section is left for subsequent edits to populate via the standard footnote protocol.

**Deliberate omissions.** No empty-section detection (very rare in practice). No flood-suppress logic for the orphan-marker rule when the same page has inline markers without definitions — orphan-marker is allowed to fire normally (low-priority, individually meaningful).

### C1 — A1 missing-adr-cite drift rule (`0968fa53e`)

**Decision.** When `architecture.md`'s `## Changes` records a change without any `decision/*` ADR wikilink in the footnote body, emit a `kind: gap` drift review item. Architecture-only by design (per `pipeline-shapes.md` ADR cross-cutting: ADR production primary site is `/a4:arch`). Filter policy `δ` per the design discussion: emit **all** orphan entries, control noise via the existing `discarded` dedup blocking (per-footnote fingerprint).

**Implementation.** New drift kind `missing-adr-cite` registered in `KIND_TO_REVIEW_KIND` (gap), `KIND_TO_PRIORITY` (medium), `KIND_TO_TITLE` ("Missing ADR citation"). Detection folded into the existing `definitions.keys() & inline` loop in `detect_wiki_drift` — for each live entry, scan its wikilinks; if none resolve to `decision/*`, emit. Architecture-only via `if name == "architecture":` gate. New `build_review_item` branch produces a 3-path Suggested Resolution:

1. **ADR exists** — add `[[decision/<id>-<slug>]]` to footnote, set `resolved`
2. **ADR needed** — `/a4:decision`, then cite, set `resolved`
3. **No ADR warranted** — `discarded` + rationale; detector won't re-emit per-footnote

Snapshot mechanism — no git history, no mtime cache. Cause = `footnote-{label}` so each orphan footnote has independent fingerprint. Smoke test verified: orphan `[^1]` flagged, ADR-cited `[^2]` not flagged, `domain.md` skipped (architecture-only), `discarded` blocks re-emission, new footnote creates new fingerprint.

**Deliberate omissions.** No section-label scheme (β option discussed and rejected — would require `## Changes` entry schema extension). No keyword heuristic (γ option — fragile across languages). No `/a4:decision` write-time hook (β-light idea — deferred; γ + dedup blocking already covers manual-bypass cases).

### C4 — A5 research citation infrastructure (`ed372e732`)

**Decision.** The original A5 ("research not cited by ADR") was first proposed as a drift detection rule. Three reframes during design rejected detection in favor of atomic registration at decision-authoring time.

**Final shape (atomic four-place dual-write).** New script `scripts/register_research_citation.py` writes a single citation in four places per invocation:

1. `decision/<id>-<slug>.md` frontmatter `research:` list — append `research/<slug>` (initialize if absent)
2. `decision/<id>-<slug>.md` body `## Research` section — append `[[research/<slug>]]` wikilink (create section if absent)
3. `research/<slug>.md` frontmatter `cited_by:` list — append `decision/<id>-<slug>`
4. `research/<slug>.md` body `## Cited By` section — append `[[decision/<id>-<slug>]]` (create section if absent)

Plus bumps the research file's `updated:` to today. Idempotent — re-invocations are no-ops; unchanged sides are left alone. Smoke-tested end-to-end.

**Schema evolution (`frontmatter-schema.md`).** Departures from the prior schema, deliberately chosen for searchability:

| Before | After |
|---|---|
| Path-reference rule listed `usecase/`, `task/`, `review/`, `decision/`, `spark/` only | Adds `research/<slug>` (project-root sibling of `a4/`) |
| Stored-reverse table had one exception (`usecase.implemented_by`) | Adds `decision.research` ↔ `research.cited_by` as second exception (script-owned by `register_research_citation.py`; consumer = SessionStart staleness courtesy on `final` + empty `cited_by:` + old `updated:`) |
| Decision schema had no `research:` field; line 273 said "body prose only — not in frontmatter" | Decision table gains `research:` row; line 273 prose revised to describe the four-place dual-write; `related:` field still **not** for research (the dedicated `research:` field is the right slot) |
| Research file convention was undocumented (only "lives outside `a4/`, not validated") | New "Research artifact" section documents the lightweight project-level convention: `topic`, `status` (extended enum: `draft \| final \| standalone \| archived`), `mode`, `options`, `cited_by` (stored reverse), `tags`, `created`, `updated`. Validation still optional |

**SKILL.md updates.** `decision/SKILL.md`: Step 3 prose revised to instruct using the registrar; Step 5 frontmatter example gains `research: []`; Step 5 field doc adds `research:` and revises `related:`; new Step 5b invokes `register_research_citation.py` after the file is written; Step 2 gains a B4-aware bullet on supersede candidate detection. `research/SKILL.md`: both frontmatter examples (comparative, single) extended with the new status enum and `cited_by: []`; Wrapping Up step 2 documents `final` vs `standalone` choice; reference to the registrar replaces the old "auto-insert wikilink" hint.

**Deliberate omissions.** No `refresh_research_citations.py` SessionStart safety net was created. The atomic registrar is the only path; manual edits bypassing it can drift but were not seen as urgent enough to justify a refresh script in this iteration. Add later if real workspaces show drift.

### C5 — adr-triggers.md catalog + 5 cite sites + 4 reciprocations (`a3ed11c2a`)

**Decision.** The B-class signals (B1 multi-option, B2 trade-off, B3 uncertainty, B4 prior-decision, B5/B6 task-implementer architectural choice) plus the reframed A2 (content-aware upward propagation) plus anti-patterns are consolidated in a new shared reference. Each skill that detects these signals cites the doc rather than carrying inline copies. Mirrors the consolidate-and-cite pattern of Topics #4/#6/#7.

**Citation list (5 sites).**

| Skill / agent | Cite location | Why |
|---|---|---|
| `arch/SKILL.md` Phase 1 | After existing line 216 nudge | B1, B2 — heaviest ADR-production site |
| `research-review/SKILL.md` | Step 4 wrap-up area | B2, B3 — post-investigation handoff |
| `decision/SKILL.md` Step 2 | New bullet on Supersedes detection | B4 — supersede candidates |
| `agents/task-implementer.md` | New "Architecture-choice exit" section parallel to existing spec-ambiguity exit | B5, B6 — mid-implementation |
| `task/SKILL.md` Step 2 | After existing feature-anchor smell | A2 reframed (content-aware upward propagation) |

`/a4:run/SKILL.md` does **not** cite directly — the cite lives in the task-implementer agent file (the agent does the actual implementation work).

**Companion-list reciprocation.** Per Topic #7 polish pattern, each peer reference (`wiki-authorship.md`, `skill-modes.md`, `iterate-mechanics.md`, `pipeline-shapes.md`) gains a one-line entry pointing at `adr-triggers.md`. Discoverability — entering the hierarchy from any peer reference now surfaces ADR-trigger detection.

## Things deliberately not done

- **A3 dropped entirely.** `validate_status_consistency.py` (existing, runs at SessionStart and PostToolUse hooks) already detects supersede chain mismatches in both directions; `transition_status.py` already runs the cascade atomically on `→ final`. The proposed `--by` flag and the proposed `inconsistent-supersede-chain` drift rule were both redundant. Decision recorded in conflict audit.
- **No `refresh_research_citations.py`.** Atomic registrar is the only write path. Add a SessionStart back-scan only if real-world drift surfaces.
- **No `/a4:decision` write-time research nudge** beyond the Step 5b instruction. The β-light option from earlier discussion was folded into Step 5b unconditionally — every decision authoring runs the registrar for confirmed research, no separate "would you like to register?" prompt.
- **No flood-suppress logic for orphan-marker** when A4 auto-fix runs against a page with inline markers but no definitions. Discussed and accepted — orphan-marker fires individually, dedup handles repeats.
- **No section-label scheme for `## Changes` entries (β option for A1).** Rejected to avoid schema extension cost.
- **No keyword heuristic for ADR-worthy entries (γ option for A1).** Rejected — fragile across languages.
- **`plugins/a4/CLAUDE.md` always-read-first list** still cites only `frontmatter-schema.md`. Deferred from prior session and again from this session — pending consideration. With `adr-triggers.md` now in play, the question expands to whether to include it (along with `wiki-authorship.md`, `skill-modes.md`, `iterate-mechanics.md`, `pipeline-shapes.md`).
- **Topic #14′ untouched.** Original #14 was rescoped during this session's design audit — the user surfaced that staleness propagation should be wiki-wide (not arch-only). When Topic #14′ is picked up, expect to add: `## Changes` advance → propagate `kind: gap` review items to dependent wikis (per wikilinks/forward-link fields), plus the temporal-staleness part of A4 ("body changed but `## Changes` didn't follow"). Both require git or mtime infrastructure.
- **No push.** 43 commits ahead of `origin/main` (38 prior + 4 this session topic-#15′ commits + 1 unrelated `chore(prompts)` interleaved); the handoff commit will make 44.

## Key reference documents the next session should know about

- **`plugins/a4/references/adr-triggers.md`** *(new)* — single source of truth for ADR-trigger signals (B1–B6 + content-aware upward propagation) and anti-patterns. Cite from any skill whose dialogue or content reads can surface ADR-worthy moments. Five skills currently cite.
- **`plugins/a4/references/frontmatter-schema.md`** — schema doc, now reflects A5's evolution (decision `research:` field, stored-reverse `research.cited_by:` exception, research artifact convention, extended status enum).
- **`plugins/a4/references/pipeline-shapes.md`** — Full / Reverse / Minimal shapes + No-shape state. Companion to adr-triggers via the ADR cross-cutting section.
- **`plugins/a4/scripts/drift_detector.py`** — now carries `ensure_changes_section` pre-pass (A4 auto-fix) and `missing-adr-cite` rule (A1, architecture-only). Snapshot-only; no temporal/git work yet.
- **`plugins/a4/scripts/register_research_citation.py`** *(new)* — atomic four-place writer for research → decision citations.
- **`plugins/a4/agents/task-implementer.md`** — now carries an "Architecture-choice exit" section parallel to the existing spec-ambiguity exit, citing adr-triggers.md.

## Citation convention (preserved)

Same as last session — for any `plugins/a4/` doc:

- Plugin-internal markdown link citations: `${CLAUDE_PLUGIN_ROOT}/<plugin-internal-path>`. No relative `../`.
- Shell commands: `${CLAUDE_PLUGIN_ROOT}/scripts/...`.
- Inline prose to current skill's own files: `${CLAUDE_SKILL_DIR}/references/...`.
- `<project-root>/a4/` workspace docs (user output): Obsidian `[[wikilinks]]` and `![[embeds]]`.

This session's new files (`adr-triggers.md`, `register_research_citation.py`) and all citations to them use `${CLAUDE_PLUGIN_ROOT}/...`.

## How to resume

1. **Pick the next topic.** Three candidates:
   - **#14′** (drift_detector staleness propagation, wiki-wide) — concrete code change. Scope: `## Changes` advance on any wiki → emit `kind: gap` review items targeted at dependent pages (wikilinks + forward-link frontmatter). Plus the temporal-staleness part of A4 ("body changed but `## Changes` didn't follow"). Requires git or mtime infrastructure. Some scope-merge consideration with refresh logic that drift_detector already runs.
   - **CLAUDE.md companion-list extension** — small one-shot. Adds `wiki-authorship.md` / `skill-modes.md` / `iterate-mechanics.md` / `pipeline-shapes.md` / `adr-triggers.md` to the always-read-first list. Decide whether all five belong or only a subset.
   - **`refresh_research_citations.py`** — defer-this-session item. Add a SessionStart back-scan that recomputes research `cited_by:` from decision `research:` lists. Useful if any real-world drift is observed.
   User has not signaled preference; ask.

2. **Discussion-first.** Per session-specific guidance, present options + recommendation, accept user's pick, then execute. Auto mode tends to be on; treat the pick as the trigger to act.

3. **Commit per topic.** Each shipped topic has been its own commit (or commit cluster within one topic). Topic #15′ shipped as 4 commits; smaller topics may ship as 1.

4. **Conflict audit before implementing.** This session's pre-implementation audit caught the A3-redundant-with-existing-infra issue and the A5-schema-departure-from-line-273 issue. Future implementation work should run a similar audit — read the SKILL.md / scripts / schema before writing code, surface conflicts, decide before editing.

## Working tree state

After Topic #15′'s 4 commits and the handoff commit, working tree is clean except for the same pre-existing modification to `plugins/a4/CLAUDE.md` mentioned in the prior handoff (one bullet about "Forward-only relationships" was removed before that session started — not part of any topic, left untouched).

Commits ahead of `origin/main`: 44 (38 prior + 4 this session topic-#15′ commits + 1 unrelated `chore(prompts)` + the handoff commit).

## Session insight worth keeping

This session's most useful pattern: the user repeatedly **dropped or simplified signals** when the cost of detection outweighed the value. A2 went from "frontmatter check" to "content-aware LLM signal" because the frontmatter check had structural false positives (small features, roadmap auto-gen). A3 was dropped because existing infra already covered it. A4 collapsed from a detection rule to an auto-fix. A5 became registration, not detection. Topic #6/#7 lessons (don't mechanically systematize asymmetries) generalized this session into: **don't add detection when the work belongs at the moment of authoring**. Future "we should detect X" conversations should ask first whether X can be prevented at write time (auto-fix or atomic registration), and if not, whether existing infra already detects it.
