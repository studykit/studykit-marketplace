---
title: "/a4:run final-fallback policy when neither roadmap nor bootstrap exists"
status: final
decision: "When `/a4:run` cannot resolve a Launch & Verify source, halt and delegate to `/a4:compass` via the inter-skill entry contract. Compass's Step 3 Gap Diagnosis (with the new bootstrap-aware Layer 1) walks the pipeline backward from the missing artifact and recommends the correct upstream skill. `/a4:run` does not implement its own fallback ladder."
supersedes: []
related: []
tags: [a4-run, fallback, ux]
created: 2026-04-25
updated: 2026-04-25
---

# /a4:run final-fallback policy

## Context

`/a4:run` selects work to execute when invoked. The current selection ladder consults `<project-root>/a4/roadmap.md` first, then `<project-root>/a4/bootstrap.md`. When neither file exists in the workspace, the current behavior degrades inconsistently — sometimes a no-op, sometimes a confused selection from `task/`, sometimes an error. The current `run/SKILL.md` "Launch & Verify Source" §3 says only "Halt … final fallback policy for projects that decline both is unresolved (see Out of Scope)."

Three layers of context narrow the answer:

1. **The pipeline is a strict prefix.** `usecase → domain → architecture → bootstrap → roadmap → tasks/run`. When a downstream artifact is missing, the user has not skipped one step — they have skipped some prefix of upstream steps. So the right response is "find the deepest missing upstream artifact and route there," not "offer a single hard-coded fallback."

2. **Compass already does this.** As of [[plugins/a4/spec/2026-04-25-compass-routing-refresh]] (Tier B 7), `compass/SKILL.md` Step 3.3 Layer 1 walks the pipeline in strict prefix order and recommends the correct upstream skill (`/a4:usecase` / `/a4:arch` / `/a4:auto-bootstrap` / `/a4:roadmap`). Compass also gained an "Inter-skill entry" subsection that documents how other skills call it as a fallback router, with a `from=<skill>; missing=<files>` argument shape.

3. **Brownfield is a real shape.** A user invoking `/a4:run` against an empty `a4/` workspace may either be (i) starting greenfield from zero, or (ii) holding an existing codebase they want to retrofit a4 onto. Compass Step 2.0 already handles (ii) by detecting code-outside-`a4/` and offering reverse-engineer / single-change / new-feature branches. `/a4:run` should not re-implement this detection.

This is the carry-forward of "Tier C 12" from the pipeline-restructure thread (see [`plugins/a4/.handoff/pipeline-restructure/2026-04-25_1527_carry-forward-link-rule.md`](../.handoff/pipeline-restructure/2026-04-25_1527_carry-forward-link-rule.md) §Tier C 12).

## Decision

When `/a4:run`'s Launch & Verify resolution fails — neither `a4/roadmap.md` nor `a4/bootstrap.md` is present — halt and delegate to compass via the inter-skill entry contract:

```
Skill({ skill: "a4:compass", args: "from=run; missing=roadmap.md,bootstrap.md" })
```

Specifically:

- `/a4:run` Step "Launch & Verify Source" §3 changes from "Halt and tell the user to run `/a4:auto-bootstrap`" to "Halt and invoke `/a4:compass` with the diagnosis argument. Do not pre-judge which upstream skill applies — compass's pipeline walk owns that decision."
- The `from=run; missing=<list>` argument shape is the canonical inter-skill entry payload established by [[plugins/a4/spec/2026-04-25-compass-routing-refresh]] §3.
- `missing` enumerates the artifacts `/a4:run` checked for. For the `roadmap.md` + `bootstrap.md` absence case, the list is `roadmap.md,bootstrap.md`. `/a4:run` does not look upstream of these (no checks for `architecture.md`, `domain.md`, etc.) — compass's Layer 1 walks the rest.
- The fallback is **not auto-execution**. Compass presents its diagnosis and recommendation; the user confirms before any upstream skill is invoked. `/a4:run` does not chain into the upstream skill itself.
- `/a4:run` is not responsible for distinguishing "fresh workspace" from "recurring-empty" (e.g., user deleted `roadmap.md`). Compass treats both identically — the pipeline walk produces the same recommendation in either case.

The `/a4:run <task-id>` carve-out (explicit task argument bypasses Launch & Verify resolution) is unchanged. This ADR governs only the no-argument or `iterate` invocation paths.

## Options Considered

- **Hard-coded fallback "offer to run `/a4:bootstrap`".** Rejected. The leading candidate from the original draft, but only correct when `architecture.md` exists. Without `architecture.md`, `/a4:auto-bootstrap` itself fails its preconditions, and the user ends up bouncing through fallback chains. Pipeline-walk is the general-case answer.
- **`/a4:run` walks the pipeline itself, recommending one skill at a time.** Rejected. Duplicates the logic compass already has post–Tier B 7 refresh. Two implementations would drift; one would fall behind. Single source of truth — compass — wins.
- **`/a4:run` walks the pipeline and chains into the upstream skill automatically (no user confirmation).** Rejected. Auto-chaining loses the user-in-the-loop check that compass provides at each step. Brownfield ambiguity (Step 2.0's three-way branch) cannot be resolved without one user question. Auto-chain conflicts with that.
- **No-op or generic help message.** Rejected. The pipeline-walk is the help message users actually want — "you're missing X; do Y next." A static help screen tells the user nothing they didn't already know.
- **Read `package.json` scripts / detect build commands and try to run them.** Rejected. Out of scope and listed as such in `run/SKILL.md` "Out of Scope" §. The decision in this ADR keeps it out of scope; "Launch & Verify must come from `bootstrap.md` or `roadmap.md`" remains a hard contract.

## Consequences

- `/a4:run` becomes thinner. The fallback policy is now a single Skill-tool call to compass with a structured argument; the multi-line "halt and tell the user" prose collapses. Other skills with similar fallback needs (e.g., `/a4:roadmap` invoked without `architecture.md`) can adopt the same pattern by following the inter-skill entry contract.
- Compass becomes more central. Tier B 7 already established it as the routing hub; this ADR makes it the routing hub for `/a4:run`'s precondition-miss case explicitly. If compass is ever broken or unavailable, `/a4:run` halts without recovery — acceptable given compass is part of the same plugin and ships together.
- The pipeline-walk handles brownfield correctly via compass Step 2.0. A user with existing code who runs `/a4:run` against an empty `a4/` is routed through "reverse-engineer / single change / new feature" before any upstream skill is suggested. `/a4:run` does not need a separate brownfield branch.
- The `Out of Scope` note in `run/SKILL.md` ("Final fallback when neither roadmap.md nor bootstrap.md exists … unresolved and not implemented") is removed by the implementing edit. The "best-effort auto-detect" / "read package.json scripts" note in the same section remains as a still-out-of-scope item.

## Open Questions

- **Should compass receive structured frontmatter as the argument, or a free-text diagnosis sentence?** This ADR specifies `from=run; missing=roadmap.md,bootstrap.md` as a key-value shape. If multiple skills end up calling compass with diverging payloads, a richer schema (JSON, frontmatter) may be warranted. Defer until a second skill adopts the contract; revisit then.
- **What happens if compass's recommended upstream skill itself has unmet preconditions (deeper missing prefix)?** In principle the recommended skill can also halt-and-delegate-to-compass, producing a chain. Compass's Layer 1 walk should already arrive at the deepest missing artifact in one pass, so chains should not occur in practice. If they do, that signals a Layer 1 walk gap and is a compass bug, not a `/a4:run` bug.
- **Does the same delegation pattern fit `/a4:roadmap` (invoked without `architecture.md`)?** Likely yes — same shape, different `missing` list. Not in scope for this ADR; `/a4:roadmap` currently halts with a recommendation, similar to pre-refresh `/a4:run`. Consider revisiting when next touching `roadmap/SKILL.md`.

## Next Steps

This ADR's implementation is a `run/SKILL.md` edit that replaces the current "Halt and tell the user to run `/a4:auto-bootstrap`" branch with the compass delegation; see `plugins/a4/skills/run/SKILL.md` "Launch & Verify Source" §3 and the related "Out of Scope" entry. Once that edit lands, `/a4:run` no longer carries a hand-rolled fallback ladder, and the inter-skill entry contract from [[plugins/a4/spec/2026-04-25-compass-routing-refresh]] has its first concrete caller.
