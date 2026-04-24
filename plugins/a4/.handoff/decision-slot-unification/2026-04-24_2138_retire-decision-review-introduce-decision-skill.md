---
timestamp: 2026-04-24_2138
topic: decision-slot-unification
previous: 2026-04-24_2117_split-spark-decide-into-research-and-review.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_2138. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

Follow-up to the preceding `decision-slot-unification` session (which split the retired `/a4:spark-decide` into `/a4:research` + `/a4:decision-review`). This session challenged the `/a4:decision-review` design itself on two grounds and pivoted the surface.

**User observations that drove the pivot:**

1. The `decision-reviewer` agent's 7 criteria and expected input format (`## Research Findings` section; "Research Balance" / "Rationale Strength" / "Rejection Clarity" criteria) assume a **research-grounded, multi-option, evaluated** decision. It fits ADR-style decisions but mis-fires on simpler conversation-derived decisions (domain-expertise calls, naming/convention choices, team-consensus outcomes, single-option adoptions, obvious answers). Every such decision would always flag `IMBALANCED` on criterion 2 and `WEAK RATIONALE` on criterion 4 despite being perfectly fine. Evidence: `agents/decision-reviewer.md:24` prescribes the input sections; criteria 2/4/5 are body-section-dependent.
2. With `/a4:spark-decide` retired and no skill responsible for *recording* a decision, there was no tool to capture a decision reached through LLM↔user conversation. The user observed the right gap was a **decision documentation** skill, not another review skill.

**Resulting decisions:**

1. **Retire `/a4:decision-review` + `decision-reviewer` agent.** Both deleted wholesale. No deprecation shim. Rationale: the agent's shape is load-bearing research-grounded; adapting it would either mean criteria-skipping hacks (option C, dismissed) or splitting into two agents (option 2, dismissed). User preferred a clean break.
2. **Introduce `/a4:decision` — records a decision reached through conversation into `a4/decision/<id>-<slug>.md`.** Owns what `/a4:spark-decide` used to own in its back half (file write + wiki nudge), but the decision content comes from conversation rather than skill-driven facilitation. Requires an `a4/` workspace.
3. **Introduce `/a4:research-review` + `research-reviewer` agent — reviews research artifacts at `./research/<slug>.md`.** Research is AI-generated (higher error risk) and feeds decisions; review belongs on the research side, not the decision side. Workspace-agnostic (no `a4/` required).
4. **Decisions themselves are not machine-critiqued anymore.** Decision authorship is the user's own thinking; `/a4:decision` only records and nudges, it does not score criteria.

# /a4:decision design (confirmed in conversation)

- **Skill name:** `/a4:decision`.
- **Argument:** optional. Two input modes both supported:
  - (a) No argument → skill extracts the decision from recent conversation context.
  - (b) Short summary / title → used as a seed; content still drawn from conversation.
- **Status transition:** not a binary prompt. Skill interprets natural-language signals from the user (`"we've decided"`, `"확정"`, `"let's go with X"` → `final`; `"let's sit with it"`, `"두고 보자"` → `draft`) and asks once if ambiguous. No mechanical default.
- **Research linkage:** body prose only, as Obsidian `[[research/<slug>]]` wikilinks. **Not** in `related:` frontmatter — research lives outside the `a4/` workspace and is not an issue-family artifact. Skill auto-scans `./research/` for candidates (by slug/topic match) and also accepts user-specified slugs; both behaviors live side-by-side.
- **Workspace requirement:** `a4/` required (unlike `/a4:research` and `/a4:research-review`). Aborts if not a git repo or if `<project-root>/a4/` is missing.
- **Wiki nudge:** performed in Step 6 of the skill — same 5-target matrix as the retired `decision-review` Step 5 (architecture / context / domain / actors / nfr), same review-item fallback on defer. See `references/obsidian-conventions.md §Wiki Update Protocol` for the footnote format.
- **Frontmatter written:** matches `references/frontmatter-schema.md §Decision` unchanged — `id`, `title`, `status`, `decision` one-liner, `supersedes`, `related`, `tags`, `created`, `updated`. No new fields.

# /a4:research-review design

- **Skill:** `/a4:research-review <path>` — takes a path to `./research/<slug>.md` (absolute, relative, or bare slug). Abort with usage hint if empty / unresolvable. If file has `status: final` already, confirm before re-running.
- **Workspace:** does **not** require `a4/`. Resolves against project root if in a git repo, otherwise cwd.
- **Flow:** runs `research-reviewer` agent → walks 6-criterion report with the user one issue at a time → applies accepted revisions via `Edit` → bumps `updated:` → optionally flips `status: draft → final` on user's call. No wiki nudge (research is workspace-agnostic).
- **Agent criteria (6):**
  1. Source Quality — URLs/docs/queries cited; primary sources preferred; currency appropriate to topic.
  2. Option Balance — equal rigor per option (comparative mode only; `N/A` for single mode).
  3. Claim Grounding — every factual claim carries an inline `([ref](<url>))` citation.
  4. Bias Detection — confirmation / anchoring / authority / recency bias; framing-language scan (adjectives like "blazing", "clunky", "modern", "legacy").
  5. Completeness — Context states a specific question; findings actually address it; known unknowns declared.
  6. Decision Neutrality — report describes, does not advocate.
- **Delegation path.** If a finding demands new research (e.g., `IMBALANCED` on a thin option), skill offers to invoke `/a4:research` on that slice rather than patching in-line.

# Rejected alternatives (discussed, not taken)

- **Rename `decision-reviewer` → `research-reviewer` and keep `/a4:decision-review`.** Suggested mid-conversation as option 1 for the research-reviewer reframe. Dismissed because it did not address the *recording* gap — leaving no skill that captures a conversation-derived decision.
- **Split `decision-reviewer` into `research-reviewer` (Research Balance + Bias + Citation) and a slim `decision-reviewer` (Rejection Clarity + Rationale Strength + Reversibility + Actionability).** Dismissed as unnecessary complexity; user wanted one fewer skill, not two.
- **Adaptive `decision-reviewer` (detects research presence and skips research-scoped criteria when absent).** Dismissed in favor of removing the review step for decisions entirely, since decision authorship is user-owned and machine critique was not the gap.
- **Write research links into `related:` frontmatter instead of body wikilinks.** Dismissed. Previous handoff had mentioned `related: [research/<slug>]` as the citation form; this session moved it to **body prose `[[research/<slug>]]` only** because research is not an `a4/` issue and pretending it is in frontmatter confuses the path-reference grammar (which is workspace-rooted).

# What changed (14 files, commit `a410087d2`)

**New skills**
- `plugins/a4/skills/decision/SKILL.md` — `/a4:decision` body. Pre-flight (a4/ required) → extract decision from conversation (argless) or use arg as seed → discover related research (auto-scan + user-specified) → status via natural-language dialog → allocate id + slug → write file with scope-dependent body sections (Context and Decision required; Options Considered / Rejected Alternatives / Next Steps typical) → in-situ wiki nudge → report.
- `plugins/a4/skills/research-review/SKILL.md` — `/a4:research-review` body. Pre-flight → run `research-reviewer` agent → walk 6-criterion findings with user → apply revisions → wrap up (status flip optional).

**New agent**
- `plugins/a4/agents/research-reviewer.md` — 6 criteria (Source Quality, Option Balance, Claim Grounding, Bias Detection, Completeness, Decision Neutrality). Output format mirrors the old decision-reviewer's but re-scoped. Handles `comparative` and `single` modes; skips Option Balance in single mode. Tools: `Read, WebFetch` (may sample a few cited URLs to spot-check claims).

**Deleted**
- `plugins/a4/skills/decision-review/SKILL.md` (and empty parent directory)
- `plugins/a4/agents/decision-reviewer.md`

**Caller updates**
- `skills/spark-brainstorm/SKILL.md` L125-129 — "Handoff to Research and Decision" rewritten: `/a4:research` → optional `/a4:research-review` → conversation → `/a4:decision`.
- `skills/spark-brainstorm/README.md` L84 — plantuml diagram trailing node "research + decision-review" → "research + decision".
- `skills/arch/SKILL.md` L213 — Phase 1 heavy-choice nudge rewritten: `/a4:research` then `/a4:decision` to record the conclusion.
- `skills/compass/SKILL.md` L73 — Ideation catalog: `decision-review` row replaced with two rows for `research-review` and `decision`.
- `skills/research/SKILL.md` L128-129 — Wrapping Up citation guide. Canonical citation form is now body-prose `[[research/<slug>]]` wikilinks from `a4/decision/<id>-<slug>.md`, **not** `related: [research/<slug>]` frontmatter. Note about optional `/a4:research-review` added.
- `skills/research/SKILL.md` L133, L135 — non-goals: references to `/a4:decision-review` → `/a4:decision`.

**Schema + conventions**
- `references/frontmatter-schema.md §Decision` (L194) — prose rewritten to describe the `/a4:decision` recording flow; research citation form clarified as **body wikilinks only** (not `related:`); reviewer pass removed from the description; Section `## Research Findings` removed from the enumerated body sections (it was an artifact of the ADR-style shape, not actually required).
- `references/frontmatter-schema.md` L257 — historical note updated to describe the full arc: spark-decide slot retired → spark-decide skill split into research + decision-review → decision-review retired when the research-grounded assumption surfaced → current shape is research + research-review + decision.
- `references/obsidian-conventions.md` L13 — spark-files historical note updated: decisions now recorded by `/a4:decision` (not hand-authored), research cited via body wikilinks.

**Top-level doc**
- `plugins/a4/README.md` — skills table: `decision-review` row removed; `research-review` and `decision` rows added. Agents table: `decision-reviewer` row replaced with `research-reviewer`. Layout diagram: research citation gloss changed from `related: [research/<slug>]` to `[[research/<slug>]]` wikilinks.

**Version**
- `.claude-plugin/marketplace.json` — a4 plugin `1.5.0 → 1.6.0`.

# Explicitly untouched

- **arch's `a4/research/<label>.md` claim-verification cache.** `arch/SKILL.md:26, 256-259, 291` still describe `a4/research/<label>.md` as the destination for `a4:api-researcher` claim-verification outputs during architecture design. Different convention from the new project-root `./research/<slug>.md`; unchanged from the preceding session. Same coexistence and potential-rename carve-out as before.
- **`plugins/a4/spec/*.decide.md`.** Plugin's own meta-ADRs. Hand-authored. Still not migrated; still explicitly carved out.
- **Agents other than decision-reviewer / research-reviewer.** `api-researcher`, `arch-reviewer`, `usecase-reviewer`, etc. — all untouched. Their descriptions and contracts unchanged.
- **Hooks.** `hooks/record-edited-a4.sh`, `hooks/validate-edited-a4.sh`, etc. unchanged. They scope to `a4/`, so `./research/` files remain outside their scope by design.
- **`scripts/validate_frontmatter.py`.** No code changes. Decision schema unchanged — `decision:` one-liner field was already in the schema, `supersedes:`/`related:`/`tags:` likewise. Body-prose `[[research/<slug>]]` wikilinks are not a frontmatter concern. `./research/` outside `a4/` still outside validator scope.
- **`scripts/validate_body.py`.** No changes. The new required-body-section discipline for `a4/decision/*.md` (Context + Decision minimum) is in the SKILL.md contract, **not** enforced by the body validator.
- **Decision frontmatter schema.** Unchanged from the preceding session's L196-209 table. `/a4:decision` writes files that match this schema exactly.
- **`a4/idea/` skill (`/a4:idea`).** Unchanged. Its non-goals still mention `/a4:spark-brainstorm` and `/a4:research` (no decision-review reference to purge).
- **`scripts/index_refresh.py`.** No changes. The Spark section comment already said "only brainstorm supported"; decision rendering was unaffected by the split.
- **Preceding handoff chain.** `2026-04-24_2033` and `2026-04-24_2117` remain frozen per their DO-NOT-EDIT banners. This new file chains via `previous:`.

# Verification performed

- `uv run plugins/a4/scripts/validate_frontmatter.py <synthetic-workspace>/a4/` on a workspace containing:
  - `a4/decision/1-test-decision.md` — `status: draft`, `decision:` one-liner, body contains `[[research/test-topic]]` wikilink
  - `a4/spark/2026-04-24-1530-test.brainstorm.md` — minimal brainstorm
  Result: `OK — 2 file(s) scanned, no violations.`
- AST parse check on `validate_frontmatter.py`, `index_refresh.py`, `allocate_id.py` — all parse cleanly.
- `grep -rn "decision-review\|decision-reviewer\|decision_review\|decision_reviewer"` across `plugins/a4/` and `.claude-plugin/` (excluding `.handoff/` and `spec/`): only match is the **intentional** historical note at `references/frontmatter-schema.md:257`. All active callers migrated.
- `grep -rn "research-review\|research-reviewer"`: all 15 matches accounted for (README rows, compass catalog, new skill/agent files, schema historical note, research/SKILL.md, spark-brainstorm handoff, decision skill non-goals). No stray references.
- `grep -rn "a4:decision\b"`: all expected — frontmatter-schema, obsidian-conventions, research/SKILL.md non-goals + wrap-up, spark-brainstorm handoff, arch Phase 1 nudge, research-review skill references. None missing.
- Manual read of new `decision/SKILL.md`, `research-review/SKILL.md`, `agents/research-reviewer.md` for self-consistency and for alignment with the schema + conventions docs.
- marketplace.json version bump verified: `a4 version: 1.6.0`.

# Plausible follow-ups (not done; user has not requested)

1. **End-to-end test of `/a4:research-review` on a real research file.** The 6-criterion agent and the skill walk-flow are designed but not exercised. A first real run will reveal whether the verdict vocabulary (`WEAK SOURCES`, `IMBALANCED`, `UNGROUNDED CLAIMS`, etc.) maps cleanly to the Step 2 table in the skill and whether the delegate-back-to-`/a4:research` offer fires at the right moments.

2. **End-to-end test of `/a4:decision`.** Same. The two input modes (argless + summary) and the natural-language status interpretation are untested in practice. Particular risk area: the argless mode's conversation-context extraction. If the session discussed several unrelated decisions, the skill should ask which one to record rather than guessing — this is specified in Step 1 but untested.

3. **No more criteria-based reviewer for decisions at all.** This is a deliberate choice, not a gap. If a future session regrets it and wants a *lightweight* decision sanity pass (e.g., "does the Decision section actually name a choice?", "is there at least one Next Step?"), that would be a new small agent — keep it shape-agnostic, maybe 2-3 criteria, and make it optional from within `/a4:decision`. Not built this session; flag for future judgment.

4. **Body-level validator for `a4/decision/*.md`.** Unchanged carry-over from preceding handoff. `/a4:decision` writes Context + Decision at minimum per SKILL.md contract, but this is not enforced. Low priority until a real drift surfaces.

5. **arch's `a4/research/` vs project-root `./research/` naming.** Same carry-over. Two different shapes under the word "research" in two different locations. If confusion surfaces in practice, the cleanup options are (a) rename arch's `a4/research/<label>.md` to `a4/verification/<label>.md`, or (b) unify both into `./research/`. Deferred until pain.

6. **Legacy `spark/*.decide.md` migration.** Unchanged carry-over. Still deferred on "mechanical and infrequent" rationale.

7. **Does `/a4:decision` auto-move a spark brainstorm's `status` to `promoted`?** Currently no. If the user records a decision whose content was sourced from a specific `spark/<...>.brainstorm.md`, the skill does not write back `promoted: [decision/<id>-<slug>]` to that brainstorm. Not surfaced as pain yet; if it becomes one, add a user-confirmed step at the end of `/a4:decision` Step 7.

# Key files to re-read on the next session

- `plugins/a4/skills/decision/SKILL.md` — authoritative `/a4:decision` contract (pre-flight, extract, research discovery, status dialog, id+slug, write, wiki nudge, report).
- `plugins/a4/skills/research-review/SKILL.md` — `/a4:research-review` flow (pre-flight, agent run, walk findings, apply revisions, wrap up).
- `plugins/a4/agents/research-reviewer.md` — 6-criterion review report contract. This is now the only review-family agent in the a4 plugin.
- `plugins/a4/references/frontmatter-schema.md §Decision` — unchanged schema; rewritten prose describing the `/a4:decision`-recorded flow and body-wikilink citation rule.
- `plugins/a4/references/obsidian-conventions.md §Link syntax` — the `[[research/<slug>]]` wikilink form is the canonical citation in body prose; frontmatter paths still follow the plain-string / no-brackets rule.
- `plugins/a4/README.md` — skills table, agents table, and layout diagram reflect the new state.

# Outstanding parked threads (unrelated to this session)

None newly surfaced. Prior parked items (`a4-redesign`, `experiments-slot`, `idea-slot`, plus the preceding two `decision-slot-unification` handoffs) remain in their own subdirectories and are unaffected by these edits.
