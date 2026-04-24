---
timestamp: 2026-04-25_0122
topic: uc-status-transition-system
previous: 2026-04-25_0028_unify-transitions-add-revising-discarded.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_0122. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

Continuation of the `uc-status-transition-system` thread. The preceding handoff (`2026-04-25_0028`) closed out the unified-writer migration for usecase / task / review and left four plausible follow-ups parked. This session executed follow-up #4 from that list: **migrate the decision family into `transition_status.py`**, retiring the last remaining hook-driven status writer (`propagate_superseded.py` + `propagate-superseded.sh`).

Scope for this session was deliberately narrow — decision family only. No `idea.promoted` / `brainstorm.promoted` work (follow-up #5 from the prior handoff, discussed first in this session but deferred). No `SessionStart` hook for `refresh_implemented_by.py`, no revising-cascade validator, no first-workspace exercise.

All prior ground rules from the preceding handoff still hold. The additions in this session extend them; they do not replace them. Treat the "Ground rules" section of `2026-04-25_0028` as still load-bearing.

All work shipped in a single commit: **`3f0a56d14`** (`feat(a4): unify decision transitions via transition_status.py`). Plugin version bumped **1.10.0 → 1.11.0**.

# Ground rules added this session

These extend the single-writer / mechanical-vs-semantic invariants from the prior handoff. Same status as those — treat as constraints, not suggestions.

- **Decision family is now under the single writer.** `draft → final` and `final → superseded` on `decision/*.md` flow through `transition_status.py`. `/a4:decision` does not write `status:` inline anymore — it writes `status: draft` at file-creation time only, then calls the writer to flip to `final` when the user signals commitment. The PostToolUse hook that used to run the cascade (`propagate-superseded.sh`) is gone.
- **Decisions are always born at `draft`.** Even when the user unambiguously wants to record as `final`, `/a4:decision` writes the new file with `status: draft` and then calls `transition_status.py --to final` in the same session. This matches the pattern across all other issue families (UC: `draft`; task: `pending`; review: `open`) — the file is born at the most-draft-ish status its schema allows, and every subsequent flip goes through the writer. The "birth + flip" is one user-perceived action but two writer events, which keeps the invariant uniform.
- **Re-invocation of `/a4:decision` on an existing draft is the `finalize` path.** There is **no dedicated `finalize` dispatch mode** (like `/a4:idea discard`). The skill's Step 1 reads the seed + recent conversation to detect "the user is referring to an already-recorded draft decision," confirms with one light question, then skips Steps 2–5 and jumps directly to Step 6 (the writer call). This kept the command surface small. If the detection fails (ambiguous seed), the skill asks once; it does not silently fall through.
- **`draft → superseded` (direct) is illegal.** Supersession presumes the predecessor was live. The only valid path to `superseded` is via the cascade fired by a newer decision reaching `final`. A decision that was never `final` cannot be superseded — delete it or leave it at `draft` instead.
- **`final → superseded` (direct, non-cascade) is legal but rarely used.** Allowed for "manually retire a decision without a replacement" scenarios. Not the primary path; the common flow is cascade-driven.
- **Decision body structure: `## Context` and `## Decision` are mandatory; everything else is free-form headed sections.** The writer mechanically enforces the two required sections (substring presence check, same mode as UC's `## Flow`). Beyond those, any additional `##` heading is fair game — common examples documented in SKILL.md and frontmatter-schema.md are Options Considered, Rejected Alternatives, Next Steps, Consequences, Migration Plan, Open Questions. Prose outside a headed section is forbidden. This matches the `spark-brainstorm` model (Context / Discussion Journey / Ideas required, rest additive) and replaces the former "Typically present" prescriptive list that had been nudging decisions toward a technical-ADR shape.
- **Decision sweep covers the same supersedes-chain recovery as UC sweep.** `transition_status.py --sweep` now walks `a4/usecase/` (shipped successors) **and** `a4/decision/` (final successors) and fires the appropriate cascade on each. Idempotent in both directions.

# What got built (commit `3f0a56d14`)

## `scripts/transition_status.py` — decision family added

- **New transition table** `DECISION_TRANSITIONS = {"draft": {"final"}, "final": {"superseded"}}`. `superseded` is absent from the keys, so it is terminal. `draft → superseded` and `final → draft` are both rejected.
- **New family entries** in `FAMILY_TRANSITIONS` and `FAMILY_STATES` (the latter includes `superseded` as a valid target state, reachable via cascade or direct call from `final`).
- **New `_validate_draft_to_final(fm, body, issues)`** — the mechanical validator for decision `draft → final`. Checks:
  - `title:` contains no placeholder (`TBD`, `???`, `<placeholder>`, `<todo>`, `TODO:`).
  - Body contains the substring `## Context`.
  - Body contains the substring `## Decision`.
- **`validate_transition` dispatch** extended to route `family == "decision"` to the new validator when `from → to` is `draft → final`. Other decision transitions have no mechanical checks (superseded is reachable only from `final`, and that path is cascade-driven).
- **New `_cascade_decision_final(...)`** — analogous to `_cascade_uc_shipped` but scoped to decision. Runs only when the primary transition was `draft → final`. Walks `supersedes:` on the successor; for each same-family target:
  - skips cross-family entries with reason `cross-family-supersedes`,
  - skips missing targets with an error (not a skip),
  - skips `already-superseded` targets,
  - skips targets at statuses other than `final` with reason `not-terminal-active` (e.g., predecessor still at `draft`),
  - for `final` targets, calls `_apply_status_change(..., "final", "superseded", f"superseded by {decision_ref}", ...)` and appends a `Change` to `report.cascades`.
- **`transition()` dispatch** extended: `elif family == "decision": if new_status == "final": _cascade_decision_final(...)`. Runs after the primary write, same single-commit discipline as UC cascades.
- **`sweep()` extended** to walk `a4/decision/*.md` after UCs. For each decision at `status: final` with a non-empty `supersedes:` list, build a synthetic `Report` and call `_cascade_decision_final` with `from_status="draft"` (synthetic — the cascade only needs `from_status != <non-draft>` to run; passing "draft" preserves the assertion inside the function). Resulting `Report` is only appended to the output list if it has cascades or errors, so a clean sweep still prints "no supersedes cascades needed."
- **Module docstring** updated to include the new decision cascade line in the cascade table.

## `/a4:decision` SKILL.md — full rewrite

The skill is now structured in 8 steps (was 7). Key changes:

- **Step 1 (new): Detect mode.** Read `$ARGUMENTS` + recent conversation. If the seed matches an existing `decision/*.md` at `status: draft` (glob + frontmatter read), this is the **finalize-existing** path — confirm once and jump to Step 6. Otherwise, this is the **new record** path and continues with Step 2.
- **Step 4 (renumbered from Step 3): Decide on status via dialogue.** Same natural-language signal interpretation as before, but the result is **recorded, not written**. The file will still be born at `draft` in Step 5; Step 6 applies the flip.
- **Step 5 (renumbered): Allocate id, slug, write file.** Frontmatter always has `status: draft`. Body includes `## Context` and `## Decision` (required by the writer's next step) plus any other sections the session produced. The step explicitly lists body rules: Required (Context, Decision) / Commonly used examples (not prescribed — Options Considered, Rejected Alternatives, Next Steps, Consequences, Migration Plan, Open Questions) / Free-form principle (any `##` is fine, no prose outside a section).
- **Step 6 (new): Finalize via writer.** Runs when either (a) Step 4 signaled `final` in new-record mode, or (b) the whole invocation came in via Step 1's finalize-existing path. Shell-out to `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" "<a4>" --file decision/<id>-<slug>.md --to final --reason "<one-liner>" --json`. Surfaces validation issues verbatim if exit is 2. Explicitly forbids `--force`.
- **Step 7 (renumbered from Step 6): In-situ wiki nudge.** Unchanged substantively; body text lightly updated so it reads correctly against the new numbering.
- **Step 8 (renumbered from Step 7): Report.** Now mentions the final status as determined by whether Step 6 ran, and cites supersedes cascades performed by the writer.
- **Non-goals:** added "Do not hand-edit `status:`. All status changes on decision files flow through `transition_status.py`; this skill never writes `status: final` directly nor uses `Edit`/`Write` to change an existing decision's status."
- **Frontmatter changes** on the skill itself: `description:` extended to mention re-invocation / finalize-existing mode. `argument-hint:` unchanged. `allowed-tools:` unchanged (still `Read, Write, Edit, Bash, Glob, Grep` — `Bash` is the channel to call the writer; `Edit` is retained for wiki nudges in Step 7).

## Scripts and hooks trimmed

- **`scripts/propagate_superseded.py`** — **deleted.** Its decision cascade is now in `transition_status.py::_cascade_decision_final`. UC cascade was already absorbed in the prior session.
- **`hooks/propagate-superseded.sh`** — **deleted.** No remaining caller; the cascade runs inline in the skill/agent flow now.
- **`hooks/hooks.json`** — the `propagate-superseded.sh` entry is removed from the `PostToolUse` block. Top-level `description:` rewritten to drop the (b) clause about "propagate superseded status to predecessor decision files" and to state plainly that **all** status writer flows (usecase, task, review, decision) live in `transition_status.py` inside skills/agents — no status-writer hooks remain.

## Validator updates

- **`scripts/validate_status_consistency.py`:**
  - Module docstring updated — drops the "Decision `final → superseded` runs via propagate_superseded.py PostToolUse hook" clause; now says the writer is `transition_status.py` across usecase/task/review/decision.
  - Comment on `SUPERSEDES_FAMILIES` updated to say `transition_status.py` is the active writer (was `propagate_superseded.py`).
  - `check_superseded()` drift message dropped the per-family writer-name branching (it used to say "transition_status.py for usecase, propagate_superseded.py for decision"). Always names `transition_status.py` now.

## Schema doc (`references/frontmatter-schema.md`)

- **§Status writers intro paragraph** — now says all four issue-status families flow through `transition_status.py`. Drops the "Decisions still use ..." sentence.
- **§Status writers table** — decision rows rewritten:
  - `decision / draft`: `/a4:decision` (file always born at draft).
  - `decision / final`: `/a4:decision` Step 6 via `transition_status.py`, with cascade note.
  - `decision / superseded`: `transition_status.py` cascade (was `propagate_superseded.py` hook).
- **Discovery principle paragraph** — drops the parenthetical "transition_status.py for usecase/task/review, propagate_superseded.py for decision" and just says `transition_status.py` is the active writer for all cascade-materialized statuses.
- **§Decision type introduction** — rewrote the last sentence of the opening paragraph. The old sentence ("The body may carry any of `## Context`, `## Options Considered`, `## Decision`, `## Rejected Alternatives`, `## Next Steps` as the decision's scope warrants; none are enforced by frontmatter validation.") is replaced with a two-paragraph **Body structure** block explicitly listing required sections (Context, Decision) as mechanically enforced by `transition_status.py` on `draft → final`, examples of commonly used sections, and the "headed sections only" rule.
- **Decision lifecycle paragraph** (line ~284) rewritten — mentions `transition_status.py` as the mover for both `draft → final` and the cascade; explicitly calls out that `draft → superseded` is not a valid direct transition.
- **§Cross-file status consistency table** — the `decision.status = superseded` row now attributes the materialization to `transition_status.py` cascade (was `propagate_superseded.py (actively writes, decision-only)`).
- **§Cross-references** — the `propagate_superseded.py` bullet is removed. The `transition_status.py` bullet's one-liner is extended to mention the new decision cascade.

## `marketplace.json`

Plugin `a4` version bumped **1.10.0 → 1.11.0**. No other plugin entries touched.

# Transition matrix (decision added; rest unchanged)

```
Decision: draft ──► final
          final ──► superseded
          superseded ──► (terminal)
```

For reference, the other families from the prior handoff remain:

```
UC:       draft ──► ready | discarded
          ready ──► draft | implementing | discarded
          implementing ──► shipped | revising | discarded | blocked
          revising ──► ready | discarded
          blocked ──► ready | discarded
          shipped ──► superseded | discarded
          superseded ──► (terminal)
          discarded ──► (terminal)

Task:     pending ──► implementing | discarded
          implementing ──► complete | failing | pending | discarded
          complete ──► pending | discarded
          failing ──► pending | implementing | discarded
          discarded ──► (terminal)

Review:   open ──► in-progress | resolved | discarded
          in-progress ──► open | resolved | discarded
          resolved ──► open  (for reopening)
          discarded ──► (terminal)
```

Any edge not listed is rejected by `transition_status.py` with a clear "allowed from X: [...]" error message. Decision reaches `superseded` almost always via the cascade triggered by a successor's `draft → final`; the direct `final → superseded` call is legal but is reserved for manual retirement without a replacement.

# Mechanical validation matrix (expanded for decision)

```
UC ready → implementing        : implemented_by non-empty, actors non-empty,
                                 ## Flow present, title no placeholder
UC revising → ready            : actors non-empty, ## Flow present, title no placeholder
UC implementing → shipped      : every task in find_tasks_implementing(uc) is complete
Decision draft → final         : title no placeholder, ## Context present, ## Decision present
(all other transitions)        : no mechanical checks — table legality only
```

`--force` bypasses mechanical checks but cannot bypass table legality. The decision mechanical check uses substring presence the same way UC's `## Flow` check does — simple, loose, accepts `## Context` at any line position; does not require content beneath.

# Verification performed

Fresh fixture at `/tmp/a4-decision-test/a4/decision/` with four files:

- `100-first.md` (`status: draft`, empty `supersedes:`, full Context+Decision body)
- `101-second.md` (`status: draft`, `supersedes: [decision/100-first]`, full body)
- `102-missing-context.md` (`status: draft`, `##` Decision only — no `##` Context)
- `103-placeholder-title.md` (`status: draft`, `title: "TBD"`, full body)

End-to-end paths exercised:

1. **`100 draft → final`** with `--reason` — writes status + bumps updated + appends `## Log` entry. Confirmed by file read.
2. **`101 draft → final --json`** with non-empty supersedes — JSON output shows primary flip + single cascade entry (`100: final → superseded`). Fixture file read confirms 100's status, `updated:`, and Log line were all updated in the same invocation.
3. **`102 → final`** — validation fails with `body is missing \`## Context\` section.`, exit 2.
4. **`103 → final`** — validation fails with `` `title:` contains placeholder `TBD`. ``, exit 2.
5. **`100 (superseded) → final`** — rejected as illegal-terminal with message `allowed from \`superseded\`: none (terminal)`, exit 2.
6. **`100 (superseded) → draft`** — same illegal-terminal rejection, exit 2.
7. **`101 (final) → superseded`** direct call — **legal**, succeeds (verifies manual retirement path works without requiring a successor).
8. **`103 (draft) → superseded`** direct call — rejected as illegal transition: `Allowed from \`draft\`: ['final']`, exit 2.
9. **`--sweep`** on fixture restored to `100 final / 101 final / 101 supersedes: [100]` — reports one cascade (100 → superseded), writes it, exit 0.
10. **Second `--sweep`** on the just-swept state — `OK — no supersedes cascades needed`, exit 0 (idempotent).
11. **`--validate --to final` on `103`** — returns exit 2 with `validation_issues: [placeholder]`, no file write.
12. **`validate_status_consistency.py a4`** on clean fixture — `OK — no status-consistency mismatches`, exit 0.
13. **Drift injection** — manually reverted 100 to `status: final` while 101 remained `final` with `supersedes: [100]`. Consistency validator reported `missing-superseded-status-decision` and named `transition_status.py` (not `propagate_superseded.py`) as the remediation path — confirms message rewrite landed.
14. **File-scoped consistency check** (`--file decision/100-first.md`) on the same drifted state — surfaces the same mismatch with correct message.
15. **`validate_frontmatter.py a4`** on clean fixture — `OK — 4 file(s) scanned, no violations` (new decision enum unchanged; no schema edits needed).

Not verified:

- **Real a4/ workspace end-to-end.** Still no real workspace under `plugins/` — the prior handoff also noted this. First production exercise of the decision single-writer flow awaits a project.
- **`/a4:decision` re-invocation detection on existing draft.** Prose is written in Step 1 of the SKILL; the natural-language pattern-match has not been stress-tested against ambiguous seeds. Behavior for ambiguous cases is "ask once," not silent fall-through — this is by design but has not been exercised.
- **Cascade correctness when `supersedes:` points at a decision still at `draft`.** Covered by the `not-terminal-active` skip path (analogous to UC's handling); not end-to-end tested this session. Low risk — same code shape as the already-verified UC path.

# Rejected alternatives

Ordered roughly by how much discussion they consumed:

- **Allow birthing at `status: final` directly.** Considered as less invasive: let `/a4:decision` write the file at `final` in one shot when the user's signal is clear, and only call `transition_status.py` for the later cascade. Rejected for consistency — UC is always born at `draft`, task at `pending`, review at `open`; decision should follow the same "born at most-draft-ish, flip via writer" pattern. Two writer events per conceptual action is a small price for a uniform invariant.
- **Dedicated `/a4:decision finalize <id>` or `/a4:decision:finalize` dispatch mode.** Mirrors `/a4:idea discard`. Rejected as extra command surface — the re-invocation detection in Step 1 handles the finalize-existing path with the same entry point. If the user refers to a decision by id/slug in `$ARGUMENTS`, the skill detects it; if ambiguous, one light question resolves it. Mode dispatch would have added a form of ceremony that `/a4:idea discard` needs (because `discard` is terminal and irreversible) but decision finalization does not.
- **Mechanical check: title placeholder only (Q3-a).** Initial default proposed by me. Rejected when the user pointed out that the existing `/a4:decision` SKILL.md already declared `## Context` and `## Decision` as "Required" in prose, while `frontmatter-schema.md` said "none are enforced." The gap was closable at the writer level with minimal cost (two substring checks), and the closure also eliminates the inconsistency between the two docs. Chose Q3-c (title + both sections) on that basis.
- **Mechanical check: require `## Options Considered`, `## Next Steps`, `## Rejected Alternatives` too.** Briefly considered as the "maximalist" option. Rejected because it bakes the technical-ADR shape into every decision, including vocabulary / team / role / process decisions where those sections are artificial. The free-form-beyond-required-sections rule handles this cleanly.
- **Separate free-form body rule as "all sections optional, warn when missing."** Rejected as strictly worse than mechanical enforcement of the two required ones — warnings are ignorable, mechanical validation with a clear error is not. The cost of enforcement is zero once the substring checks are in.
- **Keep `propagate_superseded.py` as a library (not a CLI), call it from `transition_status.py`.** Briefly considered to avoid deleting the code. Rejected — the cascade logic is ~60 lines and integrates more cleanly as a method inside `transition_status.py` (no cross-module state, shared frontmatter IO helpers). Deleting the file in full is the cleaner endpoint.
- **Leave the PostToolUse hook as a "defense in depth" fallback.** Rejected — the hook ran `propagate_superseded.py`, which we just deleted. Keeping the hook would require rewriting it to invoke `transition_status.py --sweep` on every decision edit, which both duplicates the in-flow cascade and introduces the exact hook-vs-script ambiguity the prior session's single-writer push eliminated. Clean delete is the right call.
- **Line-start anchor on the section-presence checks (`^## Context`).** Briefly raised as an edge-case tightening (substring `"## Context"` also matches `### Context`). Deferred as out-of-scope for this migration — UC's existing `## Flow` check has the same loose shape, and tightening both together keeps them consistent. Parked for a later session if the edge case ever bites.
- **Cross-family supersedes (decision supersedes usecase).** Already rejected in prior threads; reaffirmed here by the `cross-family-supersedes` skip path in the new decision cascade — same handling shape as UC.

# Design principles added (for future sessions)

Most principles from the prior handoff (one writer per family-of-transitions; mechanical vs semantic validation split; cascade must be same-commit; validator mirrors writer; script-driven not hook-driven) still hold and were reinforced. One new articulation:

1. **"Born draft, flip via writer" is now universal across issue families.** Every new issue file is written at the most-draft-ish status its schema allows (UC: `draft`; task: `pending`; review: `open`; decision: `draft`; idea: `open`; brainstorm: `open`). Subsequent transitions go through `transition_status.py` (or the family-appropriate writer for idea/brainstorm once those migrate). No skill or agent writes a non-birth status directly — not even when the user's signal is unambiguous in the same session. This is the surface rule that makes "single writer" uniform across the workspace.

2. **Required body sections are a mechanical contract, not prose guidance.** If a section is listed as "required" in a skill's documentation, the writer must enforce its presence on the relevant transition. Otherwise it is not required — it is merely common. This closes the gap where `/a4:decision` SKILL.md used to say `## Context` / `## Decision` were required while `frontmatter-schema.md` said "none are enforced." In the new model, "required" is a statement of what the writer will reject, nothing else.

3. **Free-form body past required sections is the default.** Where a skill has historically listed a "typically present" set of sections, review whether those entries are genuinely canonical or are subtly prescribing a single shape. In the decision case, "typically present" was pressuring every decision toward a technical-ADR skeleton, producing placeholder-grade sections in the non-technical decisions (vocabulary, team, scope). The rule becomes: require exactly what the writer enforces; list other sections as "commonly used examples"; defer to the session content for the rest.

# Plausible follow-ups (not done; user has not requested)

Refreshed from the prior handoff's list — items that remain open, items resolved this session, and items newly surfaced.

1. **End-to-end in a real workspace.** Still open. No real `a4/` workspace exists under `plugins/`. First production run will now also exercise `/a4:decision` re-invocation detection on an existing draft, the Step 5 → Step 6 hand-off, and `## Context` / `## Decision` mechanical validation.
2. **SessionStart hook for `refresh_implemented_by.py`.** Still open. Not touched this session.
3. **Revising-cascade consistency check.** Still open. `validate_status_consistency.py` flags discarded-cascade drift but not revising-cascade drift. Could be added as `missing-revising-cascade-task`.
4. **`/a4:decision` migration to `transition_status.py`.** **Resolved this session.**
5. **`idea.promoted` / `brainstorm.promoted` materialization.** Still open. Discussed at length at the start of this session — the user's initial direction was "what about item 5?" but then pivoted to item 4 after the conversation clarified the scope. Leading proposal from that discussion (not decided): **Option B** — add a `promote` mode to `/a4:idea` and `/a4:spark-brainstorm` (first-token dispatch, symmetric with `/a4:idea discard`). Key open sub-questions: how often promotion actually happens, brainstorm N:1 relationship handling (one shot vs. incremental append), idea promote reversibility (mirror the current `discard` refusal on already-promoted ideas). Log of that discussion lives in this session's conversation; no handoff-level record was added.
6. **`compass` sweep of the new scripts.** Still open. `compass` should probably call `refresh_implemented_by.py --sweep` + `transition_status.py --sweep` (now covers both UC and decision) + existing validators. Not wired.
7. **Task kind interaction with `discarded`.** Still open. No change this session.
8. **Tighten substring checks to line-anchored regex** (`^## Context`, `^## Decision`, `^## Flow`). New item surfaced this session. Low priority — the edge cases it guards against (`### Context` embedded in body) have not been observed. If tightened, do all three together for consistency.
9. **First real exercise of `/a4:decision` re-invocation detection.** New item. Prose is written but pattern-matching on ambiguous seeds has not been stress-tested. Watch for it on first production use.
10. **Validator for decision body sections on `final` files** (drift: a decision gets its body edited post-finalize and loses one of the required sections). Not currently checked by anything — the writer only enforces at transition time. Could be added to `validate_body.py` or a sibling. New item; low priority.

# Explicitly untouched

- **Idea / brainstorm families.** Enum unchanged; their `promoted` writers remain writer-less. Item 5 above.
- **`auto-usecase` wrap-up.** The "do not advance any UC past `status: draft`" rule from the prior thread still holds; `/a4:auto-usecase` was not edited.
- **`validate_body.py`, `allocate_id.py`, `read_frontmatter.py`, `extract_section.py`, `inject_includes.py`, `refresh_implemented_by.py`, `drift_detector.py`, `index_refresh.py`** — not touched.
- **SessionStart / SessionEnd / Stop / PreCompact hooks** — only `hooks.json` was edited (entry removal). No behavioral change to the remaining hooks.
- **All agents (`task-implementer`, `plan-reviewer`, `usecase-reviewer`, `usecase-composer`, `usecase-explorer`, `domain-updater`, `api-researcher`, `research-reviewer`, `mock-html-generator`, `test-runner`, `arch-reviewer`, `usecase-reviser`)** — not touched. The writer they interact with (`transition_status.py`) now also covers decision, but none of them write decisions today.
- **Prior-thread handoffs.** Snapshots; not edited.
- **`spec/*.decide.md` files.** Historical decision records. They carry their original `status: final` values; none were regenerated.

# Key files to re-read on the next session

- `plugins/a4/scripts/transition_status.py` — now the sole status writer for all four issue families. Start with the module docstring, then `FAMILY_TRANSITIONS` / `FAMILY_STATES` (updated), then `validate_transition` (new decision branch), then `_validate_draft_to_final` (new), then `_cascade_decision_final` (new), then the extended `sweep()`.
- `plugins/a4/skills/decision/SKILL.md` — fully rewritten. Read it top-to-bottom; Step 1 (mode detection), Step 5 (body rules), and Step 6 (writer finalize) are the meat.
- `plugins/a4/references/frontmatter-schema.md` — §Status writers, §Decision (rewritten body-structure paragraph + lifecycle sentence), §Cross-file status consistency row for decision, §Cross-references list.
- `plugins/a4/hooks/hooks.json` — confirm no status-writer hooks remain.
- `plugins/a4/scripts/validate_status_consistency.py` — updated docstring + drift messages.

# Outstanding parked threads

- **`uc-status-transition-system`** (this thread) — open. Two threads of work remain within its broad scope: (a) tightening section-presence substring checks to line-start regex, (b) validator for body-section drift on already-`final` decisions. Both are optional; neither is commissioned.
- **Candidate next sessions** (not yet requested by the user):
  - `idea.promoted` / `brainstorm.promoted` writer migration (the re-opened discussion from the start of this session) — likely Option B (promote mode on `/a4:idea` + `/a4:spark-brainstorm`) if the user returns to it.
  - `SessionStart` hook for `refresh_implemented_by.py`.
  - First real-workspace adoption, which will exercise the full new decision flow end-to-end.
- **`decision-slot-unification`** — effectively concluded as of the prior thread. With decision now on the single writer, the original "decision has a hook but UC does not" asymmetry is gone.
- **`a4-redesign`, `experiments-slot`, `idea-slot`** — unaffected.
