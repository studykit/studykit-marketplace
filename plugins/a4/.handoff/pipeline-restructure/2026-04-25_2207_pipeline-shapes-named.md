---
timestamp: 2026-04-25_2207
topic: pipeline-restructure
previous: 2026-04-25_2116_mode-axes-run-seam-iterate-mailbox.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_2207. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Pipeline restructure — Topic #7 shipped (pipeline shapes named) + ADR-trigger surfaced as new Topic #15

## Session context

Continuation of the pipeline-restructure thread from `2026-04-25_2116_mode-axes-run-seam-iterate-mailbox.md`. That session left two backlog items: #7 (brownfield/minimal pipeline 1급 시민화) and #14 (drift_detector staleness propagation). User picked **#7**.

This session walked Topic #7 as a long discussion-first thread. The user pushed back on several mid-design framings, each producing a real correction:

1. The first framing of "brownfield/minimal" conflated two axes — corrected to **project state (greenfield/brownfield)** vs **pipeline shape (Full/Reverse/Minimal)**, with shape being the actual variable that drives skill behavior.
2. The user observed Cases 1 and 2 (brownfield + decision-only vs brownfield + task→run with no wiki) felt the same — corrected by replacing the artificial split with a single determinant: **presence of `bootstrap.md`**. If absent → No shape; if present → one of the three shapes applies.
3. The user pointed out `/a4:decision` is **not** ideation — it produces ADRs, which are first-class pipeline inputs via `task.justified_by:`. Re-categorized as cross-cutting concern, not standalone.
4. The user pointed out ADRs are produced **most heavily during arch authoring**, not as Minimal-shape's primary input. Reframed ADR's place as cross-cutting with explicit production/consumption channels.
5. The user pointed out `/a4:task` models a **Jira issue** — task does not strictly require UC or ADR. `kind=bug` and `kind=spike` are self-contained (bug description / hypothesis as AC). This reduced the citation list from three skills to two.
6. The user asked "when should LLM tell the user an ADR is needed?" — recognized as a separate concern from shape taxonomy. Surfaced as **new Topic #15** (ADR-trigger detection) and deferred.

After the design converged, the work shipped as two commits.

## Topic backlog at session end

| ID | Title | Status |
|---|---|---|
| #1 | Pipeline stage 경계 | completed (session 1) |
| #2 | Wiki authorship 분배 | completed (session 1) |
| #3 | Bootstrap 위치/타이밍 + L&V owner | completed (session 1) |
| #4 | Interactive vs Autonomous skill 짝맞춤 | completed (session 2) |
| #5 | `/a4:run` 내부 seam (implement / integration-test / ship-review) | completed (session 2) |
| #6 | Iteration 모델 통일 | completed (session 2) |
| **#7** | **Brownfield/minimal 파이프라인의 1급 시민화** | **completed this session** |
| #14 | drift_detector staleness propagation | pending |
| **#15 (new)** | **ADR-trigger detection** — LLM 이 "ADR 필요" 자리를 인식하는 정적·대화적 신호 | **pending — surfaced this session** |
| (consideration) | `plugins/a4/CLAUDE.md` always-read-first 리스트 확장 (wiki-authorship / skill-modes / iterate-mechanics / pipeline-shapes 포함 여부) | pending |

User has not signaled which of #14 / #15 / CLAUDE.md to address next; ask.

## What shipped this session

Two commits on `main`:

| SHA | Subject | Topic |
|---|---|---|
| `1e5f784a8` | docs(a4): name pipeline shapes (Full / Reverse / Minimal) as first-class | #7 |
| `1bfa209c4` | docs(a4): cross-reference pipeline-shapes.md from peer reference docs | #7 polish |

`marketplace.json` `a4` version: 1.29.1 → **1.30.0**.

### Topic #7 — pipeline shapes named (`1e5f784a8`)

**Decision.** Brownfield/minimal handling was scattered across three places (compass Step 2.0, auto-bootstrap "Codebase Assessment", task's optional `implements:`/`justified_by:`). The three pipeline shapes a workspace can take were unnamed; Full forward was the implicit default. Extract the taxonomy to a single reference doc; have only the skills that genuinely branch on shape cite it.

**Three shapes (+ No-shape state) named:**

| Shape | Entry skill | Required wiki path | AC source |
|---|---|---|---|
| **Full forward** | `/a4:usecase` | `usecase → domain → architecture → bootstrap → roadmap` | UC's `## Flow`/`## Validation`/`## Error handling` |
| **Reverse** (Reverse-only or Reverse-then-forward) | `/a4:auto-usecase` | depends on sub-variant | UC-derived once forward stages run |
| **Minimal** | `/a4:task` | `bootstrap.md` only | per `kind`: UC `implements:`, ADR `justified_by:`, bug description, or spike hypothesis |
| **No shape** | (none) | `bootstrap.md` absent | n/a — `/a4:decision`, `/a4:research`, `/a4:spark-brainstorm`, manual wiki edits |

**Shape determinant:** presence of `a4/bootstrap.md`. `/a4:run` requires it for Launch & Verify (per existing fallback policy in `plugins/a4/spec/2026-04-25-a4-run-final-fallback-policy`); every shape terminates in `/a4:run` so every shape requires `bootstrap.md`. Absence → No shape.

**ADRs as cross-cutting concern.** ADRs (`/a4:decision` output) are orthogonal to shape:

- *Production primary*: during `/a4:arch` (heavy stack/component/integration choices) — `arch/SKILL.md:216` already nudges users toward `/a4:research` → `/a4:decision`.
- *Production secondary*: standalone `/a4:decision` invocation at any time, any shape, even No-shape.
- *Consumption mandatory*: `architecture.md` `## Changes` footnote `[[decision/N-...]]`; `task.justified_by:` for non-UC `feature` tasks (Minimal-shape canonical path); successor ADR `Status: superseded by ADR-M` chain; other wiki pages' `## Changes` when driven by an ADR.
- *Consumption optional*: task body prose, review item body, research artifact forward-pointers.

ADR trigger conditions documented (multiple viable options + non-trivial trade-off + non-recoverable from code + plausibly-revisitable). Anti-patterns documented (routine choices, framework-mandated, post-hoc justification, multiple decisions per file).

**Citation discipline (key design decision).** Only skills whose behavior **genuinely depends on shape** cite the new reference:

| Skill | Cites? | Reason |
|---|---|---|
| `auto-bootstrap` | yes | Step 1 has two axes: project state (fresh/incremental) AND pipeline shape (Full needs `architecture.md`, Minimal can run without it) |
| `run` | yes | Step 4b ship unit varies — per-UC when `task.implements:` non-empty, per-task when empty; runs can mix both in one cycle |
| `task` | **no** | itself the Minimal-shape entry; always Jira-issue-modeled regardless of other shape activity in workspace |
| `decision` | no | cross-cutting; shape-independent |
| `usecase`, `domain`, `arch`, `roadmap` | no | Full-only stages; shape determined by invocation |
| `auto-usecase` | no | Reverse entry; shape determined by invocation |
| `compass` | yes (entry-routing level) | Step 2.0 catalog cites the ref; not internal-branching cite |

Per Topic #4 / #6 pattern: consolidate, cite from the places that actually need it, do not mechanically add citations everywhere.

**Files touched.**
- New: `plugins/a4/references/pipeline-shapes.md`
- Modified: `plugins/a4/skills/auto-bootstrap/SKILL.md` (Step 1 reorganized into two axes), `plugins/a4/skills/run/SKILL.md` (Step 4b ship-unit branching made explicit), `plugins/a4/skills/compass/SKILL.md` (Step 2.0 reframed in shape vocabulary, No-shape acknowledged as catalog fall-through).

### Topic #7 polish — reciprocal companion-list cross-refs (`1bfa209c4`)

**Decision.** `pipeline-shapes.md` already lists the other peer references as companions. Reciprocate: each peer reference's "Companion to:" header gains a one-line entry for `pipeline-shapes.md`. Discoverability — entering the hierarchy from any node should surface the rest.

**Files touched.**
- `plugins/a4/references/wiki-authorship.md` (companion line extended)
- `plugins/a4/references/skill-modes.md` (companion list +1)
- `plugins/a4/references/iterate-mechanics.md` (companion list +1)

## ADR-trigger detection (Topic #15) — surfaced but deferred

Last design exchange of the session. The user asked: "ADR 을 만들어야 한다고 LLM 이 언제 알려줄 수 있는지?" — when can the LLM (running inside an a4 skill) recognize that an ADR-worthy moment has arrived?

**Two signal classes identified:**

**A. Static / structural signals** (deterministic, code-detectable):
- `architecture.md`'s `## Changes` advanced but no cited `decision/*` (= drift_detector candidate; this overlaps with Topic #14)
- `task.justified_by:` empty for `kind=feature` and `implements:` also empty — already smell-flagged in `/a4:task` Step 2
- `decision/*.md` flipped to `superseded` without a complete supersede chain (partial validate_frontmatter coverage)
- A wiki page substantively edited without `## Changes` updated (drift_detector partial)
- `research/<slug>.md` written but no ADR cites its conclusion (no current hook)

**B. Conversational / semantic signals** (LLM in dialogue):
- Multiple-option enumeration ("A or B", "Postgres or Mongo")
- Trade-off language ("we trade X for Y", "장단점이 있다")
- User uncertainty markers ("not sure", "더 생각해봐야")
- Prior-decision references (signals supersede chain candidate)
- Implementation deferral by `task-implementer` agent
- Architecture-impacting implementation choice surfaced mid-`/a4:run`

**Current state.** Only `/a4:arch:216` carries an explicit ADR-nudge instruction. Other natural-trigger sites (`/a4:usecase`, `/a4:domain`, `/a4:run` task-implementer, `/a4:research-review` conclusion handoff) lack analogous instructions and rely on LLM general intuition.

**Decision for now.** Separate topic (#15) — distinct from Topic #7's "name the shapes" abstraction. Static and conversational signals have different processing mechanisms (script/hook vs SKILL.md instruction) and don't fit under one reference. Not a one-skill change either — at least 5 skills' instructions affected. Treat as Topic #6-scale work when picked up.

**Possible structure for Topic #15** when addressed:
- New `plugins/a4/references/adr-triggers.md` — enumerate signals A and B, link to anti-patterns
- Static signals → integrate into `drift_detector.py` (Topic #14 territory) — emit `kind: gap` review items targeting `decision` when arch advances without ADR cite
- Conversational signals → one-line nudge instruction added to each of `usecase`, `domain`, `arch` (already has, but make uniform), `run` (task-implementer halt path), `research-review` (post-conclusion handoff)
- Anti-patterns documented to limit false positives

## Key reference documents the next session should know about

- **`plugins/a4/references/pipeline-shapes.md`** — single source of truth for Full / Reverse / Minimal shapes + No-shape state. Cite from any skill whose behavior branches on shape; do NOT mechanically cite from skills that don't branch. ADR cross-cutting section names the production/consumption channels.
- **`plugins/a4/references/skill-modes.md`** — interactive/autonomous + forward/reverse axes per skill. Companion to pipeline-shapes (per-skill mode vs per-pipeline shape).
- **`plugins/a4/references/iterate-mechanics.md`** — mailbox protocol shared by every iterate flow. Now lists pipeline-shapes.md as companion.
- **`plugins/a4/references/wiki-authorship.md`** — who can write each wiki page. Companion list now includes pipeline-shapes.md.
- **`plugins/a4/skills/run/SKILL.md`** — Step 4b ship branch is `task.implements:`-driven; per-UC vs per-task ship unit, can mix.
- **`plugins/a4/skills/auto-bootstrap/SKILL.md`** — Step 1 reorganized into two axes (project state, pipeline shape).
- **`plugins/a4/skills/compass/SKILL.md`** — Step 2.0 prompt now in shape vocabulary; No-shape acknowledged as catalog fall-through (no explicit (d) branch).

## Citation convention (preserved)

Same as last session — for any `plugins/a4/` doc:

- Plugin-internal markdown link citations: `${CLAUDE_PLUGIN_ROOT}/<plugin-internal-path>`. No relative `../`.
- Shell commands: `${CLAUDE_PLUGIN_ROOT}/scripts/...` or `${CLAUDE_PLUGIN_ROOT}/hooks/...`.
- Agent system prompts ("shared refs"): `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/...`.
- Inline prose to current skill's own files: `${CLAUDE_SKILL_DIR}/references/...` (existing convention).
- `<project-root>/a4/` workspace docs (user output): Obsidian `[[wikilinks]]` and `![[embeds]]`.

This session's new file (`pipeline-shapes.md`) and the citation edits in compass/auto-bootstrap/run/peer-references all use `${CLAUDE_PLUGIN_ROOT}/...`.

## Things deliberately not done

- **Did not touch `/a4:task` for shape-awareness.** task is itself the Minimal-shape entry — always Jira-issue-modeled, no internal shape branching needed. The user's "task models a Jira issue" correction reinforced this.
- **Did not add `/a4:decision` shape branching.** `/a4:decision` is cross-cutting; same behavior in any shape or No-shape.
- **Did not add a (d) "no pipeline" branch to compass Step 2.0.** No-shape is a *fall-through* via the catalog's Ideation/Standalone sections, not an explicit user-facing fourth choice. Adding (d) would make "no shape" feel like a shape, contradicting the taxonomy.
- **Did not touch `plugins/a4/CLAUDE.md`'s always-read-first list** to add the four peer references. Still cites only `frontmatter-schema.md`. Deferred from last session and again from this session — pending consideration.
- **Did not address Topic #14** (drift_detector staleness propagation). Some overlap with Topic #15's static signals (arch ## Changes vs ADR cite) — a session that picks #14 may want to scope-merge with #15's structural-signal portion.
- **Did not push.** 34 commits ahead of `origin/main` (32 prior + 2 this session). User has not signaled push intent.

## How to resume

1. **Pick the next topic.** Three candidates:
   - **#14** (drift_detector staleness propagation) — concrete code change emitting `kind: gap` review items for downstream wikis when `architecture.md`'s `## Changes` advances. Some overlap with #15's static signals.
   - **#15** (ADR-trigger detection) — newly surfaced. Larger: new `references/adr-triggers.md` + 5 SKILL.md instructions + drift_detector hook for static signals. Could scope-merge with #14.
   - **CLAUDE.md companion-list extension** — small one-shot. Adds `wiki-authorship.md` / `skill-modes.md` / `iterate-mechanics.md` / `pipeline-shapes.md` to the always-read-first list.
   User has not signaled preference; ask.
2. **Discussion-first.** Per session-specific guidance, present options + recommendation, accept user's pick, then execute. Auto mode tends to be on; treat the pick as the trigger to act.
3. **Commit per topic.** Each shipped topic has been its own commit; follow the same cadence.
4. **Citation discipline.** When writing new docs or editing existing ones under `plugins/a4/`, keep `${CLAUDE_PLUGIN_ROOT}/...` for plugin-internal markdown citations.

## Working tree state

After two commits this session and the handoff commit, working tree is clean except for one pre-existing modification to `plugins/a4/CLAUDE.md` (one bullet about "Forward-only relationships" was removed before this session started — not part of this session's work, left untouched).

Commits ahead of `origin/main`: 35 (33 prior + 2 this session topic-#7 commits + the handoff commit).

## Session insight worth keeping

The handoff's most useful pattern across Topics #4, #6, #7: the user repeatedly resists abstractions that **mechanically fill out asymmetries** ("add `/a4:auto-domain` to match `/a4:domain`") and rewards abstractions that **name an asymmetry already in the code** ("name the three shapes that already exist"). Topic #7's design path mirrored this exactly — five rounds of correction that progressively stripped artificial categories (project-state-as-determinant, ideation-includes-decision, AC-must-be-UC-or-ADR, three-skill-citation-list) down to the minimum honest taxonomy. When a future topic feels like "we should systematize X for symmetry," that's a flag to ask: is X actually asymmetric for a reason?
