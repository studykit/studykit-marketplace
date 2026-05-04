# dev/ — contributor guardrails

## Audiences

- **This file (`AGENTS.md`) and the colocated `CLAUDE.md` shim:** plugin contributors editing files in this directory.
- **Other files in this directory (`*.md`):** plugin contributors. Files here describe how the plugin enforces the contracts in `../authoring/` (frontmatter / body), document shared procedure shapes that skills implement (e.g., `iterate-mechanics.md`), and capture design rationale for hooks / scripts. Skills, agents, and rules MUST NOT cite this directory at runtime — each skill's `references/` is self-contained, and contributor docs here are for *contributors building or modifying skills*, not for runtime consumption.

If you find a skill or agent citing `../dev/`, the content belongs in `../authoring/` (workspace contract) or directly inlined into the skill's `references/`. Promote it and update the skill cross-ref.

## Citation rules

- May cite anywhere — `../scripts/`, `../authoring/`, `../hooks/`, `../skills/`. This is the only directory plugin-internal pointers are allowed.
- Prefer absolute-style anchors with descriptive labels (e.g., "**Cascade engine:** `../scripts/status_cascade.py` — supersedes / discarded / revising primitives") over bare paths.

## When to add a file here

- A new implementation surface that warrants its own jump-table (e.g., a new validator subsystem, a new hook flow, a new long-running script).
- A shared procedure shape that multiple skills implement, with the contributor-facing rationale (e.g., `iterate-mechanics.md`). Skills inline the procedure in their own `references/`; this file is the design memo.
- Detailed design rationale for a hook or script that doesn't fit in the script's docstring.

## When NOT to add content here

- Workspace contracts (what fields mean, what's valid) → `../authoring/`.
- Per-skill procedure → `../skills/<name>/references/`.

## Tone

Implementation references are jump-tables, not narratives. Lead each entry with the file path; one-liner summary; reserve longer prose for design rationale that belongs nowhere else.

The full audience routing and plugin directory layout lives in `../AGENTS.md` (loaded by the `../CLAUDE.md` shim).
