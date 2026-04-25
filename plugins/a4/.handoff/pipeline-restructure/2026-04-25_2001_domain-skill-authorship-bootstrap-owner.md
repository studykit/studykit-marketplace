---
timestamp: 2026-04-25_2001
topic: pipeline-restructure
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_2001. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Pipeline restructure — three Topics shipped: /a4:domain split, wiki authorship policy, bootstrap as L&V owner

## Session context

The user opened the session with `@plugins/a4/` "pipeline stage별 skill 문서를 읽고 어떻게 pipeline을 재구축하면 좋을지 논의" — a discussion-first request to restructure the a4 pipeline. Prior to this session the user had deliberately wiped `plugins/a4/spec/` and `plugins/a4/.handoff/` (commit `5f797c7f2 docs(a4): remove old docs to avoid anchoring`) so we worked from current SKILL.md content rather than past ADRs. There is no `previous:` field on this handoff for that reason — the chain was reset on purpose.

The session enumerated seven restructure topics, then walked them in order. Three were resolved and committed; the remaining four (plus one drift_detector follow-up created mid-session) are listed in the backlog below.

## Topic backlog at session end

Ordered as the user prefers them addressed; numbering matches in-session task IDs.

1. **#1 Pipeline stage 경계** — completed (Topic 1)
2. **#2 Wiki authorship 분배** — completed (Topic 2)
3. **#3 Bootstrap 위치/타이밍 + L&V owner** — completed (Topic 3)
4. **#4 Interactive vs Autonomous skill 짝맞춤** — pending. `auto-bootstrap` has no interactive twin; `auto-usecase` is the brownfield reverse-engineer path. Asymmetry to resolve.
5. **#5 `/a4:run` 내부 seam (implement / integration-test / ship-review)** — pending. `run` does five phases; consider whether ship-review or failure classification should be split out.
6. **#6 Iteration 모델 통일** — pending. Each skill defines its own `iterate` mode reading review items; possible unification.
7. **#7 Brownfield/minimal 파이프라인의 1급 시민화** — pending. The "single change" shortcut (`bootstrap → task → run`) lives only as compass routing today; consider codifying as a first-class shape.
8. **#14 drift_detector staleness propagation** — pending follow-up created during Topic 2. When `architecture.md` is updated, auto-emit `kind: gap` review items targeting downstream wikis (`bootstrap`, `roadmap`, related `task/*.md`) whose `updated:` predates the new arch footnote. The wiki-authorship policy's "How an arch fix flows back downstream" section already cites this rule as planned; the drift_detector code change is the open work.

The TaskList tool is the in-conversation tracker; tasks #1–#16 (including completed sub-tasks for the three shipped topics) are all there for the next session if it wants to resume from the same numbering.

## What shipped this session

Three commits on `main`, in order:

| SHA | Subject | Scope |
|---|---|---|
| `dcab63688` | feat(a4): split /a4:domain skill from /a4:usecase | New skill, new agent, decision table on arch |
| `58ddb609b` | docs(a4): codify wiki authorship + cross-stage feedback policy | New reference doc + inline citations across skills |
| `1acbb0704` | refactor(a4): bootstrap.md is the single source of truth for L&V | Removed duplicate L&V authorship; embed-only on roadmap |

`marketplace.json` `a4` version moved 1.23.0 → 1.24.0 → 1.25.0 → 1.26.0 across these three commits.

### Topic 1 — `/a4:domain` skill split (`dcab63688`)

**Decision.** Cross-cutting Domain Model extraction (Concept Extraction / Relationship Mapping / State Transition Analysis) is its own skill, separate from `/a4:usecase`. Reasoning: per-UC interview and cross-cutting pattern induction are different reasoning modes; bundling them inflated `usecase`'s task list and context.

**Sub-decisions during the discussion:**
- (a) Skill name: `/a4:domain` (over `/a4:domain-model`).
- (b) `/a4:arch` Phase 3 in-situ domain edits: option **b3** — *simple* changes (concept add, 1:1 rename, definition wording) edit `domain.md` inline; *structural* changes (split / merge / relationship / state) emit a review item with `target: domain` and continue using a placeholder term.
- (c) Domain reviewer agent: replace dead `domain-updater` (single-`.usecase.md`-file model jetsam) with new `domain-reviewer` matching the `usecase-reviewer` / `arch-reviewer` / `roadmap-reviewer` per-finding-review-item pattern.

**Files touched.**
- New: `plugins/a4/skills/domain/SKILL.md`, `plugins/a4/agents/domain-reviewer.md`
- Moved: `plugins/a4/skills/usecase/references/domain-model-guide.md` → `plugins/a4/skills/domain/references/domain-model-guide.md`
- Removed: `plugins/a4/agents/domain-updater.md`
- Modified: `plugins/a4/skills/usecase/SKILL.md` (Step 12 deleted, task list slimmed, wrap-up suggests `/a4:domain`), `plugins/a4/skills/usecase/references/session-closing.md`, `plugins/a4/skills/arch/SKILL.md` (Phase 3 b3 decision table), `plugins/a4/skills/arch/README.md` (PlantUML refresh + `.arch.md` / SHA leftovers cleaned), `plugins/a4/skills/compass/SKILL.md` (Step 2.0(c), Step 2.1 catalog, Layer 1 routing, Layer 3 target routing all add `domain`), `plugins/a4/README.md` (Skills + Agents tables).

### Topic 2 — wiki authorship + cross-stage feedback policy (`58ddb609b`)

**Decision.** Codify in one reference doc:
- Authorship table (Option A): each wiki page has one primary-author skill plus a small in-situ allow-list for other skills; everything else flows through review items.
- Cross-stage feedback policy: when a stage discovers a problem in another stage's wiki, decide stop vs continue by **whether this stage's output is valid before the upstream fix**. Strong upstream dependency → stop; weak → continue + review item.

**Stop/continue assignment.**
- **stop**: `roadmap`, `roadmap-reviewer`, `run` Step 4
- **continue + review item**: `auto-bootstrap`, `usecase iterate`, `domain`, `auto-usecase`, `arch iterate`

**Architecture-specific rules.**
- `architecture.md` is single-author (`arch` only); no other skill edits in-situ. Justification: arch is the most depended-on wiki (bootstrap, roadmap, every task, run), so contract drift cost is high.
- Asymmetry with `domain.md` (which allows arch in-situ for simple changes per b3) is intentional — domain is upstream of arch and term churn is normal; architecture is downstream of everyone.

**How arch fixes flow back downstream.** Documented as the cycle: external stage emits `target: architecture` review item → `/a4:arch iterate` resolves it → `architecture.md` gets a `## Changes` footnote → drift_detector emits new `kind: gap` items targeting downstream wikis → compass routes the user to the right `iterate`. The drift_detector staleness-propagation rule is currently planned (backlog item #14), not implemented.

**Composer agent change.** `usecase-composer` no longer writes `domain.md` (description, Section 5, return-summary `wiki_pages_touched` all updated). After `/a4:auto-usecase` or interactive `/a4:usecase`, the next-step suggestion is `/a4:domain`.

**Files touched.**
- New: `plugins/a4/references/wiki-authorship.md` (the authorship + feedback-policy reference)
- Modified: `plugins/a4/agents/usecase-composer.md`, `plugins/a4/skills/{arch,auto-bootstrap,auto-usecase,domain,roadmap,run,usecase}/SKILL.md` (each adds an inline citation at the relevant decision point), `marketplace.json`

### Topic 3 — `bootstrap.md` is the single source of truth for L&V (`1acbb0704`)

**Decision.** `bootstrap.md` owns Launch & Verify: `## Verified Commands`, `## Smoke Scenario`, `## Test Isolation Flags`. `roadmap.md` does not author L&V content — it embeds those bootstrap sections via Obsidian transclusion (`![[bootstrap#Verified Commands]]` etc.). `/a4:run`, `task-implementer`, and `test-runner` read `bootstrap.md` directly; the roadmap embed is for human readers only.

**Sub-decisions during the discussion:**
- (a) Single owner: `bootstrap.md` (Option 1) — it already has every section `run` needs; roadmap was a copy site for historical reasons.
- (b) Embed format: Obsidian standard `![[...]]` transclusion (over wikilinks-with-summary).
- (c) Roadmap template still keeps the `## Launch & Verify` heading, but the body is just the embeds — readers see the commands inline; SoT is bootstrap.

**Run fallback ladder removed.** Previous: roadmap.md → bootstrap.md → compass. Now: `bootstrap.md` required, missing bootstrap → compass. `roadmap.md`'s presence is irrelevant for L&V. `run/SKILL.md` "Launch & Verify Source" section, agent prompts in Step 2 + Step 3, and Out-of-Scope section all updated.

**Roadmap planning-guide auto-detection deleted.** The `## Launch & Verify Derivation` section in `plugins/a4/skills/roadmap/references/planning-guide.md` (~60 lines of app-type detection / build-cmd guessing / isolation-flag tables) was replaced with a redirect to `/a4:auto-bootstrap`. That work belongs in bootstrap, was already verified there, and re-running auto-bootstrap is the canonical update path.

**Reviewer behavior.** `roadmap-reviewer` now flags authored L&V content on `roadmap.md` as `CONFLICT` against the workspace authorship policy. `roadmap.md`'s outputs description in `roadmap/SKILL.md` was updated to remove "Launch & Verify" from the authored-section list.

**Files touched.**
- Modified: `plugins/a4/skills/roadmap/SKILL.md` (Step 1 / Step 3 / hand-off / Non-Goals + template embed), `plugins/a4/skills/roadmap/README.md` (PlantUML note), `plugins/a4/skills/roadmap/references/planning-guide.md` (L&V Derivation replaced), `plugins/a4/skills/run/SKILL.md` (intro / Workspace Layout / Launch & Verify Source / Step 2 prompt / Step 3 prompt / Out-of-Scope), `plugins/a4/skills/auto-bootstrap/SKILL.md` (intro emphasizes single SoT), `plugins/a4/skills/compass/SKILL.md` (router-from-other-skills wording), `plugins/a4/agents/{task-implementer,test-runner,roadmap-reviewer}.md`, `plugins/a4/references/wiki-authorship.md` (bootstrap + roadmap rows strengthened), `marketplace.json`

## Key reference documents the next session should know about

- **`plugins/a4/references/wiki-authorship.md`** — single source of truth for authorship + cross-stage feedback policy. Updates to skill behavior around wiki edits or stop/continue should land here first; SKILL.md citations follow.
- **`plugins/a4/references/frontmatter-schema.md`** — pre-existing; the field-level rules. Unchanged this session but is the companion to wiki-authorship.md.
- **`plugins/a4/CLAUDE.md`** — already requires consulting `references/frontmatter-schema.md` before any a4 work; the wiki-authorship.md rule is now an equal peer for any skill behavior touching wiki pages or cross-stage feedback. CLAUDE.md was not updated this session — consider adding wiki-authorship.md alongside the frontmatter-schema.md mention if it gets cited often.
- **`plugins/a4/skills/domain/SKILL.md`** — new skill; phases 1/2/3 mirror the prior usecase Step 12 but with iteration entry, staleness signal, and explicit collaboration with arch's b3 rules.
- **`plugins/a4/skills/arch/SKILL.md`** Phase 3 — the b3 decision table. Cross-referenced from `domain/SKILL.md` and `wiki-authorship.md`.

## Things deliberately not done

- **Did not edit `plugins/a4/CLAUDE.md`.** `wiki-authorship.md` is consequential enough that it could be added next to `frontmatter-schema.md` in CLAUDE.md's "always read first" list. Left this for the next session to decide — small lift, but worth one-line consideration.
- **Did not implement drift_detector staleness propagation (#14).** Cited as a planned rule in `wiki-authorship.md` §"How an arch fix flows back downstream" and in `roadmap-reviewer.md`'s feedback. Code change deferred.
- **Did not edit `usecase-reviewer` agent.** Section 10 ("Domain Model — Coverage and consistency") still claims domain findings as a usecase-review concern. With `domain-reviewer` now owning that area, the two reviewers will likely deduplicate at runtime via the existing dedup-by-target check, but a future cleanup could trim overlap.
- **Did not touch `arch/README.md`'s old workflow diagram beyond the b3 fixes.** Line 22-27 had `.arch.md` / SHA references; those were updated. The "Iteration Mode" branch and "Wrap Up" branch are now consistent with current SKILL.md but the README is still PlantUML-only and may diverge again.

## How to resume

1. **Pick the next topic.** User indicated they prefer topic-by-topic. The unresolved list is #4, #5, #6, #7, #14. The user has not signaled a preferred next; ask. (#14 is the smallest scope and concrete code; #5 is the next-largest design question after Topic 3.)
2. **Discussion-first.** Per session-specific guidance, the user wants a discussion before code. Surface options + recommendation, accept the user's pick, then act.
3. **Auto mode is on.** When the user agrees to a direction, execute autonomously without further confirmation per topic-internal sub-step.
4. **Commit per topic.** Each shipped topic this session was its own commit with a substantive subject; follow the same cadence rather than rolling multiple topics into one commit.
5. **TaskList.** Tasks #1–#16 (with sub-tasks per topic) are tracked via the in-conversation `TaskCreate` / `TaskUpdate` tools. Re-create them at the start of the next session if the conversation is fresh.

## Working tree state

Clean as of this snapshot. Commits ahead of `origin/main`: 27 (per pre-handoff `git status`). User has not signaled push intent; do not push without instruction.
