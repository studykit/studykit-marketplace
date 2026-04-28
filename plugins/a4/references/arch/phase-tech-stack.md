# Phase 1: Technology Stack

Select language, framework, platform, and key libraries for `<technology-stack>` in `architecture.md`.

## Procedure

1. **For each choice, record the rationale.** Lightweight choices: discuss inline and record with a brief rationale. Heavy choices (multiple viable options with significant trade-offs): ask the user:

   > "This seems like a decision worth investigating more deeply. Would you like to run `/a4:research` on the candidates first, then record the conclusion via `/a4:spec` once we've converged?"

2. **Watch for spec-trigger signals during the interview** — multi-option enumeration, trade-off language, user uncertainty, prior-spec references. The full list of signals and the anti-patterns that suppress nudges is in `../spec-triggers.md`.

3. **Codebase detection.** If a codebase already exists, detect the stack from project files (package.json, pyproject.toml, Cargo.toml, lockfiles, framework configs) and confirm with the user before recording.

4. **Write the initial `architecture.md`** at the end of Phase 1 with frontmatter, `<overview>` stub, and the confirmed `<technology-stack>` content.

## Output checklist

- Language + version policy
- Framework + key version constraints
- Runtime / platform target
- Key libraries the architecture depends on (not implementation libraries — only those that shape components, dataflow, or integration)
- Per-choice rationale (one or two sentences each)
