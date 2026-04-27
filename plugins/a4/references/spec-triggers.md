# ADR-trigger Detection

How a4 skills and agents recognize the moments when an ADR (`a4/adr/<id>-<slug>.md`) is warranted, in dialogue or in artifact content. This complements [`pipeline-shapes.md`](${CLAUDE_PLUGIN_ROOT}/references/pipeline-shapes.md), which names the production and consumption channels for ADRs but does not catalog the triggers themselves.

Companion to:
- [`pipeline-shapes.md`](${CLAUDE_PLUGIN_ROOT}/references/pipeline-shapes.md) — when shape-aware skills branch, and where ADR production is heaviest.
- [`wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md) — who can write each wiki page; relevant when an ADR drives a wiki update.
- [`skill-modes.md`](${CLAUDE_PLUGIN_ROOT}/references/skill-modes.md) — interactive vs autonomous + forward vs reverse axes per skill.
- [`iterate-mechanics.md`](${CLAUDE_PLUGIN_ROOT}/references/iterate-mechanics.md) — review-item processing; the resolution path for ADR-trigger review items lands here.
- [`frontmatter-schema.md`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md) — adr and review frontmatter.

## What makes a moment ADR-worthy

An ADR captures a decision when **all** of the following hold:

- **Multiple viable options exist** — the choice isn't forced by the framework, the stack, or a hard constraint.
- **The trade-off is non-trivial** — picking option A vs option B changes downstream effort, surface area, or cost in a meaningful way.
- **It is non-recoverable from code alone** — reading the codebase later would not reveal *why* the option was chosen. The decision is a fact that lives outside the code.
- **It is plausibly revisitable** — future evidence could justify revisiting (a supersede candidate). One-way-door choices specifically benefit from ADR capture.

If a moment fails any of these, see Anti-patterns below — it likely does not warrant an ADR even if it superficially resembles one.

## Conversational signals (LLM in dialogue)

These signals fire while the LLM is in conversation with the user — during architecture authoring, research review, ADR authoring, or mid-implementation. The skill or agent that surfaces the signal should pause and ask whether the moment warrants an ADR; if yes, route to `/a4:adr`.

### B1. Multi-option enumeration

Triggers: "A or B", "Postgres or Mongo", "REST vs GraphQL", "should we use X or Y".

Action: pause the current flow. Ask: "This sounds like a decision worth recording. Want to run `/a4:research` first to compare the options, then `/a4:adr` to capture the conclusion?" If the user confirms, route accordingly. If the user dismisses ("just pick one — it doesn't matter"), proceed without an ADR.

### B2. Trade-off language

Triggers: "we trade X for Y", "the cost of Z is...", "장단점이 있다", "the downside of A is...".

Action: same as B1. Trade-off articulation is one of the strongest ADR-worthy signals because it implies the ADR-worthy criteria (multiple options, non-trivial trade-off) are already in the user's head.

### B3. User uncertainty markers

Triggers: "not sure", "더 생각해봐야", "I'm torn between...", "I keep going back and forth on this".

Action: clarify whether the uncertainty is decision-pending (→ `/a4:adr` after enough context) or research-pending (→ `/a4:research` to surface evidence). If neither resolves the uncertainty quickly, the moment may simply not be ready for an ADR — leave a `## Open Questions` placeholder in any draft ADR rather than forcing closure.

### B4. Prior-ADR references

Triggers: "we decided X before, but now...", "the old auth scheme...", "remember when we picked Postgres? we might want to revisit".

Action: search `a4/adr/*.md` for the prior ADR. If found:
- This is a **supersede candidate**. Use `/a4:adr` to author the new ADR with `supersedes: [adr/<prior-id>-<slug>]` populated. The `transition_status.py` cascade will flip the prior ADR to `superseded` when the new one reaches `final`.
- Do **not** edit the prior ADR's body — supersession is captured via frontmatter and the new ADR's `## Context`.

If no prior ADR is found, this is a fresh decision — proceed as B1/B2.

### B5. task-implementer architectural-choice exit

Triggers: while implementing a task, the agent encounters an architectural choice that is *not* a UC spec ambiguity (UC is clear; the choice is a design alternative not yet captured in any ADR or `architecture.md` section).

Action: halt implementation. Emit a review item with `kind: gap`, `target: adr/` (omit `target:` when no specific ADR id applies), `source: task-implementer`, body describing the choice and the alternatives surfaced. Return failure naming the review item id. The user resolves via `/a4:adr`, and `/a4:run iterate` resumes after the ADR is recorded.

This is parallel to the existing UC-spec-ambiguity exit (`implementing → revising`); the adr-gap exit does **not** flip the UC's status — the UC is fine, the architectural choice underneath it is the gap.

### B6. Mid-`/a4:run` architecture-impacting choice

Same shape as B5 from a human-driven angle. When the user (rather than the agent) surfaces the choice mid-run — "actually, I'm not sure which retry strategy to apply here" — the same exit applies: halt, emit an `adr/`-targeted gap review, route to `/a4:adr`.

## Content-aware upward propagation

Beyond live dialogue, ADR-worthy moments can be detected by reading existing artifact content. The lower-level artifact (typically a task) implies a missing upstream artifact (a UC or an ADR).

**Trigger:** a task body describes work that:
- implies a user-facing scope not captured in any existing UC, or
- implies an architectural / stack / integration choice not captured in any existing ADR.

**Sites:** `/a4:task` author (Step 2, after the smell check on `kind: feature` with empty `implements:`/`adr:`), `/a4:run` task-implementer (pre-flight content scan before implementation), `/a4:wiki-iterate` (when reconciling tasks against upstream wikis).

**Action:** emit a review item with `kind: gap`, `target: usecase/` or `target: adr/` (or omit `target:` for cross-cutting), `source: <skill-name>`, body specifying what upstream artifact appears missing and why the task content suggests it. The user resolves by:
1. Authoring the upstream artifact (`/a4:usecase` or `/a4:adr`) and pointing the task's `implements:` or `adr:` at it; or
2. Closing the review with `discarded` + rationale (e.g., "task is genuinely small, no upstream needed").

Frontmatter `kind: feature` with both `implements:` and `adr:` empty is a coarse proxy for this signal but is **not** a binary rule — sufficiently small features (UI tweaks, label changes, single-property validation, roadmap-auto-generated features without a UC group) can legitimately have neither anchor. The content-aware check is the right fidelity; the frontmatter check is just a starting hint.

## Anti-patterns (do NOT nudge for ADR)

These look like ADR moments but are not. Suppress nudges when the situation matches.

- **Routine choices.** Variable names, folder layout, file naming conventions, code formatting — these are coding-style decisions that belong in style guides or simply in the code.
- **Framework-mandated.** When the framework, runtime, or stack constrains the choice (e.g., "use React's `useState` for local state in this component" — there's no alternative within the chosen stack).
- **Post-hoc justification.** When code is already written and the conversation is just explaining what's there. ADRs are decisions; if there's no decision left to make, do not retroactively author one.
- **Multiple decisions per file.** If a session converges on three independent decisions, write three separate ADRs — each with its own `## Decision` and supersede chain — not one omnibus ADR. Use the `/a4:adr` skill once per decision.
- **Bug fixes that are just "use the right tool".** Fixing a bug by switching to the correct API call within the same library/framework is not a decision; it's a fix. Distinct from B5/B6, which surface when the *fix* would require an architectural choice (e.g., the bug reveals a missing retry strategy).

## How skills should use this reference

- Cite this doc (`${CLAUDE_PLUGIN_ROOT}/references/adr-triggers.md`) in the SKILL.md or agent system prompt at the step where signals can fire — typically the conversational step (architecture authoring, research review, ADR finalization, task implementation) rather than the wrap-up.
- Surface a signal when one of B1–B6 (or the upward-propagation shape) matches the current dialogue or artifact content.
- Run the Anti-pattern check before nudging — if the situation matches an anti-pattern, suppress the nudge.
- For B1–B4 nudges that the user dismisses, do not re-nudge in the same session for the same topic. For review-item-emission paths (B5, B6, upward propagation), the existing `discarded` + rationale flow on the review item closes the loop without re-emission (`drift_detector.py` dedup blocks per `(kind, target, cause)` fingerprint).

This reference is consumed at the point of signal recognition; it is not iterated over by a script.
