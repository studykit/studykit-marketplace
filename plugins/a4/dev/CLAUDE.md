# dev/ — contributor guardrails

## Audiences

- **This file (`CLAUDE.md`):** plugin contributors editing files in this directory.
- **Other files in this directory (`*.md`):** plugin contributors. Files here describe how the plugin enforces the contracts in `../authoring/` (frontmatter / body) and `../workflows/` (skill orchestration). Skills, agents, and rules MUST NOT cite this directory.

Both audiences coincide here, but the split is preserved for parity with `../authoring/CLAUDE.md` and `../workflows/CLAUDE.md`.

If you find a skill or agent citing `../dev/`, the content belongs in `../workflows/` (cross-skill orchestration) or `../authoring/` (workspace contract). Promote it and update the skill cross-ref.

## Citation rules

- May cite anywhere — `../scripts/`, `../authoring/`, `../workflows/`, `../hooks/`, `../skills/`. This is the only directory plugin-internal pointers are allowed.
- Prefer absolute-style anchors with descriptive labels (e.g., "**Cascade engine:** `../scripts/status_cascade.py` — supersedes / discarded / revising primitives") over bare paths.

## When to add a file here

- A new implementation surface that warrants its own jump-table (e.g., a new validator subsystem, a new hook flow, a new long-running script).
- Detailed design rationale for a hook or script that doesn't fit in the script's docstring.

## When NOT to add content here

- Workspace contracts (what fields mean, what's valid) → `../authoring/`.
- Cross-skill orchestration (mode taxonomy, pipeline shapes) → `../workflows/`.
- Per-skill procedure → `../skills/<name>/references/`.

## Tone

Implementation references are jump-tables, not narratives. Lead each entry with the file path; one-liner summary; reserve longer prose for design rationale that belongs nowhere else.

The full audience routing and plugin directory layout lives in `../CLAUDE.md`.
