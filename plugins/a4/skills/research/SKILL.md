---
name: research
description: "This skill should be used when the user wants to investigate a technical topic or compare alternatives before making a decision. Produces a portable research artifact at `./research/<slug>.md` (project root, outside any a4/ workspace) that decision files or other artifacts can reference. Triggers: 'research', 'investigate', 'look into', 'dig into', 'compare alternatives', 'evaluate options', 'what are the options for', 'how does X work', 'pros and cons of'. Accepts a topic, a comma-separated option list, or a path to a spark-brainstorm / idea file as input. Runs standalone — does not require an a4/ workspace."
argument-hint: <topic, comma-separated options, or path to brainstorm/idea file>
allowed-tools: Read, Write, Edit, Agent, Bash, Glob, WebSearch, WebFetch
---

# Research Facilitator

A standalone research skill. Investigates a technical topic or compares alternatives, and saves the result as a portable markdown artifact at `./research/<slug>.md` (relative to the current working directory / project root). The output is designed to be **cited** by spec files (`a4/spec/<id>-<slug>.md`) or any other artifact via `register_research_citation.py` — not consumed as a decision itself.

Research: **$ARGUMENTS**

## Scope

This skill is **decoupled from any pipeline**. It does not require an `a4/` workspace and does not write to one. Output lives at project root.

Two modes:

| Mode | Input | Output body shape |
|------|-------|-------------------|
| `comparative` | 2+ options to compare | Per-option `### <name>` subsections under `## Options` |
| `single` | One topic / question | Flat `## Findings` section |

## Workflow

| Step | Focus | Procedure |
|------|-------|-----------|
| 1 | Resolve argument + working file path | `references/input-handling.md` |
| 2 | Initial file content (yaml templates per mode) | `references/file-templates.md` |
| 3 | Update discipline (checkpoint writes) | `references/update-discipline.md` |
| 4 | Research orchestration (comparative / single / protocol) | `references/orchestration.md` |
| 5 | Wrap up (final write, status flip, report) | `references/wrap-up.md` |

## Output format

Subsection contract (sources, key findings, raw excerpts): `references/research-report.md`.

## Non-goals

- **No decisions.** Research is objective investigation. The decision is recorded elsewhere via `/a4:spec`, which writes `a4/spec/<id>-<slug>.md` and performs the wiki nudge.
- **No evaluation / scoring.** Weighted scoring, Pugh matrices, SWOT — that's for the decision step.
- **No wiki updates.** Research is workspace-agnostic. Nudges to `a4/architecture.md` etc. happen during `/a4:spec`, not here.
- **No commit.** Leave the file in the working tree.
