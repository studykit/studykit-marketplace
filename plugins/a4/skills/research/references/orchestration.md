# Research Orchestration

## Comparative mode

For each option, spawn `Agent(subagent_type: "a4:api-researcher", run_in_background: true)`. Independent options run in parallel. The agent returns its findings as a markdown subsection per `./research-report.md`. This skill inserts each returned subsection inside the `<options>` block at the next checkpoint.

`api-researcher` is narrowly scoped to API / library / SDK documentation lookup (uses `get-api-docs`, `find-docs`, web fallback). Use it when each option is a concrete API, library, framework, SaaS product, or tool.

When options are **not** API-centric (architectural patterns, conceptual trade-offs, qualitative approaches), research them directly from this skill — `WebSearch` / `WebFetch` (+ `get-api-docs` / `find-docs` where applicable) — and write the subsection yourself in the same format.

## Single mode

No subagent. The skill investigates directly (`WebSearch` / `WebFetch`, and `get-api-docs` / `find-docs` if the topic is API-shaped). Findings accumulate inside `<findings>`.

## Protocol (both modes)

1. **Ask before researching.** "I'm about to research [X]. Any specific questions you want me to answer?" Prevents wasted effort.
2. **Avoid duplicate work.** Before launching a new pass on the same option/topic, check the current file for existing content.
3. **Be objective.** Present both strengths and limitations. Do not advocate or recommend — that's for the caller (a decision file or the user).
4. **Cite sources.** Every factual claim carries an inline `([ref](<url>))` citation. Raw excerpts go in `<details><summary>Raw excerpts</summary>…</details>` blocks per the research-report contract.
5. **Match depth across options** (comparative mode) — roughly equal rigor per option.
