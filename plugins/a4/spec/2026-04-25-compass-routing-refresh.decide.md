---
title: "Compass routing refresh for /a4:run and /a4:task era"
status: final
decision: "Refresh `compass/SKILL.md` with three surgical inserts: a brownfield intent branch in Step 2, bootstrap-aware gap diagnosis in Step 3.3 Layer 1, and an inter-skill entry contract that establishes compass as the canonical fallback router."
supersedes: []
related: []
tags: [compass, routing, skill-selection]
created: 2026-04-25
updated: 2026-04-25
---

# Compass routing refresh for /a4:run and /a4:task era

## Context

`plugins/a4/skills/compass/SKILL.md` routes user intent across a4 skills. Its current shape is two top-level branches off Step 1:

- **Step 2 — Fresh Start.** When the workspace is empty or the user describes a vague intent, present the skill catalog and let the user pick.
- **Step 3 — Gap Diagnosis.** When the workspace has wiki pages or issues, walk Layer 0–6 (UCs → wiki foundation → drift alerts → review items → active tasks → blocked → completion) and recommend the next skill.

The catalog in Step 2 already lists `/a4:run` and `/a4:task`, and Layer 4 in Step 3 recommends `/a4:run iterate` for active tasks. So at the surface level, the routing reaches the new skills.

Three real gaps remain, surfaced during the pipeline-restructure thread (Tier B 7) and during the Tier C 12 (`/a4:run` final-fallback) discussion:

1. **No brownfield branch in Step 2.** Step 2 assumes "empty workspace = greenfield, user is starting fresh." When the project has implementation code already (a brownfield codebase that wants to adopt a4 retroactively), the catalog is the wrong response — the user does not want to write `context.md` from scratch; they want to choose between (a) reverse-engineer the workspace from existing code, (b) bolt on a single small change without the full pipeline, or (c) start the formal pipeline for a new feature on top of the existing code. Step 2 currently funnels all three into the same skill catalog.

2. **Layer 1 of Step 3 has a `bootstrap.md` blind spot.** Layer 1 (Wiki foundation) checks for `domain.md`, `architecture.md`, and `roadmap.md` presence, but does not check `bootstrap.md`. The pipeline order is `context → domain → architecture → bootstrap → roadmap → tasks/run`, so a workspace with `architecture.md` but missing `bootstrap.md` should route to `/a4:auto-bootstrap` before `/a4:roadmap` is suggested. Without this rule, gap diagnosis can recommend roadmap authoring against an unverified dev environment.

3. **No inter-skill entry contract.** Compass is currently described as a user-facing skill — invoked when the user types `/a4:compass` or asks "what should I do next." It is not described as a callable router for other skills. Tier C 12 (`/a4:run` final-fallback) needs `/a4:run` to halt and delegate to compass when its preconditions are not met (`roadmap.md` missing, `bootstrap.md` missing, etc.). For that delegation to be a stable contract, compass must explicitly accept and document a "called from another skill" entry shape.

This is the carry-forward of "Tier B 7" from the pipeline-restructure thread (see [`plugins/a4/.handoff/pipeline-restructure/2026-04-25_1527_carry-forward-link-rule.md`](../.handoff/pipeline-restructure/2026-04-25_1527_carry-forward-link-rule.md) §Tier B 7).

## Decision

Refresh `compass/SKILL.md` with three surgical inserts, not a full Layer 1–4 rewrite:

### 1. Brownfield branch in Step 2 (Fresh Start)

Before showing the skill catalog, detect whether the project has implementation code outside `a4/`:

- Heuristic: any tracked file at the project root that matches a build/manifest signature (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, etc.) **or** any tracked source file outside `a4/`, `plugins/`, `.claude*/`, and `research/`.
- If detected and `a4/` is empty, ask **one** question before showing the catalog:

  > This project has existing code but no a4 workspace. What are you trying to do?
  > - **(a) Reverse-engineer** — extract use cases and supporting wiki pages (`context.md`, `actors.md`, `domain.md`) from the existing code.
  > - **(b) Single change** — make one small change without the full pipeline (write `bootstrap.md` minimally, then `/a4:task` → `/a4:run`).
  > - **(c) New feature** — start the formal pipeline (`/a4:usecase` → `/a4:arch` → `/a4:auto-bootstrap` → `/a4:roadmap` → `/a4:run`) for a new feature on top.

- Route based on the answer:
  - **(a)** → invoke `/a4:auto-usecase` with the project root (or a specific source path) as the argument. The skill autonomously performs code analysis per its Step 2b, extracts user-facing features as UC candidates with `## Source: code — <path>` attribution, and produces `context.md` / `actors.md` / `domain.md` / per-UC files at `status: draft` for the user to review via `/a4:usecase iterate`. Existing UCs (partial brownfield) trigger the skill's expansion mode automatically.
  - **(b)** → invoke `/a4:auto-bootstrap` (which already supports incremental mode against an existing codebase per its Step 1 "Codebase Assessment"), then `/a4:task`.
  - **(c)** → fall through to the existing skill catalog (`/a4:usecase` or whichever entry skill the user picks).

When no implementation code is detected and `a4/` is empty, behavior is unchanged — show the catalog as today.

### 2. Bootstrap-aware Layer 1 in Step 3.3 Gap Diagnosis

Insert one bullet into Step 3.3 Layer 1 (Wiki foundation), placed between the `architecture.md` and `roadmap.md` checks:

- `architecture.md` exists, `bootstrap.md` missing → recommend `/a4:auto-bootstrap`.

The downstream `roadmap.md`-missing check then assumes `bootstrap.md` is present. The pipeline check order in Layer 1 becomes the strict prefix `usecase → domain → architecture → bootstrap → roadmap`, matching the actual data dependency graph.

### 3. Inter-skill entry contract

Add a short subsection at the top of `compass/SKILL.md` (after the description, before Step 0) titled **"Inter-skill entry"**:

> Compass is also callable as a fallback router from other a4 skills. When another skill's preconditions are unmet (e.g., `/a4:run` invoked without `roadmap.md` or `bootstrap.md`), it halts and invokes compass via the Skill tool, passing the workspace state diagnosis as the argument. Compass treats this as Step 1 with an empty argument — no special branch — but skips the "What are you trying to do?" prompt in Step 2 if the calling skill already determined the intent.

This makes the `/a4:run` → compass delegation a documented contract rather than an ad-hoc call. Tier C 12's ADR ([[plugins/a4/spec/2026-04-25-a4-run-final-fallback-policy]]) concretizes the calling side; this ADR fixes the receiving side.

## Options Considered

- **Full Layer 1–4 rewrite.** Rejected — the existing layers are sound; the gaps are localized. Rewriting risks regressing the catalog accuracy and Layer 4 (`/a4:run iterate`) routing that already works.
- **Inline `<!-- TODO -->` markers in `compass/SKILL.md` instead of an ADR.** Rejected because the changes raise plugin-meta-design questions (brownfield branch UX, inter-skill contract shape) that need a recorded decision per `plugins/a4/CLAUDE.md`. The original Open Question 1 in this ADR's draft form weighed this trade-off and resolved toward a full ADR.
- **Auto-detect intent in Step 2 (b) brownfield without asking.** Rejected — the three intents (reverse-engineer / single change / new feature) are too divergent to disambiguate from heuristics alone. One question is cheaper than wrong routing.
- **Make compass detect every precondition for every skill itself, removing the need for skills to halt and delegate.** Rejected — that would re-implement each skill's precondition logic in compass. The inter-skill entry contract is the lighter inversion: each skill knows its own preconditions and delegates back to compass when they fail.

## Consequences

- `compass/SKILL.md` gains a brownfield branch in Step 2, a bootstrap check in Step 3.3 Layer 1, and an "Inter-skill entry" subsection. Three surgical edits, no rewrite.
- The Tier C 12 ADR ([[plugins/a4/spec/2026-04-25-a4-run-final-fallback-policy]]) can now reference this ADR's inter-skill entry contract as the receiving end of `/a4:run`'s halt-and-delegate behavior. The two ADRs are siblings: Tier B 7 fixes the receiver, Tier C 12 fixes the caller.
- The brownfield reverse-engineer path (Step 2 (a)) routes to `/a4:auto-usecase`, which already treats source-code paths as a first-class input per its Step 1 ("source-code directories → code analysis target") and Step 2b (autonomous code analysis subagent). UCs produced this way carry `## Source: code — <path>` attribution. No new skill or branch is needed for `(a)` to function — the audit confirmed `/a4:auto-usecase` already does the work. `/a4:context` and `/a4:domain` do not exist as standalone skills; their wiki pages (`context.md`, `domain.md`) are produced as side effects of `/a4:usecase` (interview) and `/a4:auto-usecase` (autonomous). The composer subagent of `/a4:auto-usecase` writes all four wiki pages (`context.md`, `actors.md`, `domain.md`, `nfr.md`) alongside per-UC files in one pass.
- The brownfield code-detection heuristic (build manifests + source files outside `a4/`) is a best-effort signal, not a contract. False positives (a brand-new project with a `package.json` but no real code) result in one extra question; false negatives (an unusual project layout) fall through to the catalog. Both modes are recoverable.

## Open Questions

- **Test surface for routing correctness.** Routing is not unit-tested. The `/a4:compass` skill itself is the test driver and the user is the judge. Manual walk-through of canonical intents (empty workspace + no code, empty workspace + code, partial workspace at each pipeline step, fully populated workspace) is sufficient for now. Worth revisiting if routing regressions become recurring.
- **Should compass surface the brownfield-branch decision somewhere persistent?** Currently the user's answer (a/b/c) is consumed once and lives only in the conversation. If they re-invoke compass later in the same empty-but-not-quite workspace, they answer again. Possible mitigation: write a one-line marker into `a4/INDEX.md` or a tiny config file. Deferred — out of scope for this ADR; revisit if friction reports accumulate.

## Next Steps

This ADR's three inserts are now applied to `plugins/a4/skills/compass/SKILL.md`. The implication for downstream work is that Tier C 12's ADR ([[plugins/a4/spec/2026-04-25-a4-run-final-fallback-policy]]) can be drafted against this ADR's "Inter-skill entry" subsection as the receiving-side contract — when `/a4:run` (or any other skill) halts on missing preconditions, it delegates to compass with a `from=<skill>; missing=<files>` argument shape, and compass routes to Step 3 Gap Diagnosis with the diagnosis text as input.
