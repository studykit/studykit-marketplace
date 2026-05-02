# a4 — evidence-readiness gate (spike-before-task)

Cross-type rule for `task` and `bug` authorship: **author the issue file only when the implementer-facing facts it depends on are gathered**. When facts are missing, the issue is not yet evidence-ready and the parent issue family is `spike` (PoC code accompanies findings) or `research` (written investigation only); author the spike or research first, then resume the task / bug.

Companion to `./task-authoring.md`, `./bug-authoring.md`, `./spike-authoring.md`. Cross-type lifecycle and writer rules live in `./issue-family-lifecycle.md`.

## Why

A `task` or `bug` file is the agreed handoff anchor for implementation work. A new session opening that file in isolation must be able to start coding without re-deriving the context. When the file's `## Acceptance Criteria` and `## Files` are written but the underlying facts are missing, the file becomes a design record rather than an actionable handoff — the implementer's first move is still investigation, not implementation.

The split is **not** a quality gate on the design. The design may be fully decided; the rule fires only when the *evidence the design rests on* has not been captured. The two are independent: a task can have a strong design and weak evidence, or vice versa.

## Evidence categories

Five facts a `task` or `bug` is expected to anchor by the time it is `pending`:

1. **Reproduce command** — the exact CLI / SQL / probe / script that reproduces the situation the task addresses (a current-state measurement, a failure, a fan-out, a benchmark). Must be runnable from a fresh checkout.
2. **Code coordinates** — file paths and line spans for the call sites, helpers, fill code, and adjacent narrowing infrastructure the task touches or depends on. Symbol names alone are not enough — they rot.
3. **Data flow** — end-to-end hop list for any non-local data dependency the design assumes (a witness propagating from caller A to dispatch site B, a key flowing from constructor C to lookup D). State each hop with the file:line where it lands.
4. **Baseline measurements** — current-state numbers the task's success criteria are framed against (indexing time, fan-out cardinality, sample line count, error rate). Without baseline, "+X% within Y" acceptance criteria are unfalsifiable.
5. **Test fixture** — the synthetic project / minimal repro / fixture shape the unit-test or integration-test strategy assumes. Sketch the directory layout and key files; do not leave fixture design for the implementer.

A `task` / `bug` is **evidence-ready** when each of the five is present in the file, the cited spec, or a linked spike's artifact directory. "We know this from a previous session" or "the user confirmed it in chat" is not present.

## When to split

Split into a `spike` (with `parent:` pointed at the still-being-drafted task / bug, or vice versa) when **two or more** of the five evidence categories are empty.

- **Spike vs. research** — if the evidence requires running code (probes, benchmarks, dry-runs against the project's own indexer / DB / sample corpus), use `spike` and put the runnable artifact under `artifacts/spike/<id>-<slug>/`. If the evidence is gathered by reading code and external sources only (no PoC, no scripts to keep), use `research`.
- **One-evidence-category miss** is a soft signal — capture the gap inline as an open question in the task / bug `## Resume`, do not split. Splitting on a single missing fact is over-process.
- **All five missing** — the design itself is probably not decided yet. Do not author a task; the parent issue family is `spike` or `research` from the start.

## Linkage

When a spike is spun out before the task / bug:

- The spike is authored first at `status: pending`. Its `## Description` states the question and the decision the spike's outcome will inform; its `## Acceptance Criteria` enumerates which of the five evidence categories the spike must populate.
- The spike's artifact directory at `artifacts/spike/<id>-<slug>/` holds reproducible probes (scripts, queries, configs) and any captured outputs that became evidence.
- The follow-up task / bug declares `parent: spike/<id>-<slug>` (derivation parent) or `depends_on: [spike/<id>-<slug>]` when the relationship is consumption-only. The follow-up's `## Description` cites the spike, and its evidence sections quote the spike's findings rather than re-deriving them.
- The reverse — task / bug authored first, spike spawned mid-flight when an evidence gap surfaces — is also valid; in that case the spike's `parent:` points at the originating task / bug.

The rule is symmetric for `bug`: a regression report without a reproducible failure path is exploratory until reproduction is captured. Spike (or research, when no code runs) the reproduction first; author the bug afterward with `parent:` pointing at the spike.

## Out of scope

- Wiki authoring (`actors`, `architecture`, `bootstrap`, `context`, `domain`, `nfr`) — wikis are not implementation handoffs; the evidence-readiness lens does not apply.
- `usecase`, `spec`, `umbrella`, `idea`, `brainstorm`, `review` — none are implementer-facing in the same sense; their own authoring contracts cover their evidence-shape.
- Quality of the design itself — this rule does not govern AC depth, file-list completeness, or test-strategy soundness. Those belong to the per-type authoring contract.
