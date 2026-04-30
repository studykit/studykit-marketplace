# authoring/ — contributor guardrails

> **You are editing a file inside `authoring/`.** Files here are read by workspace authors (humans) and by LLMs editing `<project-root>/a4/**/*.md`. They define the **binding contract** — what's valid in workspace files — not how the plugin enforces it.

## Citation rules (binding)

- Cite `./` siblings only — `./<file>.md` for files in this directory.
- **Never** cite `../scripts/`, `../dev/`, or `../workflows/` in body content. The `**Audience:**` banner at the top of every file is the one allowed exception (it lives in the routing meta, not the content).
- For implementation pointers an author might want (recovery commands, hook behavior), use the **command surface** (`/a4:validate`, `/a4:install-rules`, "the cascade hook") — not script paths.

## When to add a file here

- New `type:` value → add `<type>-authoring.md` (per-type field table + lifecycle + body shape).
- Workspace-wide rule that applies to every file → extend `frontmatter-universals.md` or `body-conventions.md`.
- New artifact taxonomy → extend `artifacts.md`.

## When NOT to add content here

- Plugin implementation, script paths, import graphs → `../dev/`.
- Cross-skill orchestration rules (modes, shapes, iterate, wiki-authorship) → `../workflows/`.
- A single skill's procedure → `../skills/<name>/references/`.

## Tone

Authoring contracts are precise and conservative. State *what* is valid, not *how* it is checked. Avoid hedging language ("usually", "typically") when describing schema. Reserve that voice for `../workflows/` (which describes orchestration choices that vary by context).

The full audience routing and plugin directory layout lives in `../CLAUDE.md`.
