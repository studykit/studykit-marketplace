---
timestamp: 2026-04-25_1702
topic: pipeline-restructure
previous: 2026-04-25_1527_carry-forward-link-rule.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_1702. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# pipeline-restructure — checkpoint at 2026-04-25_1702

This session executed the prior handoff's default starting point in full: **(1) backfill ADR for Sub-decision A** (the handoff carry-forward wikilink rule shipped in `9f92bfe7b`) and **(2) Sub-decision B** (ADR `## Next Steps` as implications prose with task wikilinks). Both ADRs are now in `plugins/a4/spec/`. The decision SKILL.md absorbed Sub-decision B's body-structure rule and the a4 plugin version is bumped 1.20.0 → 1.21.0.

After ADR work, this session also created the four on-disk anchors required by the just-shipped wikilink rule, so this handoff itself complies with the rule (no free-text carry-forward) and the transitional period is closed.

## What is committed

Three commits this session, in order:

- `92a901eae` — `feat(a4): require ADR Next Steps as implications prose with task wikilinks`. 4 files, +129 / −1.
  - **New ADR**: [`plugins/a4/spec/2026-04-25-handoff-carry-forward-as-wikilinks.decide.md`](../../spec/2026-04-25-handoff-carry-forward-as-wikilinks.decide.md). Backfill for Sub-decision A. Records the carry-forward wikilink rule (already shipped in `9f92bfe7b`) as a proper plugin meta-ADR. Body covers `## Context` (three-tracker problem), `## Decision` (the rule itself), `## Options Considered` (four alternatives, including the rejected fourth-tracker option), `## Consequences` (bootstrap requirement, handoffs become referential, plugin self-handoff fallback), `## Open Questions` (validator scope/severity, retroactive bootstrap order).
  - **New ADR**: [`plugins/a4/spec/2026-04-25-adr-next-steps-as-implications-prose.decide.md`](../../spec/2026-04-25-adr-next-steps-as-implications-prose.decide.md). Sub-decision B. ADR `## Next Steps` is implications prose with `[[task/<id>-<slug>]]` wikilinks; bullet items describing executable work without a task link are forbidden; section is omitted when there is no follow-on work; plugin meta-ADR fallback uses `[[plugins/a4/spec/<filename>]]`. `## Open Questions` covers validator severity for `## Next Steps` and plugin meta-ADR target shape.
  - **`plugins/a4/skills/decision/SKILL.md` Step 5 §Body structure rules** — adds two bullets: (1) the implications-prose rule for `## Next Steps`, (2) the plugin meta-ADR fallback. The required-section enforcement (`## Context`, `## Decision`) is unchanged.
  - **`.claude-plugin/marketplace.json`** — bumps a4 plugin `1.20.0 → 1.21.0`.

- `4efef8a78` — `docs(a4): add draft-ADR anchors for open pipeline-restructure carry-forwards`. 4 files, +124 / 0. Bootstrap anchors required by the wikilink rule (created mid-`/handoff` so this handoff body can wikilink them):
  - [`plugins/a4/spec/2026-04-25-compass-routing-refresh.decide.md`](../../spec/2026-04-25-compass-routing-refresh.decide.md) — Tier B 7.
  - [`plugins/a4/spec/2026-04-25-a4-arch-generation-pattern.decide.md`](../../spec/2026-04-25-a4-arch-generation-pattern.decide.md) — Tier C 8.
  - [`plugins/a4/spec/2026-04-25-roadmap-reviewer-uc-less-audit.decide.md`](../../spec/2026-04-25-roadmap-reviewer-uc-less-audit.decide.md) — Tier C 11.
  - [`plugins/a4/spec/2026-04-25-a4-run-final-fallback-policy.decide.md`](../../spec/2026-04-25-a4-run-final-fallback-policy.decide.md) — Tier C 12.
  - Each stub has `status: draft`, summarizes the problem in `## Context`, and lists open sub-questions in `## Open Questions`. `## Decision` is left as TBD until the next session decides each.

- (this handoff) — `docs(handoff): snapshot pipeline-restructure session state` (separate commit per `/handoff` skill).

## Why this matters

The prior handoff (2026-04-25_1527) closed Sub-decision A but flagged two pieces of debt:

1. **Process drift.** Sub-decision A shipped a SKILL.md rule + version bump without a covering ADR in `plugins/a4/spec/`, contradicting `plugins/a4/CLAUDE.md` (plugin meta-design decisions are recorded as ADRs).
2. **Three-tracker problem on the ADR side.** Handoff `§Open` was newly disciplined, but ADR `## Next Steps` was still a hand-rolled list and could carry the same drift.

This session resolved both:

- The backfill ADR closes the process drift retroactively. Reading the codebase now reveals the carry-forward rule both as live behavior (in `handoff/SKILL.md`) and as a recorded decision (in `spec/`). The `## Open Questions` on that ADR captures the validator follow-up so it has a permanent home.
- Sub-decision B closes the ADR-side three-tracker gap. Together with Sub-decision A, the rule is now: every "still open" item — whether in a handoff or in an ADR — must point at a tracked artifact (`[[task/...]]`, draft ADR, or `## Open Questions` heading).

After this session, the pipeline-restructure thread's two original "still open" items in Tier C 9 / 10 are both effectively closed:

- **Tier C 9** (`decision` skill `## Next Steps` guardrail) → shipped as Sub-decision B.
- **Tier C 10** ("남은 일" single source) → fully embodied in code on both the handoff side (Sub-decision A) and the ADR side (Sub-decision B). No remaining concrete sub-tasks.

## Self-compliance — this handoff complies in full

The prior handoff was an explicit transitional snapshot allowed to use free-text carry-forward; this handoff is the first under the rule with full compliance required.

To comply, this session created the four draft-ADR anchors in commit `4efef8a78` before drafting the handoff body. Every carry-forward item below points at one of those draft ADRs or at an `## Open Questions` heading on a settled ADR. There is no free-text carry-forward.

Concretely, this means the bootstrap step deferred by the prior handoff is now complete. From this handoff onward, the wikilink rule is fully in force without exception.

## Carry-forward items

### Compass routing refresh (Tier B 7)

`plugins/a4/skills/compass/SKILL.md` Layer 1–4 routing predates `/a4:run` and `/a4:task` and either silently skips them or routes through stale predecessors. Refresh required.

→ [[plugins/a4/spec/2026-04-25-compass-routing-refresh]]

### `/a4:arch` ADR-generation pattern (Tier C 8)

Three candidate patterns: A multi-agent debate, B research-drafter, C passive detector. B+C is the leading combination. Decide and ship.

→ [[plugins/a4/spec/2026-04-25-a4-arch-generation-pattern]]

### `roadmap-reviewer` UC-less audit reframing (Tier C 11)

Reframe the reviewer to walk the workspace as a graph of tasks/decisions/architecture rather than as a UC tree. Largest-scope carry-forward; the natural occasion to introduce `decision.justifies` as a stored reverse-link (which itself needs a sibling ADR per [`2026-04-25-stored-reverse-links.decide.md`](../../spec/2026-04-25-stored-reverse-links.decide.md)).

→ [[plugins/a4/spec/2026-04-25-roadmap-reviewer-uc-less-audit]]

### `/a4:run` final-fallback policy (Tier C 12)

Define behavior when neither `roadmap.md` nor `bootstrap.md` exists in the user-project a4/ workspace. Leading candidate: offer to run `/a4:bootstrap`.

→ [[plugins/a4/spec/2026-04-25-a4-run-final-fallback-policy]]

### Validator follow-up to the carry-forward rule

Should a validator scan handoff bodies for non-wikilinked carry-forward? Where does it live (`validate_body.py` extension vs. new `validate_handoff.py`)? Hard error or soft warning?

→ [[plugins/a4/spec/2026-04-25-handoff-carry-forward-as-wikilinks#Open Questions]]

### Validator follow-up to ADR `## Next Steps`

Should a validator extension to `validate_body.py` flag `## Next Steps` lines lacking a `[[task/...]]` wikilink on `draft → final`? Severity?

→ [[plugins/a4/spec/2026-04-25-adr-next-steps-as-implications-prose#Open Questions]]

## Where to start the next session

**Default suggestion: pick the smallest of the four Tier draft ADRs and ship it.** Tier C 12 (`/a4:run` final fallback) is likely the smallest — the candidate set is enumerated and the leading option ("offer `/a4:bootstrap`") is already obvious. Promote the draft ADR to `final` after the implementation lands.

Alternatives in rough priority order (each is the cheapest path inside its scope):

- **Tier C 8** — `/a4:arch` generation pattern. Confirm B+C, pin the detector signal set for C, ship `/a4:arch` as a working skill.
- **Tier B 7** — compass routing refresh. May be a SKILL.md edit only, no full ADR finalization needed.
- **Tier C 11** — `roadmap-reviewer` UC-less reframing. Largest scope but highest leverage; pulls in `decision.justifies` as a sibling stored-reverse-link ADR.
- **Validator follow-ups** — either the handoff validator or the ADR `## Next Steps` validator. Lower priority than the four Tier items because the SKILL.md rules already block the bad behavior at the model level.

In all cases, finalizing a draft ADR uses `transition_status.py` per `decision/SKILL.md` Step 6 — but note that these are plugin meta-ADRs in `plugins/a4/spec/`, which are date-slugged rather than id-numbered, and the user-project `transition_status.py` does not apply to them. Plugin meta-ADRs at `status: draft` transition to `status: final` by direct edit (within the working-tree-edit + commit discipline of `plugins/a4/spec/`); confirm the operating procedure with the user before the first such transition.

## Hook surface today (unchanged)

`plugins/a4/hooks/hooks.json` declares four events: PostToolUse / Stop / SessionStart (two — bash sweep + Python session-start) / SessionEnd (bash cleanup only — no Python entry). The dispatcher's subcommand set is `post-edit | stop | session-start`. Unchanged this session.

## Files to inspect first

- [`plugins/a4/spec/2026-04-25-handoff-carry-forward-as-wikilinks.decide.md`](../../spec/2026-04-25-handoff-carry-forward-as-wikilinks.decide.md) — backfill ADR for the carry-forward wikilink rule. Read this before writing any handoff in this thread.
- [`plugins/a4/spec/2026-04-25-adr-next-steps-as-implications-prose.decide.md`](../../spec/2026-04-25-adr-next-steps-as-implications-prose.decide.md) — Sub-decision B. Read before writing any new ADR with executable follow-on work.
- `plugins/a4/skills/decision/SKILL.md` Step 5 "Body structure rules" — where Sub-decision B's two new bullets live.
- `plugins/a4/skills/handoff/SKILL.md` Task §4 "Carry-forward items" — unchanged this session, but still the live source of truth for the carry-forward rule.
- The four new draft ADRs (Tier B 7, C 8, C 11, C 12) listed under §Carry-forward items above. Each has `status: draft` and `## Decision: TBD` — the next session's main work is moving each through the `draft → final` transition.
- `.claude-plugin/marketplace.json` — current a4 plugin version is 1.21.0. Bump again on the next behavior change.
- [`plugins/a4/spec/2026-04-25-stored-reverse-links.decide.md`](../../spec/2026-04-25-stored-reverse-links.decide.md) — still the active gate for any new stored reverse-link field. Tier C 11 will need a sibling ADR if `decision.justifies` lands.

## Don'ts (refreshed)

- **Don't ship a plugin meta-design change without a covering ADR in `plugins/a4/spec/`.** This session backfilled Sub-decision A's missing ADR — do not re-introduce the same drift.
- **Don't write free-text carry-forward in handoffs.** The transitional period closed with this handoff. From now on, every carry-forward must be a wikilink to an on-disk tracker (or an `## Open Questions` heading on a settled ADR). Create the anchor before writing the carry-forward.
- **Don't write `## Next Steps` items in ADRs without `[[task/<id>-<slug>]]` wikilinks** (or, for plugin meta-ADRs, without the analogous on-disk anchor). Empty or placeholder `## Next Steps` sections are forbidden.
- Don't add a new stored reverse-link field (e.g., `decision.justifies`) without a covering ADR per [`2026-04-25-stored-reverse-links.decide.md`](../../spec/2026-04-25-stored-reverse-links.decide.md) §Decision.
- Don't edit any file under `plugins/a4/spec/archive/` or `plugins/a4/.handoff/**` — both are immutable. Supersession of an archived ADR is recorded by writing a new ADR in `spec/`. Handoff revisions are recorded by writing a new handoff.
- Don't move ADRs back from `archive/` to `spec/` without a reason. The split is decided: `spec/` = active, `archive/` = frozen.
- Don't update prior-handoff references in `plugins/a4/.handoff/**` to point at `archive/` — handoffs are point-in-time snapshots; broken paths inside them are the expected aging behavior.
- Don't reintroduce `default_mode:` or `mode_transitions:` frontmatter on any SKILL.md.
- Don't reintroduce `scripts/workflow_mode.py` or any session state file under `a4/.workflow-state/`.
- Don't merge `/a4:roadmap` and `/a4:run` back together.
- Don't `rm -rf a4` from the studykit-plugins root — case-insensitive macOS match wipes tracked content.
- Don't write Tier C 10's "single source" as a new file format or directory. The picture uses only existing schema positions (`a4/decision/*.md` at `status: draft`, ADR `## Open Questions`, `a4/task/*.md`, handoff `§Open` as mirror via the new wikilink rule).
