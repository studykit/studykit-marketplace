---
name: extract-usecase
description: "Generate use cases from raw inputs without an interview."
argument-hint: <codebase path, idea, brainstorm text, or file path to extract use cases from>
disable-model-invocation: true
allowed-tools: Read, Write, Agent, Glob, Grep, Bash, WebSearch, WebFetch, TaskCreate, TaskUpdate, TaskList
---

# Use Case Extractor / Batch Generator

Extract or batch-shape a complete Use Case set from raw input — an existing codebase, an idea, brainstorm notes, description, or file path — without human interaction. Make all decisions independently, record open questions as review items, and refine until the set meets quality criteria.

This skill is independent. It does not require any prior a4 skill to have run, and does not direct the user to any specific next skill — the user picks where to go after the run finishes (typical follow-ups include `/a4:usecase iterate` to review the drafts, `/a4:domain`, or `/a4:arch`).

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

## Shared References for Subagents

Subagents read these directly — don't pull their contents into the main session.

- `${CLAUDE_PLUGIN_ROOT}/skills/usecase/SKILL.md` — file layout, frontmatter schemas, wiki update protocol.
- `${CLAUDE_PLUGIN_ROOT}/authoring/usecase-abstraction-guard.md` — banned implementation terms.
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

When extraction surfaces an architecture / domain / NFR concern, emit a review item targeting the upstream wiki and continue the autonomous run — UC drafts are independently meaningful. Domain Model itself is **out of scope** — domain extraction lives in `/a4:domain` and is recommended in the final summary.

## Autonomous Decision Rules

Apply the rules in `references/autonomous-decision-rules.md` consistently across composition, revision, and exclusion. No user interaction is permitted — autonomous output is always `status: draft` and promotion is user-driven.

## Non-Goals

- Do not write an aggregated `a4/<topic>.usecase.md` file. All output is per-UC + wiki pages.
- Do not maintain per-topic or per-slug file naming. `a4/` is a single workspace — filenames carry no topic.
- Do not write a `history.md` file. Per-UC `## Log` sections plus git history cover audit needs.
- Do not create GitHub Issues — `a4/` replaces that role.
