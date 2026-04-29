---
name: auto-usecase
description: "This skill should be used when the user wants to extract or batch-shape Use Cases from raw input — an existing codebase, an idea, brainstorm notes, or a file path — without interactive interview. Reverse-engineering an existing system into UCs is its primary job; running it on a fresh idea is a secondary mode. Triggers: 'reverse-engineer use cases', 'extract use cases from code', 'auto-generate use cases', 'auto-usecase', 'generate use cases from this idea', 'no interview needed just generate', 'run auto-usecase on'. Writes the result into <project-root>/a4/ per the spec-as-wiki+issues layout (per-UC files + context.md / actors.md / nfr.md). Not the autonomous twin of /a4:usecase — they serve different inputs; see docs/skill-modes.md for the mode taxonomy."
argument-hint: <codebase path, idea, brainstorm text, or file path to extract use cases from>
allowed-tools: Read, Write, Agent, Glob, Grep, Bash, WebSearch, WebFetch, TaskCreate, TaskUpdate, TaskList
---

# Use Case Reverse-Engineer / Batch Generator

> **Authoring contracts:** UC files — `${CLAUDE_PLUGIN_ROOT}/references/usecase-authoring.md`. Wiki pages: `${CLAUDE_PLUGIN_ROOT}/references/context-authoring.md`, `${CLAUDE_PLUGIN_ROOT}/references/actors-authoring.md`, `${CLAUDE_PLUGIN_ROOT}/references/nfr-authoring.md`. Review items: `${CLAUDE_PLUGIN_ROOT}/references/review-authoring.md`. Subagents follow those contracts at write time.

Extract or batch-shape a complete spec-as-wiki+issues Use Case set from raw input — an existing codebase, an idea, brainstorm notes, description, or file path — without human interaction. Make all decisions independently, record open questions as review items, and refine until the set meets quality criteria.

This skill is **not** the autonomous twin of `/a4:usecase`. `/a4:usecase` is a Socratic interview that draws UCs out of a user who knows the problem; this skill is a reverse / batch entry for cases where the input is raw material rather than a person to interview against. See `${CLAUDE_PLUGIN_ROOT}/docs/skill-modes.md` for the full mode taxonomy.

Generate use cases for: **$ARGUMENTS**

## Workspace

All artifacts live under `<project-root>/a4/` (resolve via `git rev-parse --show-toplevel`).

```
a4/
  context.md, actors.md, domain.md, nfr.md   # wiki pages
  usecase/<id>-<slug>.md                       # one per UC
  review/<id>-<slug>.md                        # per-finding / per-gap / per-question
  research/                                    # similar-systems research, code-analysis reports, exploration reports
```

Create `a4/`, `a4/usecase/`, `a4/review/`, `a4/research/` if missing.

## Id Allocation

Every new UC / review item uses the shared allocator:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

Subagents (composer, reviser, reviewer, explorer) each call the allocator themselves at write time — do not batch ids in the main session.

## Shared References for Subagents

Subagents read these directly — don't pull their contents into the main session.

- `${CLAUDE_PLUGIN_ROOT}/skills/usecase/SKILL.md` — file layout, frontmatter schemas, wiki update protocol.
- `${CLAUDE_PLUGIN_ROOT}/skills/usecase/references/abstraction-guard.md` — banned implementation terms.
- `${CLAUDE_PLUGIN_ROOT}/skills/usecase/references/usecase-splitting.md` — splitting guide.
- `${CLAUDE_PLUGIN_ROOT}/skills/usecase/references/usecase-relationships.md` — relationship analysis.
- `${CLAUDE_PLUGIN_ROOT}/skills/usecase/references/review-report.md` — review-item schema emitted by reviewers.

Include these paths in each subagent prompt.

## Source Attribution on UCs

Each UC body records source attribution (`input`, `research — <systems>`, `code — <path>`, or `implicit`) as a one-line note inside the relevant required section (typically the start of `## Situation`). Definitions and rationale: `references/source-attribution.md`.

## Flow

This skill runs two nested loops:

- **Outer growth loop** — compose → review → expand (via explorer / completeness) — up to 3 iterations.
- **Inner quality loop** — review → revise — up to 3 rounds per growth iteration.

| Step | Focus | Procedure |
|------|-------|-----------|
| 1 | Classify the input + resume detection | `references/input-classification.md` |
| 2 | Research (similar systems + code analysis, parallel) | `references/research-step.md` |
| 3 | Compose + refine loop (a/b/c/d) | `references/compose-refine-loop.md` |
| 4 | Final summary | `references/final-summary.md` |

## Commit Points

Per-step subject formats and timing: `references/commit-points.md`.

## Cross-Stage Findings

This skill is **continue + review item** for any architecture / domain / NFR concern that surfaces during composition or review — UC drafts are independently meaningful, so emit review items targeting the upstream wiki and finish the autonomous run. See `${CLAUDE_PLUGIN_ROOT}/docs/wiki-authorship.md` §Cross-stage feedback. Domain Model itself is **out of scope** — domain extraction lives in `/a4:domain` and is recommended in the final summary.

## Autonomous Decision Rules

Apply the rules in `references/autonomous-decision-rules.md` consistently across composition, revision, and exclusion. No user interaction is permitted — autonomous output is always `status: draft` and promotion is user-driven.

## Non-Goals

- Do not write an aggregated `a4/<topic>.usecase.md` file. All output is per-UC + wiki pages.
- Do not maintain per-topic or per-slug file naming. `a4/` is a single workspace — filenames carry no topic.
- Do not write a `history.md` file. Per-UC `## Log` sections plus git history cover audit needs.
- Do not create GitHub Issues — `a4/` replaces that role.
