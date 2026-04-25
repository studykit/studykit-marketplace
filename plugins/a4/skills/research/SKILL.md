---
name: research
description: "This skill should be used when the user wants to investigate a technical topic or compare alternatives before making a decision. Produces a portable research artifact at `./research/<slug>.md` (project root, outside any a4/ workspace) that decision files or other artifacts can reference. Triggers: 'research', 'investigate', 'look into', 'dig into', 'compare alternatives', 'evaluate options', 'what are the options for', 'how does X work', 'pros and cons of'. Accepts a topic, a comma-separated option list, or a path to a spark-brainstorm / idea file as input. Runs standalone — does not require an a4/ workspace."
argument-hint: <topic, comma-separated options, or path to brainstorm/idea file>
allowed-tools: Read, Write, Edit, Agent, Bash, Glob, WebSearch, WebFetch
default_mode: conversational
mode_transitions:
  to_conversational:
    - research scope or option list ambiguous (no comma-separated alternatives, brainstorm/idea file path resolves to multiple candidates)
    - sub-topic prioritization requires user judgment
    - conflicting sources require user-driven adjudication
  to_autonomous:
    - user emits an explicit handoff token to run agent-driven investigation (web search + draft) with no further input expected
    - user invokes /a4:research-review after the artifact is written (mode flips at the skill boundary)
---

# Research Facilitator

A standalone research skill. Investigates a technical topic or compares alternatives, and saves the result as a portable markdown artifact at `./research/<slug>.md` (relative to the current working directory / project root). The output is designed to be **cited** by decision files (`a4/decision/<id>-<slug>.md`) or any other artifact via `related:` / wikilink — not consumed as a decision itself.

Research: **$ARGUMENTS**

## Scope

This skill is **decoupled from any pipeline**. It does not require an `a4/` workspace and does not write to one. Output lives at project root.

Two modes:

| Mode | Input | Output body shape |
|------|-------|-------------------|
| `comparative` | 2+ options to compare | Per-option `### <name>` subsections under `## Options` |
| `single` | One topic / question | Flat `## Findings` section |

## Input handling

Resolve the argument to `(mode, candidates)`:

1. **File path** (`a4/spark/...brainstorm.md`, `a4/idea/<id>-<slug>.md`, any `.md`): read the file, extract candidates. Present to the user: "Here's what I found. Which do you want to research?" The user's answer determines the final list; 2+ items → `comparative`, 1 → `single`.
2. **Comma / `vs` separated list** (e.g., `React vs Svelte vs Vue`, `Postgres, MySQL, SQLite`): parse into a list, confirm, `comparative`.
3. **Single topic or question** (e.g., `gRPC streaming semantics`, `how does RocksDB handle compaction`): confirm the question, `single`.

If the input is ambiguous, ask the user for mode + scope before creating the file.

## Working file path

1. Derive the slug from the topic (kebab-case, ASCII + CJK allowed, trim to ~40 chars).
2. Ensure `./research/` exists; create with `mkdir -p` if missing.
3. Resolve collisions: if `./research/<slug>.md` exists, try `-2`, `-3`, … until free. Tell the user about the suffix.
4. File path: `./research/<slug>.md` relative to the current working directory.

Report the full path as soon as the file is created: "Research file started at `<path>`. It will update as we go."

## Initial file content

Write immediately after mode and candidates are confirmed.

**`comparative` mode:**

```markdown
---
topic: "<topic>"
status: draft       # draft | final
mode: comparative
options: [name-a, name-b, name-c]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: []
---
# <topic>

## Context
<Why this research is needed. What the caller wants to know. 1–3 sentences.>

## Options
*Subsections will appear here as each option is researched.*
```

**`single` mode:**

```markdown
---
topic: "<topic>"
status: draft
mode: single
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: []
---
# <topic>

## Context
<The specific question to answer. 1–3 sentences.>

## Findings
*Findings will appear here as research progresses.*
```

## Update discipline

- **Track each option (or sub-question) via a task.** Mark completed as findings come in. This gives the user a running overview without writing the file after every update.
- **Write at checkpoints only.** Use the `Write` tool to rewrite the entire file with all pending confirmed content. Never partial-edit mid-research. Always preserve prior confirmed content.
- **Checkpoint triggers:** every 2 options researched (`comparative`), major progress increments (`single`), user request, before the finalize step.
- **Bump `updated:`** on every checkpoint write.

## Research orchestration

### Comparative mode

For each option, spawn `Agent(subagent_type: "a4:api-researcher", run_in_background: true)`. Independent options run in parallel. The agent returns its findings as a markdown subsection per `${CLAUDE_SKILL_DIR}/references/research-report.md`. This skill inserts each returned subsection under `## Options` at the next checkpoint.

`api-researcher` is narrowly scoped to API / library / SDK documentation lookup (uses `get-api-docs`, `find-docs`, web fallback). Use it when each option is a concrete API, library, framework, SaaS product, or tool.

When options are **not** API-centric (architectural patterns, conceptual trade-offs, qualitative approaches), research them directly from this skill — `WebSearch` / `WebFetch` (+ `get-api-docs` / `find-docs` where applicable) — and write the subsection yourself in the same format.

### Single mode

No subagent. The skill investigates directly (`WebSearch` / `WebFetch`, and `get-api-docs` / `find-docs` if the topic is API-shaped). Findings accumulate under `## Findings`.

### Protocol (both modes)

1. **Ask before researching.** "I'm about to research [X]. Any specific questions you want me to answer?" Prevents wasted effort.
2. **Avoid duplicate work.** Before launching a new pass on the same option/topic, check the current file for existing content.
3. **Be objective.** Present both strengths and limitations. Do not advocate or recommend — that's for the caller (a decision file or the user).
4. **Cite sources.** Every factual claim carries an inline `([ref](<url>))` citation. Raw excerpts go in `<details><summary>Raw excerpts</summary>…</details>` blocks per the research-report contract.
5. **Match depth across options** (comparative mode) — roughly equal rigor per option.

## Wrapping Up

End only when the user says the research is done. Never conclude unilaterally.

When the user indicates completion:

1. **Final checkpoint write** — ensure every confirmed finding is in the file.
2. **Flip `status: draft → final`** in frontmatter.
3. **Bump `updated:`** to today.
4. **Report the path** and how to reference it:
   - From body prose inside an `a4/decision/<id>-<slug>.md` (Obsidian vault that sees both `a4/` and `./research/`): `[[research/<slug>]]` wikilink — this is the canonical citation form for decisions. `/a4:decision` offers to auto-insert this.
   - Optional review pass: `/a4:research-review ./research/<slug>.md` before relying on it for a decision.

## Non-goals

- **No decisions.** Research is objective investigation. The decision is recorded elsewhere via `/a4:decision`, which writes `a4/decision/<id>-<slug>.md` and performs the wiki nudge.
- **No evaluation / scoring.** Weighted scoring, Pugh matrices, SWOT — that's for the decision step.
- **No wiki updates.** Research is workspace-agnostic. Nudges to `a4/architecture.md` etc. happen during `/a4:decision`, not here.
- **No commit.** Leave the file in the working tree.

## Output format

Follow `${CLAUDE_SKILL_DIR}/references/research-report.md` for the subsection contract (sources, key findings, raw excerpts).
