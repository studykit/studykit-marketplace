---
timestamp: 2026-04-24_2231
topic: decision-slot-unification
previous: 2026-04-24_2213_status-consistency-validator-and-hooks.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_2231. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

Direct continuation of the `decision-slot-unification` thread. The preceding handoff (`2026-04-24_2213`) surveyed status enum writers across all six issue families, identified seven values with no mechanical writer, and delivered a read-only consistency validator covering three of them (`decision.superseded`, `idea.promoted`, `brainstorm.promoted`) on the theory the rest would also need either writers or reporting.

Mid-session the user sharpened the ground rule:

> **"사용자가 파일을 수동으로 편집하는 경우는 없음. 항상 LLM을 이용하여 수정."**

With "manual user edit" eliminated as a valid writer category, four of the seven remaining gaps became unacceptable rather than deferred:

- `usecase.implementing` — no writer at all.
- `usecase.done` — no writer at all.
- `idea.discarded` — no writer at all.
- `brainstorm.discarded` — no writer at all.

Plus the three already handled by the consistency validator (but without active writers):

- `decision.superseded` — still derived, no writer (validator-only surface).
- `idea.promoted` — user-driven via downstream skill (left as is).
- `brainstorm.promoted` — same (left as is).

This session assigned concrete writers to the four unacceptable gaps. The user gave a design hint on `usecase.*`:

> **"implementing은 실제 코드 작업하는 LLM이 바꾸는게 맞고. done은 기능이 정상으로 돌아갔는지 확인 하는 LLM이 review후 사용자 confirm을 받고 수정하는."**

That shaped the placement: `implementing` belongs on `task-implementer` (the coding agent), `done` belongs on a post-test-pass review with mandatory user confirmation. Not on the orchestrating skill by mechanical sweep.

# What got built (6 files, commit `ad5b3b0f8`)

## `usecase.implementing` — `task-implementer` writes it

`plugins/a4/agents/task-implementer.md` gained a new step 1: "Transition the implementing UCs." Before beginning any implementation work, the agent reads each UC in its `implements:` frontmatter and flips `status: draft → implementing` + bumps `updated:`. Already-`implementing`, `done`, or `blocked` UCs are left alone.

Rules section was tightened by **removing** the blanket prohibition on editing UC files (it previously read: "Do not modify other task files, plan.md, architecture.md, UC files, domain files, or review items"). Replaced with a targeted carve-out: UC files may be edited **only** for the `status: draft → implementing` flip and the paired `updated:` bump; every other UC field still belongs to `/a4:usecase` / `usecase-reviser`. The commit step was also updated to roll UC status flips into the same task-level commit.

Design rationale for placing this on the agent rather than on `/a4:plan`: the user explicitly wanted the coding LLM to be the transition subject ("실제 코드 작업하는 LLM이 바꾸는게 맞고"). That keeps the "work started" signal co-located with the actor doing the work, not with the orchestrator. Parallel task-implementer spawns still each do their own flip; because the flip is idempotent (`draft → implementing`, skip otherwise), races are fine.

## `usecase.done` — `/a4:plan` Step 2.5 writes it, user confirms

New Step 2.5 added to `plugins/a4/skills/plan/SKILL.md` between Step 2.4 (Analyze Results) and wrap-up. It runs only when 2.4 hits the happy branch (all tests passed, all tasks `complete`). Plan:

1. **Collect candidates.** A UC X qualifies when: X.status is `implementing`, every task with `implements: [usecase/X]` is `complete`, and no review item with `target: usecase/X` is `open`/`in-progress`. Empty candidate set → skip to wrap-up.

2. **Review each candidate** inline (no new agent spawned). The plan skill reads the UC + its implementing tasks' `## Log` + the test-runner return summary, composes a 2-4 sentence verdict identifying: which task(s) implemented it, which tests exercise its Flow/Validation/Error paths, any Expected Outcome item not visibly covered.

3. **Present to user** per candidate: "UC X is ready to mark done... [verdict]. Mark done?" Accept natural-language confirmations (yes/ok/맞아요/확정) / defers (not yet / 아직 / hold) / negatives (no — X is incomplete because ... → creates a fresh review item `kind: gap, target: usecase/X`).

4. **Apply confirmations** — edit UC frontmatter `status: implementing → done`, bump `updated:`, append `## Log` entry: `<date> — marked done after Phase 2 (cycle <N>); tests <list>; user confirmed.`

5. **Commit** all confirmed UC done-transitions in a single commit, separate from task commits. Added a new bullet under "Commit Points": message prefix `docs(a4): mark UC <ids> done`.

Leftover `implementing` UCs (user deferred) stay `implementing` across sessions; the next `/a4:plan iterate` re-offers them.

Deliberately **not** done via a new agent — the plan skill already has the full context (tasks, tests, UCs, review items) without spawning. Adding a `uc-verifier` agent was considered and skipped as unnecessary surface area.

## `idea.discarded` — `/a4:idea discard <id-or-slug> [reason]`

`plugins/a4/skills/idea/SKILL.md` extended with a second mode, dispatched by the first token of `$ARGUMENTS`:

- First token is the literal `discard` → discard mode.
- Otherwise → original capture mode.

Discard mode (steps D1–D4):

- **D1. Resolve**: accepts numeric id (`12`), folder-prefixed path (`idea/12-foo`), or slug fragment (substring of existing idea basenames). Exactly-one-match rule; multiple matches → prompt user to pick; zero → abort with a hint to `ls a4/idea/`.
- **D2. Status check**: only `open` is discardable here. `promoted` is explicitly refused ("discarding a promoted idea is ambiguous; edit by hand if you truly want to reverse that"). Already `discarded` → no-op report.
- **D3. Apply**: frontmatter `status: open → discarded`, `updated:` today. If trailing tokens remain after the target, they are the reason — appended verbatim under a `## Why discarded` body section (new section if absent, date-prefixed line appended if present).
- **D4. Report** the path and whether a reason was recorded. No commit (matches capture mode's non-commit stance).

Frontmatter was also updated: `description` mentions both modes, `argument-hint` is now `<one-line idea> | discard <id-or-slug> [reason]`, `allowed-tools` extended to include `Edit` and `Glob`.

Alternative rejected mid-design: a separate `/a4:idea-discard` skill. Folded into `/a4:idea` to keep "one mental entry point per artifact" — the user already has `/a4:idea` loaded for captures, so toggling to discard via first-token dispatch is lower friction than learning a sibling command.

## `brainstorm.discarded` — `/a4:spark-brainstorm` wrap-up Step 4

`plugins/a4/skills/spark-brainstorm/SKILL.md` Wrapping Up section expanded from 6 steps to 7 by inserting a new Step 4 between "draft summary" and "ask save location":

**Step 4. Decide status.** Interprets natural-language signals from the session's close to pick between `open` (default — may be revisited) and `discarded` (buried). Signals for discard: `"접자"`, `"없던 일로"`, `"그냥 두자"`, `"discard"`, `"drop this"`, `"buried"`, `"not worth it"`. Ambiguous → ask once: "Close as `open` (we may return to these ideas) or `discarded` (these ideas are buried)?"

**`promoted` is deliberately NOT written at wrap-up.** Rationale: `promoted` means an idea from the brainstorm actually became a downstream artifact. That's a distinct act tied to running `/a4:decision` / `/a4:usecase` / etc., not to closing the brainstorm. If the user already produced a decision during the brainstorm, the instruction is to run `/a4:decision` first and then edit `promoted:` by hand. Keeping `promoted` off this skill's writer list avoids the "closed as promoted but no target artifact exists" failure mode.

Step 6 (write file) and Step 7 (report path) renumbered, with Step 7 now explicitly mentioning the recorded status in the final report ("Saved as `status: discarded` — no further action.").

## Docs: `§Status writers` table

`plugins/a4/references/frontmatter-schema.md` gained a new §Status writers subsection right after §Relationships are forward-only. It opens with:

> `a4/` files are always written by an LLM via a skill or agent — never hand-edited by the user.

That statement captures the user's ground rule directly in the canonical schema doc — future contributors reading the schema see the invariant explicitly, not scattered across session handoffs.

Then a per-value table listing the writer for every enum value across all six families. Three values are documented as "derived — no writer; surfaced by `validate_status_consistency.py`": `decision.superseded`, and by extension drift alerts on `idea.promoted` / `brainstorm.promoted`. Two values (`idea.promoted`, `brainstorm.promoted`) are marked "user-driven via downstream skill" to be explicit that they remain writer-less by design.

## Version

`.claude-plugin/marketplace.json` — a4 `1.7.0 → 1.8.0`.

# Rejected alternatives (discussed, not taken)

- **`/a4:plan` orchestrator writes `usecase.implementing` on task-implementer spawn.** This was my first proposal. User redirected to "the coding LLM itself should flip it." Plan-orchestrator writing would be a bigger change (Step 2.2 pre-flight) and would diverge from the intent of "work started" — the orchestrator decides to spawn, but the agent is the entity actually starting.
- **Mechanical sweep writes `usecase.done` without user confirm.** Rejected by user at design ("review후 사용자 confirm을 받고"). The done transition has reversibility and user-judgment stakes (does the feature actually work in practice, not just in tests?) that a sweep cannot resolve.
- **New `uc-verifier` agent for Step 2.5.** Considered as a "cleaner separation of concerns." Rejected on the ground that the plan skill already has all the needed context in scope at that step. Adding an agent would require re-passing UC paths, task logs, test summaries — duplication without benefit.
- **Separate `/a4:idea-discard` skill.** Considered for CLI purity. Rejected — discard is semantically part of the idea lifecycle and the skill is already user-triggered, so folding discard into `/a4:idea` via first-token dispatch gives one entry point per artifact.
- **Write `brainstorm.promoted` at wrap-up from natural-language signals** (symmetric to `discarded`). Rejected because `promoted` carries a cross-file invariant (non-empty `promoted:` list pointing at an actual pipeline artifact). Writing `promoted` without a target file would immediately fail the consistency validator. Keep writing `promoted` tied to the downstream skill that produces the target.
- **Extend `/a4:compass` to sweep old `open` ideas / brainstorms and offer discard.** Mentioned as a future route. Not done this session — scope was gap closure, not proactive housekeeping. Left as plausible follow-up.

# Verification performed

- Read each edited file after editing; confirmed text intent matches design.
- Ran `validate_status_consistency.py` on a synthetic fixture to confirm no regression (the validator is unchanged by this session — the writer assignments don't touch its logic).
- `.claude-plugin/marketplace.json` JSON parse valid.
- No code changes to scripts/hooks in this session — all changes are in agent/skill markdown + schema doc + version bump. No AST parses or unit tests to run.

**Not verified** (deferred): end-to-end exercise of the new `/a4:plan` Step 2.5 in a real workspace. The step's interplay with multi-UC candidate sets and the user-confirm dialogue is designed but untested.

# Explicitly untouched

- **`validate_status_consistency.py`** — unchanged. Its rule coverage (three values) and two-mode shape stay as the preceding handoff documented.
- **Hooks** (`report-status-consistency-*.sh`, `validate-edited-a4.sh`, etc.) — unchanged. Writer assignments affect skill/agent behavior but not hook-level detection.
- **`/a4:idea` promotion path.** The capture→promoted transition for ideas is still user-driven (open the file, set `promoted:`, flip status). This session added `discard` but not `promote`. Reason: promotion targets are known only when the downstream artifact is created, and baking that into `/a4:idea` would duplicate what `/a4:decision`/`/a4:usecase` already do. If this becomes painful, the right fix is a confirmation prompt at the END of those downstream skills.
- **`/a4:spark-brainstorm promote`.** Same reasoning.
- **`decision.superseded` writer.** Still none. Consistency validator surfaces the drift; the user accepted that shape in the preceding handoff. Adding a writer would require auto-mutation, explicitly rejected.
- **`task.*` writers, `review.*` writers, `usecase.blocked`, `usecase.draft`.** All already had writers per the preceding handoff's survey; this session did not revisit them.

# Design notes for future sessions

- **Ground rule at the top of the schema doc.** The new §Status writers section opens with "`a4/` files are always written by an LLM via a skill or agent — never hand-edited by the user." Treat that sentence as load-bearing: every future status value added to an enum MUST have an assigned writer before landing. The consistency validator is a drift-detection safety net, not a substitute for assignment.
- **`task-implementer` UC edit carve-out is narrow by design.** Only `status: draft → implementing` and the paired `updated:` bump. Broadening this (e.g., letting the agent adjust UC Flow based on implementation learnings) would violate the "one writer per field family" invariant and conflict with `/a4:usecase`. Don't relax the rule without a dedicated design round.
- **UC done-review is per-UC and user-confirmed, not batched.** Step 2.5 walks candidates one at a time so the user can defer per-UC. Batching into a single yes/no would lose the ability to defer individual UCs while confirming others.
- **`promoted` is deliberately never written by wrap-up skills.** Writing `promoted` without a corresponding target artifact triggers the consistency validator's `empty-promoted-list-*` rule. If a future session wants to write `promoted` automatically, it MUST do so from the downstream skill at the moment the target artifact is actually created — not at the source side's close.
- **First-token dispatch in `/a4:idea`.** Precedent for other skills: if a skill needs a secondary verb, parse the first whitespace-delimited token and dispatch, rather than creating a sibling skill. Keep arguments free-form otherwise.

# Plausible follow-ups (not done; user has not requested)

1. **End-to-end test of `/a4:plan` Step 2.5.** Untested in a real workspace. Risk areas: (a) user-confirm dialogue repeated N times for an N-candidate set could be tedious — consider a single "here are N candidates, confirm which" flow if pain surfaces; (b) the "no open review items targeting this UC" precondition might be too strict in cases where an unrelated cosmetic review happens to target the same UC — judge case-by-case.

2. **End-to-end test of `task-implementer`'s new step 1.** The narrow-carve-out wording relies on the agent honoring "only flip status, don't touch other fields." A misinterpretation would corrupt UC files. First real run should be watched.

3. **`/a4:idea discard` collision on ambiguous slug fragment.** The "multiple matches → prompt user to pick" path is designed but untested. If the idea folder grows, slug fragments will collide more often; may warrant a fuzzy-ranking UI.

4. **Brainstorm wrap-up `promoted` gap.** Today the only way a brainstorm gets `promoted` is user hand-edit — which was just ruled out as "never." This creates a latent inconsistency: once an idea from a brainstorm graduates via `/a4:decision`, the brainstorm's `status` and `promoted:` remain `open`/`[]`. The preceding handoff flagged this (follow-up #8). The right fix is a confirmation step at the END of `/a4:decision` (and siblings) asking "is this decision sourced from spark/<...>? Update its `promoted:` + `status`?" Not built this session.

5. **`idea.promoted` symmetric gap.** Same shape as #4. Same fix — a confirmation at the end of downstream skills. Same "not built" status.

6. **`/a4:compass` stale-open-item sweep.** A periodic "you have N ideas open since date X; discard any?" prompt would reduce `open`-status accumulation. Out of scope this session but a natural fit for compass's sweep-and-recommend role.

7. **Consistency-validator extension for the two writer-less `promoted` values.** The validator already catches `status=promoted, promoted:[]` and `status!=promoted, promoted:[...]` mismatches. What it does NOT catch: the case where a decision was produced from a brainstorm without updating either the `status` or the `promoted:` list on the brainstorm (both empty, consistent with each other, but wrong relative to world state). Catching this requires cross-file reasoning between decisions and their source brainstorms, which isn't currently in the validator's scope. Deferred until a pattern of actual drift surfaces.

8. **Writer assignment for the three review-target sink statuses** (`in-progress`, `dismissed`). The preceding handoff survey found writers for these (iterate flows, reviser) but described them tersely. A dedicated review pass to confirm every iterate skill actually does write these correctly would close the verification gap. Low urgency — they are working in practice.

# Key files to re-read on the next session

- `plugins/a4/agents/task-implementer.md` — new step 1 + tightened rules. The only place where UC status is flipped to `implementing`.
- `plugins/a4/skills/plan/SKILL.md` §Step 2.5 — UC done-review flow, user-confirm dialogue, new commit point.
- `plugins/a4/skills/idea/SKILL.md` §Discard mode — D1-D4, failure modes.
- `plugins/a4/skills/spark-brainstorm/SKILL.md` §Wrapping Up — inserted Step 4.
- `plugins/a4/references/frontmatter-schema.md §Status writers` — canonical writer table + ground-rule statement. Any future status enum change MUST update this table.

# Outstanding parked threads (unrelated to this session)

- `decision-slot-unification` — this thread continues. Four preceding handoffs (`2026-04-24_2033`, `2026-04-24_2117`, `2026-04-24_2138`, `2026-04-24_2213`) plus this one. The consistency-validator + writer-assignment arc is now closed for the four gap values; the two `promoted` writer-less cases remain parked per design (see follow-ups #4, #5, #7).
- `a4-redesign`, `experiments-slot`, `idea-slot` — unaffected.
