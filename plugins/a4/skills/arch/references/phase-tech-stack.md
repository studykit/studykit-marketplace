# Phase 1: Technology Stack

Select language, framework, platform, and key libraries for `## Technology Stack` in `architecture.md`.

## Procedure

1. **For each choice, record the rationale.** Lightweight choices: discuss inline and record with a brief rationale. Heavy choices (multiple viable options with significant trade-offs): ask the user:

   > "This seems like a decision worth investigating more deeply. Would you like to author a research task via `/a4:research <topic>` first, then record the conclusion via `/a4:spec` once we've converged?"

2. **Watch for spec-worthy moments during the interview** — multi-option enumeration ("A or B"), trade-off language ("we trade X for Y"), user uncertainty ("not sure", "torn between..."), or references to prior specs ("we decided X before, but now..."). When one fires, pause and offer `/a4:research` then `/a4:spec`. Suppress the nudge for routine choices (variable names, file layout), framework-mandated picks (no real alternative), or post-hoc justification (code already written).

3. **Codebase detection.** If a codebase already exists, detect the stack from project files (package.json, pyproject.toml, Cargo.toml, lockfiles, framework configs) and confirm with the user before recording.

4. **Write the initial `architecture.md`** at the end of Phase 1 with frontmatter, `## Overview` stub, and the confirmed `## Technology Stack` content.

## Output checklist

- Language + version policy
- Framework + key version constraints
- Runtime / platform target
- Key libraries the architecture depends on (not implementation libraries — only those that shape components, dataflow, or integration)
- Per-choice rationale (one or two sentences each)
