---
timestamp: 2026-04-25_1804
topic: pipeline-restructure
previous: 2026-04-25_1702_adr-next-steps-and-backfill-shipped.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_1804. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# pipeline-restructure — checkpoint at 2026-04-25_1804

This session shipped both **Tier B 7** (compass routing refresh) and **Tier C 12** (`/a4:run` final-fallback policy) end-to-end — ADR finalized and skill SKILL.md edits applied — and ran a full pipeline inventory pass that surfaced four new follow-up gaps. Both Tier items are now closed; the four new gaps are tracked as draft-ADR anchors and carried forward.

The session arc (Q1: "Tier C 12은 뭐야?" → inventory pass → ADR + SKILL.md edits → handoff) followed the prior handoff's "default suggestion" (start with the smallest of the four pending Tier draft ADRs). It did not stop at Tier C 12: when the conversation revealed that `/a4:context` and `/a4:domain` skills do not exist (only `/a4:usecase` produces those wiki pages, as a side effect), the user requested a full pipeline review, which became this session's main work and reshaped both the Tier B 7 and Tier C 12 ADRs.

## What is committed

Three commits this session:

- `aa9e3df46` — `feat(a4): refresh compass routing for /a4:run, /a4:task, brownfield`. 3 files, +116 / −15.
  - **ADR finalized**: [`plugins/a4/spec/2026-04-25-compass-routing-refresh.decide.md`](../../spec/2026-04-25-compass-routing-refresh.decide.md). `status: draft → final`. Decision body specifies three surgical inserts. Open Questions reduced to two (test surface, brownfield-decision persistence — both deferred). Original Q1 ("do `/a4:context` / `/a4:domain` / `/a4:arch` support reverse-engineering?") removed because the inventory pass closed it: `/a4:auto-usecase` already treats source-code paths as a first-class input.
  - **`plugins/a4/skills/compass/SKILL.md` edited** with the three inserts:
    1. New "Inter-skill entry" subsection (placed above Step 0). Documents that other a4 skills can call compass as a fallback router via the `from=<skill>; missing=<files>` argument shape. The first concrete caller is `/a4:run` (see Tier C 12 below).
    2. New Step 2.0 "Brownfield detection" (placed before the catalog at Step 2.1). Detects build manifests / tracked source files outside `a4/` and asks one question — reverse-engineer / single-change / new-feature — routing to `/a4:auto-usecase`, `/a4:auto-bootstrap`, or the catalog respectively. Reverse-engineer leverages `/a4:auto-usecase` Step 2b code-analysis subagent; no new skill is introduced.
    3. Step 3.3 Layer 1 gains a `bootstrap.md`-missing check between the `architecture.md` and `roadmap.md` checks, and a header note that the layer walks pipeline order in strict prefix.
  - **`.claude-plugin/marketplace.json`** — bumps a4 plugin `1.21.0 → 1.22.0`.

- `59e1d1586` — `feat(a4): /a4:run delegates to compass when launch & verify source is absent`. 3 files, +58 / −15.
  - **ADR finalized**: [`plugins/a4/spec/2026-04-25-a4-run-final-fallback-policy.decide.md`](../../spec/2026-04-25-a4-run-final-fallback-policy.decide.md). `status: draft → final`. Decision: when `/a4:run` cannot resolve a Launch & Verify source, halt and delegate to `/a4:compass` via the inter-skill entry contract from the just-finalized Tier B 7 ADR. `/a4:run` does not implement its own fallback ladder; compass's Step 3 Gap Diagnosis (with the new bootstrap-aware Layer 1) walks the pipeline backward and recommends the deepest missing artifact's owning skill. Three Open Questions retained (argument shape evolution, transitive halt-and-delegate chains, `/a4:roadmap` adopting the same pattern).
  - **`plugins/a4/skills/run/SKILL.md` edited**: Launch & Verify Source §3 changed from "Halt and tell the user to run `/a4:auto-bootstrap`" to a `Skill({ skill: "a4:compass", args: "from=run; missing=roadmap.md,bootstrap.md" })` call. Out of Scope §1 reworded — the "no roadmap, no bootstrap" item is no longer unresolved; only "auto-detect commands from package.json / AGENTS.md" remains out of scope.
  - **`.claude-plugin/marketplace.json`** — bumps a4 plugin `1.22.0 → 1.23.0`.

- `d11d665f3` — `docs(a4): add draft-ADR anchors for pipeline-restructure inventory gaps`. 4 files, +129 / 0. Bootstrap anchors required by the wikilink rule (created mid-`/handoff` so this handoff body can wikilink them):
  - [`plugins/a4/spec/2026-04-25-compass-catalog-consistency-audit.decide.md`](../../spec/2026-04-25-compass-catalog-consistency-audit.decide.md) — gap #2.
  - [`plugins/a4/spec/2026-04-25-auto-bootstrap-stepwise-greenfield-vs-incremental.decide.md`](../../spec/2026-04-25-auto-bootstrap-stepwise-greenfield-vs-incremental.decide.md) — gap #4.
  - [`plugins/a4/spec/2026-04-25-run-uc-ship-review-strictness.decide.md`](../../spec/2026-04-25-run-uc-ship-review-strictness.decide.md) — gap #5.
  - [`plugins/a4/spec/2026-04-25-usecase-vs-auto-usecase-selection-criteria.decide.md`](../../spec/2026-04-25-usecase-vs-auto-usecase-selection-criteria.decide.md) — gap #6.
  - Each stub has `status: draft`, summarizes the problem in `## Context`, lists open sub-questions in `## Open Questions`, and leaves `## Decision: TBD` until the next session decides each.

- (this handoff) — `docs(handoff): snapshot pipeline-restructure session state` (separate commit per `/handoff` skill).

## Why this matters

The prior handoff (2026-04-25_1702) flagged four pending Tier draft ADRs and two validator follow-ups. This session intended to start with the smallest (Tier C 12) but discovered, during routine context-gathering, that the prior plan was built on an incorrect assumption: it spoke of `/a4:context` / `/a4:domain` as if they were skills, when in fact those wiki pages are produced as side effects of `/a4:usecase` (interactive) and `/a4:auto-usecase` (autonomous). That single observation cascaded:

1. **Tier B 7's brownfield branch needed re-routing.** The original draft of the compass ADR routed reverse-engineer to a non-existent `/a4:context`. The user requested a pipeline-wide review, which produced an inventory of all 18 skills (call/data-flow graph + 6 detected gaps). The inventory revealed that `/a4:auto-usecase` already accepts source-code paths as first-class input (Step 1 input classification, Step 2b code-analysis subagent, `## Source: code — <path>` attribution category). So Tier B 7's reverse-engineer path collapsed to a single existing-skill route — no new skill required, no sibling ADR needed.

2. **Tier C 12 found its general answer.** Once Tier B 7's inter-skill entry contract was finalized — compass as canonical fallback router — Tier C 12's Decision became a one-liner: `/a4:run` halts and delegates. The earlier "offer to run `/a4:bootstrap`" candidate was rejected as insufficient, because it only works when `architecture.md` exists; the pipeline-walk via compass handles every prefix-missing case, including brownfield via Step 2.0.

3. **Four new follow-up gaps surfaced.** The inventory pass found six total gaps; two coincided with already-shipped work, four are new (carry-forward items below).

After this session, the two Tier items that motivated the prior handoff (Tier B 7 and Tier C 12) are both **closed and shipped**. The remaining pre-existing carry-forwards from the 1702 handoff are **Tier C 8** (`/a4:arch` generation pattern), **Tier C 11** (`roadmap-reviewer` UC-less audit), and the two **validator follow-ups** — none touched this session.

## Self-compliance — this handoff complies in full

This handoff is the second under the carry-forward wikilink rule (per [[plugins/a4/spec/2026-04-25-handoff-carry-forward-as-wikilinks]]) with full compliance required. Every carry-forward item below points at an on-disk draft ADR or `## Open Questions` heading on a settled ADR. There is no free-text carry-forward.

The four bootstrap draft ADRs (commit `d11d665f3`) were created mid-`/handoff` so this handoff body can wikilink them. The two pre-existing Tier carry-forwards (Tier C 8, Tier C 11) reuse anchors created in the prior session. The two validator follow-ups reuse `## Open Questions` headings on the settled ADRs from the prior session.

## Carry-forward items

### Compass Step 2.1 catalog consistency audit (new — gap #2)

`compass/SKILL.md` Step 2.1 catalog tables (Ideation / Pipeline interactive / Pipeline autonomous / Standalone) may be partially out of date relative to the actual skill set under `plugins/a4/skills/`. Audit needed; categorization may need rethinking after the Tier B 7 brownfield branch shifts the catalog's role.

→ [[plugins/a4/spec/2026-04-25-compass-catalog-consistency-audit]]

### auto-bootstrap stepwise greenfield vs incremental contract (new — gap #4)

`auto-bootstrap/SKILL.md` declares the binary mode in Steps 0–1, but Steps 2–5 do not consistently spell out per-mode behavior. Incremental mode against an existing project may need to skip / refuse / nudge various actions; the SKILL.md does not say which.

→ [[plugins/a4/spec/2026-04-25-auto-bootstrap-stepwise-greenfield-vs-incremental]]

### `/a4:run` UC ship-review candidate strictness (new — gap #5)

`run/SKILL.md` Step 5 requires "every task with `implements: [usecase/X]` … has `status: complete`" for X to enter ship-review candidacy. Ambiguous whether this is intentional all-or-nothing (correct under "shipped means the running system reflects this UC end-to-end") or an oversight that prevents partial-shipping. Also: tasks added mid-implementation, failing tasks blocking ship, multi-cycle ship windows.

→ [[plugins/a4/spec/2026-04-25-run-uc-ship-review-strictness]]

### `/a4:usecase` vs `/a4:auto-usecase` selection criteria (new — gap #6)

For greenfield (no existing code) workspaces, compass Step 2.1 presents both `/a4:usecase` (interactive Socratic interview) and `/a4:auto-usecase` (autonomous generation) without a selection rule. The inventory pass's brownfield-routing logic resolved the code-bearing case (route to `auto-usecase`), but the greenfield case remains user-instinct only.

→ [[plugins/a4/spec/2026-04-25-usecase-vs-auto-usecase-selection-criteria]]

### `/a4:arch` ADR-generation pattern (Tier C 8 — pre-existing)

Three candidate patterns: A multi-agent debate, B research-drafter, C passive detector. B+C is the leading combination. Decide and ship.

→ [[plugins/a4/spec/2026-04-25-a4-arch-generation-pattern]]

### `roadmap-reviewer` UC-less audit reframing (Tier C 11 — pre-existing)

Reframe the reviewer to walk the workspace as a graph of tasks/decisions/architecture rather than as a UC tree. Largest-scope carry-forward; the natural occasion to introduce `decision.justifies` as a stored reverse-link (which itself needs a sibling ADR per [[plugins/a4/spec/2026-04-25-stored-reverse-links]] §Decision).

→ [[plugins/a4/spec/2026-04-25-roadmap-reviewer-uc-less-audit]]

### Validator follow-up to the carry-forward rule (pre-existing)

Should a validator scan handoff bodies for non-wikilinked carry-forward? Where does it live (`validate_body.py` extension vs. new `validate_handoff.py`)? Hard error or soft warning?

→ [[plugins/a4/spec/2026-04-25-handoff-carry-forward-as-wikilinks#Open Questions]]

### Validator follow-up to ADR `## Next Steps` (pre-existing)

Should a validator extension to `validate_body.py` flag `## Next Steps` lines lacking a `[[task/...]]` wikilink on `draft → final`? Severity?

→ [[plugins/a4/spec/2026-04-25-adr-next-steps-as-implications-prose#Open Questions]]

## Pipeline inventory — non-obvious facts the next session should know

These were established by reading every SKILL.md under `plugins/a4/skills/` this session. They are not encoded anywhere as a single document, but they shape every routing decision:

1. **`/a4:context` and `/a4:domain` are not skills.** The wiki pages `context.md`, `actors.md`, `domain.md`, `nfr.md` are produced as side effects of `/a4:usecase` (Step 1 / Discovery Loop / Step 11 / Step 12) and the `/a4:auto-usecase` composer subagent. There is no standalone "create context.md" skill. Routing must account for this.

2. **`/a4:auto-usecase` is brownfield-aware.** Argument can be an idea, a brainstorm file, **a source-code path**, or a mix. Step 1 classifies the input; Step 2b spawns a `general-purpose` code-analysis subagent that writes `a4/research/code-analysis-initial.md`; the composer reads that report and produces UCs with `## Source: code — <path>` attribution. Existing UCs trigger expansion mode automatically.

3. **`/a4:auto-bootstrap` is the only skill with an explicit incremental (brownfield) mode** — declared in Step 0 by `bootstrap.md` presence and in Step 1 by codebase assessment. Per-step behavior under incremental mode is not consistently spelled out (see gap #4).

4. **The pipeline order is `usecase → domain → architecture → bootstrap → roadmap → tasks/run`**, in strict prefix. Compass Step 3.3 Layer 1 walks this order to find the deepest missing artifact. `/a4:run` halts and delegates to compass when neither `roadmap.md` nor `bootstrap.md` exists; it does not look upstream itself.

5. **Inter-skill entry contract.** Skills that halt on missing preconditions delegate to `/a4:compass` via the Skill tool with arg `from=<skill>; missing=<comma-separated files>`. This is the canonical fallback-router shape established by Tier B 7 and adopted by Tier C 12. `/a4:roadmap` (currently halts with a recommendation) is the next likely adopter; not in scope yet.

6. **wiki-page wikilink-only fields.** `wiki_impact:` on review items uses bare wiki basenames (`[architecture]`, `[domain]`); body wikilinks use Obsidian style `[[architecture]]`. Plugin meta-ADRs in `plugins/a4/spec/` use `[[plugins/a4/spec/<filename>]]` for cross-references (per [[plugins/a4/spec/2026-04-25-adr-next-steps-as-implications-prose]] plugin meta-ADR fallback rule).

## Where to start the next session

**Default suggestion: pick the smallest of the seven open carry-forwards.** Among the four newly-anchored gaps, **gap #5 (UC ship-review strictness)** is the smallest by far — it is a clarification, not a redesign. Likely outcome: confirm that the all-or-nothing reading is intentional, add one sentence to `run/SKILL.md` Step 5 making it explicit, and transition the draft ADR to `final`. Total work is probably one commit.

Alternatives in rough priority order (each is the cheapest path inside its scope):

- **Gap #2** — compass catalog consistency audit. SKILL.md edit only; no implementation work. Walk `ls plugins/a4/skills/` and reconcile.
- **Gap #6** — `/a4:usecase` vs `/a4:auto-usecase` selection criteria. May be a one-paragraph addition to compass Step 2.1 catalog plus a "When to pick" sentence in each skill's description.
- **Gap #4** — auto-bootstrap stepwise contracts. Larger, requires re-reading auto-bootstrap end-to-end and adding per-step mode notes. Could be folded with **Tier C 8** if the user is touching `auto-bootstrap` and `/a4:arch` together.
- **Tier C 8** — `/a4:arch` generation pattern. Confirm B+C, pin the detector signal set for C, ship `/a4:arch` as a working skill.
- **Tier C 11** — `roadmap-reviewer` UC-less reframing. Largest scope but highest leverage.
- **Validator follow-ups** — either the handoff validator or the ADR `## Next Steps` validator. Lower priority than the seven scoped items because the SKILL.md rules already block the bad behavior at the model level.

In all cases, finalizing a draft ADR uses direct edit (plugin meta-ADRs are not managed by `transition_status.py`); confirm the operating procedure with the user before the first such transition this session.

## Hook surface today (unchanged)

`plugins/a4/hooks/hooks.json` declares four events: PostToolUse / Stop / SessionStart (two — bash sweep + Python session-start) / SessionEnd (bash cleanup only — no Python entry). The dispatcher's subcommand set is `post-edit | stop | session-start`. Unchanged this session.

## Files to inspect first

- [`plugins/a4/spec/2026-04-25-compass-routing-refresh.decide.md`](../../spec/2026-04-25-compass-routing-refresh.decide.md) — Tier B 7 final ADR. Read this before touching `compass/SKILL.md` or designing any other skill's halt-and-delegate flow.
- [`plugins/a4/spec/2026-04-25-a4-run-final-fallback-policy.decide.md`](../../spec/2026-04-25-a4-run-final-fallback-policy.decide.md) — Tier C 12 final ADR. The first concrete caller of the inter-skill entry contract.
- `plugins/a4/skills/compass/SKILL.md` — three new sections (Inter-skill entry subsection above Step 0; Step 2.0 brownfield branch; Step 3.3 Layer 1 bootstrap check).
- `plugins/a4/skills/run/SKILL.md` "Launch & Verify Source" §3 and "Out of Scope" §1 — both updated.
- The four new draft ADRs (gaps #2, #4, #5, #6) listed under §Carry-forward items above. Each has `status: draft` and `## Decision: TBD` — the next session's main work is moving each through the `draft → final` transition.
- `.claude-plugin/marketplace.json` — current a4 plugin version is 1.23.0. Bump again on the next behavior change.
- [`plugins/a4/spec/2026-04-25-adr-next-steps-as-implications-prose.decide.md`](../../spec/2026-04-25-adr-next-steps-as-implications-prose.decide.md) — Sub-decision B from the prior session. Read before writing any new ADR with executable follow-on work.

## Don'ts (refreshed)

- **Don't route to `/a4:context` or `/a4:domain` as if they were skills.** They are not. Wiki pages flow from `/a4:usecase` (interactive) or `/a4:auto-usecase` (autonomous). The earlier draft of the Tier B 7 ADR did this; it is fixed in commit `aa9e3df46`.
- **Don't reimplement the pipeline-walk in `/a4:run`** (or any other halting skill). Delegate to `/a4:compass` with `from=<skill>; missing=<files>`. Two implementations would drift.
- **Don't auto-chain into compass's recommendation.** Compass presents and asks; the user confirms before the upstream skill is invoked. `/a4:run` does not chain itself into the recommended skill.
- **Don't write free-text carry-forward in handoffs.** Every carry-forward must be a wikilink to an on-disk tracker (or an `## Open Questions` heading on a settled ADR). Create the anchor before writing the carry-forward (this session created four).
- **Don't write `## Next Steps` items in ADRs without `[[task/<id>-<slug>]]` wikilinks** (or, for plugin meta-ADRs, the analogous on-disk anchor — sibling ADR by file path, `## Open Questions` heading, or SKILL.md edit named by file path). Empty or placeholder `## Next Steps` sections are forbidden.
- **Don't ship a plugin meta-design change without a covering ADR in `plugins/a4/spec/`.** The covering ADR for this session's compass/run edits is the two finalized ADRs above.
- Don't add a new stored reverse-link field (e.g., `decision.justifies`) without a covering ADR per [[plugins/a4/spec/2026-04-25-stored-reverse-links]] §Decision.
- Don't edit any file under `plugins/a4/spec/archive/` or `plugins/a4/.handoff/**` — both are immutable. Supersession of an archived ADR is recorded by writing a new ADR in `spec/`. Handoff revisions are recorded by writing a new handoff.
- Don't update prior-handoff references in `plugins/a4/.handoff/**` to point at `archive/` — handoffs are point-in-time snapshots; broken paths inside them are the expected aging behavior.
- Don't reintroduce `default_mode:` or `mode_transitions:` frontmatter on any SKILL.md.
- Don't reintroduce `scripts/workflow_mode.py` or any session state file under `a4/.workflow-state/`.
- Don't merge `/a4:roadmap` and `/a4:run` back together.
- Don't `rm -rf a4` from the studykit-plugins root — case-insensitive macOS match wipes tracked content.
