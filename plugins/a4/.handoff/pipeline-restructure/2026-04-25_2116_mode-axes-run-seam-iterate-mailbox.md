---
timestamp: 2026-04-25_2116
topic: pipeline-restructure
previous: 2026-04-25_2001_domain-skill-authorship-bootstrap-owner.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_2116. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Pipeline restructure — Topics #4 / #5 / #6 shipped, plus plugin-internal citation cleanup

## Session context

Continuation of the pipeline-restructure thread from `2026-04-25_2001_domain-skill-authorship-bootstrap-owner.md`. That session left five topics open: #4 (interactive vs autonomous skill pairing), #5 (`/a4:run` internal seam), #6 (iteration model unification), #7 (brownfield/minimal pipeline 1급 시민화), and #14 (drift_detector staleness propagation).

This session walked Topics #4 → #5 → #6 in order, each as a discussion-first conversation followed by an autonomous-mode shipment. After Topic #6, the user raised a side-question about whether `${CLAUDE_PLUGIN_ROOT}` env-var citations should replace relative-path markdown citations across the plugin; that became a fourth shipped change.

Topics #7 and #14 remain pending as of session end. Auto mode was on throughout.

## Topic backlog at session end

| ID | Title | Status |
|---|---|---|
| #1 | Pipeline stage 경계 | completed (prior session) |
| #2 | Wiki authorship 분배 | completed (prior session) |
| #3 | Bootstrap 위치/타이밍 + L&V owner | completed (prior session) |
| **#4** | **Interactive vs Autonomous skill 짝맞춤** | **completed this session** |
| **#5** | **`/a4:run` 내부 seam (implement / integration-test / ship-review)** | **completed this session** |
| **#6** | **Iteration 모델 통일** | **completed this session** |
| #7 | Brownfield/minimal 파이프라인의 1급 시민화 | pending |
| #14 | drift_detector staleness propagation | pending |

User has not signaled which of #7 / #14 to address next; ask. (#14 is the smallest scope and concrete code; #7 is a larger pipeline-shape design discussion.)

## What shipped this session

Four commits on `main`, in order:

| SHA | Subject | Topic |
|---|---|---|
| `674210a21` | docs(a4): codify skill-mode taxonomy as intentional asymmetry | #4 |
| `e7e548c1c` | refactor(a4): reframe /a4:run as loop body + user-driven post-loop review | #5 |
| `e6abc83c8` | refactor(a4): extract shared iterate mechanics into one reference | #6 |
| `a665a92dd` | docs(a4): unify plugin-internal markdown citations on \${CLAUDE_PLUGIN_ROOT} | citation cleanup |

`marketplace.json` `a4` version: 1.26.0 → 1.27.0 → 1.28.0 → 1.29.0 → 1.29.1.

### Topic #4 — skill-mode taxonomy (`674210a21`)

**Decision.** The asymmetry between interactive and autonomous skills is intentional, not a gap to fill. Each pipeline stage's mode is determined by the nature of its work, not by template completeness. Codified the rationale in a new reference doc rather than mechanically adding missing pairs.

**Two-axis framing.** A skill is shaped by two independent axes:
- **Mode** — interactive (Socratic dialogue) vs autonomous (decide-and-act)
- **Direction** — forward (build new from upstream wiki) vs reverse / batch (extract from raw input or code)

The `/a4:auto-*` prefix is *not* a guarantee that a skill is the autonomous twin of an interactive `/a4:*` at the same stage. `auto-usecase` is the reverse / batch entry (codebase / idea → UCs); `auto-bootstrap` is true autonomy because verification work doesn't benefit from dialogue.

**Per-stage mode (codified):**
| Stage | Mode | Direction | Why |
|---|---|---|---|
| `usecase` | interactive | forward | Socratic discovery |
| `auto-usecase` | autonomous | reverse / batch | extract from raw input — distinct job |
| `domain`, `arch`, `roadmap` | interactive | forward | decision collaboration |
| `auto-bootstrap` | autonomous | forward | pure verification |
| `run` | autonomous | forward | loop execution |

**What was deliberately NOT added:** `/a4:auto-domain`, `/a4:auto-arch`, `/a4:auto-roadmap`, interactive `/a4:bootstrap`, interactive `/a4:run`. Reasons documented in `references/skill-modes.md` "Why missing pairs are intentional."

**Files touched.**
- New: `plugins/a4/references/skill-modes.md`
- Modified: `plugins/a4/skills/auto-usecase/SKILL.md` (description + intro repositioned as reverse/batch entry — explicitly **not** the autonomous twin of `/a4:usecase`), `plugins/a4/skills/compass/SKILL.md` (Pipeline (autonomous) catalog row + cite to skill-modes.md), `plugins/a4/README.md` (auto-usecase row), `plugins/a4/references/wiki-authorship.md` (companion list).

### Topic #5 — `/a4:run` reframed as loop body + post-loop review (`e7e548c1c`)

**Decision.** What looked like five phases is really two seams: an **autonomous loop body** (Steps 1–3: pick → implement → test, up to 3 cycles) and a **user-driven post-loop review** (Step 4) with two mutually-exclusive branches (4a failure path / 4b ship path). No new skill split, no agent classifier.

**Why no agent in post-loop review.** The user pushed back on the initial "delegate to a `run-failure-classifier` / `uc-ship-reviewer` agent" recommendation, pointing out that user-in-the-loop is simpler. Honest re-analysis confirmed:
- Adding agents → new files (.md), new output schema contracts, new confidence thresholds, new failure modes (misclassify → infinite loop), calibration burden.
- Time saved per `/a4:run` invocation: ~1.5 min (3 classifications × 30s) vs ~5 min for ship verdict prep.
- Ship is forward-path terminal — `shipped → implementing` is disallowed — so `transition_status.py --to shipped` must stay user-authorized regardless of agent involvement.
- ROI: poor.

**What changed in run/SKILL.md:**
- Description rewritten as "two stages: autonomous loop body, then user-driven post-loop review."
- Old Step 4 (failure classify) and Step 5 (ship review) merged into a single **Step 4: Post-loop Review** with subsections **4a. Failure path** and **4b. Ship path**.
- Routing details (cascade rules, cycle counter, transitions) extracted to `skills/run/references/failure-classification.md`.
- Per-UC verdict template, defer protocol, and writer call extracted to `skills/run/references/uc-ship-review.md`.
- Non-Goals strengthened with one more line: "Do not split post-loop review (Step 4) into a separate skill, and do not delegate failure classification or UC ship to an agent."
- Stale "Step 5" / "five phases" references swept across the file (Workspace Layout, Mode Detection, Commit Points, Out of Scope, Wrap Up).

**Files touched.**
- New: `plugins/a4/skills/run/references/failure-classification.md`, `plugins/a4/skills/run/references/uc-ship-review.md`
- Modified: `plugins/a4/skills/run/SKILL.md` (intro, Step 4 merge, Non-Goals, internal Step refs)

### Topic #6 — shared iterate mechanics (`e6abc83c8`)

**Decision.** Extract the truly-shared mechanics of iterate flows into one reference doc; keep stage-specific work inline in each SKILL.md. Not full unification (which would force-fit different work shapes into a single procedure), not the do-nothing option (which leaves real mechanics duplication).

**The mailbox metaphor.** During the discussion, the user observed: *"iterate mode 형식 절차가 mail box 처리하는 거와 비슷하네."* That metaphor was right and concise enough to embed in the new reference's intro:

> Treat each skill's iterate mode as a stage-specific mailbox: filter the inbox to messages addressed to this stage, open the priority queue, mark a message in-progress when you start, archive (resolve / discard) when done. The mechanics here are the mailbox protocol; per-stage SKILL.md sections describe what each *kind* of message actually requires you to do when you read it.

**What's shared (mailbox protocol — moved to the new reference):**
1. Filter the review backlog to this stage's mailbox (per-stage filter table provided).
2. Present as a priority-ordered backlog (priority H→M→L, then `created:`).
3. `transition_status.py --to in-progress / resolved / discarded` writer-call patterns.
4. Footnote markers + `## Changes` entry rules (citing `obsidian-conventions.md`).
5. Discipline (never hand-edit `status:`, never renumber, never delete review files).

**What's stage-specific (left inline in each SKILL.md):**
- `usecase` — unreflected research/exploration check, revising-UC scope
- `domain` — concept ↔ relationships ↔ state impact rule, staleness signals
- `arch` — UC ↔ actor/domain drift, stack ↔ component ↔ flow ↔ contract impact rule
- `roadmap` — scoped roadmap-reviewer single re-run after revision, cascade awareness
- `run` — cycle counter, depends_on cascade reset, crash hygiene, stop-on-strong-upstream

**Files touched.**
- New: `plugins/a4/references/iterate-mechanics.md`
- Modified: `plugins/a4/skills/{arch,domain,roadmap,run,usecase}/SKILL.md` (Iteration Entry sections slimmed; mechanics replaced with citations to the new doc), `plugins/a4/skills/usecase/references/iteration-entry.md` (also slimmed: shared mechanics replaced with citations, only revising-UC scope / research check / work-surface summary / allowed activities remain).

### Plugin-internal markdown citation cleanup (`a665a92dd`)

**Decision.** Use `${CLAUDE_PLUGIN_ROOT}/<plugin-internal-path>` for plugin-internal markdown citations across all `plugins/a4/` docs, not relative `../` paths.

**Why.** Initial recommendation in this session leaned toward relative paths to keep clickable links. The user corrected the framing: **Obsidian is for the user-project `<project-root>/a4/` workspace, not for plugin sources.** Plugin docs are read by GitHub / IDE; clickability through GitHub is the only real loss, and that's outweighed by:
- Depth-independence (`../../../` vs `../../` mistakes go away)
- Greppability (one pattern per cited doc, no per-location variants)
- Alignment with agent prompts that already use `${CLAUDE_PLUGIN_ROOT}/...` for plugin-internal paths
- Stability under file moves

**Implementation.** A throwaway Python script walked `plugins/a4/**/*.md` (excluding `.handoff/`, `archive/`, `spec/`) and substituted markdown link URLs of the form `(<...>../<basename>)` to `(${CLAUDE_PLUGIN_ROOT}/<plugin-internal-path>)` for the well-known target docs:

```
wiki-authorship.md       → references/wiki-authorship.md
frontmatter-schema.md    → references/frontmatter-schema.md
obsidian-conventions.md  → references/obsidian-conventions.md
obsidian-dataview.md     → references/obsidian-dataview.md
hook-conventions.md      → references/hook-conventions.md
skill-modes.md           → references/skill-modes.md
iterate-mechanics.md     → references/iterate-mechanics.md
failure-classification.md → skills/run/references/failure-classification.md
uc-ship-review.md        → skills/run/references/uc-ship-review.md
iteration-entry.md       → skills/usecase/references/iteration-entry.md
```

Plus one one-off: `[`skills/arch/SKILL.md`](../skills/arch/SKILL.md)` in `wiki-authorship.md` → `${CLAUDE_PLUGIN_ROOT}/skills/arch/SKILL.md`.

**`${CLAUDE_SKILL_DIR}` was deliberately not changed.** It's a separate convention used in inline prose (not markdown link form) for *the current skill's own directory*, e.g., `${CLAUDE_SKILL_DIR}/references/abstraction-guard.md` inside `usecase/SKILL.md`. Other studykit plugins use this same pattern. It's correct as-is — different concern from the markdown-link cleanup.

**Result.** 19 files, 51 substitutions, zero remaining relative-path markdown citations under `plugins/a4/` (verified by grep).

**Files touched.** All under `plugins/a4/`: `references/{wiki-authorship,frontmatter-schema,obsidian-conventions,obsidian-dataview,skill-modes,iterate-mechanics}.md`, `agents/usecase-composer.md`, `skills/{arch,auto-bootstrap,auto-usecase,compass,domain,roadmap,run,usecase}/SKILL.md`, `skills/roadmap/references/planning-guide.md`, `skills/run/references/failure-classification.md`, `skills/usecase/references/iteration-entry.md`. Plus `marketplace.json` version bump.

## Key reference documents the next session should know about

- **`plugins/a4/references/skill-modes.md`** — single source of truth for the interactive/autonomous + forward/reverse axes and why missing pairs are intentional. Cite this when changing skill mode behavior; do *not* mechanically add missing pairs.
- **`plugins/a4/references/iterate-mechanics.md`** — the mailbox protocol shared by every iterate flow. Filter, presentation, writer calls, footnote rules, discipline. Cite this from any SKILL.md "Iteration Entry" section; only stage-specific work belongs inline.
- **`plugins/a4/references/wiki-authorship.md`** — companion list now also includes `skill-modes.md`. Three "always read first" companion docs in the references hierarchy: `frontmatter-schema.md` (field-level), `obsidian-conventions.md` (body-level), `wiki-authorship.md` (who-can-write). The new `skill-modes.md` is the fourth peer.
- **`plugins/a4/skills/run/references/failure-classification.md`** — routing table (task/arch/UC) for `/a4:run` Step 4a. Cycle bound logic.
- **`plugins/a4/skills/run/references/uc-ship-review.md`** — verdict template, candidate selection, defer protocol, writer call for `/a4:run` Step 4b.
- **`plugins/a4/skills/run/SKILL.md`** — now reads as "loop body (Steps 1–3) → post-loop review (Step 4)" with Non-Goals explicitly forbidding split or agent delegation of Step 4.

## Citation convention (newly established this session)

When writing or editing any plugin-internal doc under `plugins/a4/`:

- **Shell commands** (`uv run`, `bash`, hooks.json `command:` fields): always `${CLAUDE_PLUGIN_ROOT}/scripts/...` or `${CLAUDE_PLUGIN_ROOT}/hooks/...`.
- **Agent system prompts ("shared refs" lists)**: always `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/...` (agent has env at spawn time; Read resolves it).
- **Markdown link citations across plugin-internal docs** (`[name](path)`): always `${CLAUDE_PLUGIN_ROOT}/<plugin-internal-path>`. No relative `../` form.
- **Inline prose references to the current skill's own files**: keep `${CLAUDE_SKILL_DIR}/references/...` (existing convention; not in markdown-link form).
- **`<project-root>/a4/` workspace docs (user output)**: continue to use Obsidian `[[wikilinks]]` and `![[embeds]]`. The plugin-internal convention here does NOT apply to user-output workspaces.

## Things deliberately not done

- **Did not edit `plugins/a4/CLAUDE.md`.** Top-level `CLAUDE.md` still cites only `frontmatter-schema.md`. Three new high-traffic references (`wiki-authorship.md`, `skill-modes.md`, `iterate-mechanics.md`) could be added as peer companions to it, but the lift was not in scope this session. Worth a one-line consideration next session: should the "always-read-first" list grow?
- **Did not implement Topic #14 drift_detector staleness propagation.** Still cited as planned in `wiki-authorship.md` §"How an arch fix flows back downstream" and in agent feedback. Code change deferred.
- **Did not address Topic #7 brownfield 1급 시민화.** Still pending.
- **Did not touch `${CLAUDE_SKILL_DIR}` references.** Verified across other studykit plugins (`structurizr`, `d2`, `workbench/jenkins-cli`, `workbench/loco-manager`) that this is a real, widely-used convention for the current skill's directory; left alone.
- **Did not split `/a4:run` Step 5 into `/a4:ship`.** This was Option A in the Topic #5 discussion. Cost-benefit (transient state persistence + extra invocation ceremony vs. user time saved) was unfavorable; Non-Goals now codifies "do not split."
- **Did not add an autonomous twin for `domain` / `arch` / `roadmap` or interactive twin for `bootstrap` / `run`.** Topic #4 codified these as intentional gaps, not omissions.
- **Did not commit any extra docs cleanup beyond what each topic's commit covered.** No CLAUDE.md edits, no README extension.

## How to resume

1. **Pick the next topic.** Two pending: #7 (brownfield/minimal pipeline as a first-class shape — currently lives only in compass routing) and #14 (drift_detector staleness propagation — code change to emit `kind: gap` review items targeting downstream wikis when `architecture.md`'s `## Changes` advances). User has not signaled preference; ask.
2. **Discussion-first.** Per session-specific guidance, present options + recommendation, accept user's pick, then execute. Auto mode tends to be on; treat the pick as the trigger to act.
3. **Commit per topic.** Each shipped topic this session was its own commit with a substantive subject; follow the same cadence.
4. **TaskList.** This session created tasks #1–#5 in TaskCreate corresponding to backlog #4–#7 + #14. After this handoff the live TaskList is:
   - #1 — completed (#4)
   - #2 — completed (#5)
   - #3 — completed (#6)
   - #4 — pending (#7 brownfield)
   - #5 — pending (#14 drift_detector)
   The numeric mapping was not strict; if next session starts fresh, just re-create from this handoff's backlog table.
5. **Citation discipline.** When writing new docs or editing existing ones under `plugins/a4/`, use `${CLAUDE_PLUGIN_ROOT}/...` for plugin-internal markdown citations. The session's last commit (`a665a92dd`) re-baselined the whole plugin to that convention — preserve it.

## Working tree state

Clean as of this snapshot. Commits ahead of `origin/main`: 32 (including this session's 4 commits + the prior session's 27 + last session's handoff commit). User has not signaled push intent; do not push without instruction.
