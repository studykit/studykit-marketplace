# authoring/ — contributor guardrails

> **You are editing a file inside `authoring/`.** Files here are read by workspace authors (humans) and by LLMs editing `<project-root>/a4/**/*.md`. They define the **binding contract** — what's valid in workspace files — not how the plugin enforces it.

## Citation rules (binding)

- Cite `./` siblings only — `./<file>.md` for files in this directory.
- Cite `./` siblings (other `authoring/` files) and `../scripts/<script>.py` when naming a script artifact (script *usage*, not implementation — scripts are independently usable, so naming them in prose is fine). **Never** cite `../workflows/`, `../rules/`, `../skills/`, or `../dev/` in body content — those layers consume `authoring/`, so the reverse direction would create a cross-layer dependency. The `**Audience:**` banner at the top of every file is the one allowed exception (it lives in the routing meta, not the content).
- **Use relative paths for shell snippets too** — `uv run ../scripts/<script>.py ...` rather than `${CLAUDE_PLUGIN_ROOT}/scripts/<script>.py ...`. `authoring/` is loaded in contexts where the env var does not expand; the harness resolves the relative path against the doc's filesystem location. The `${CLAUDE_PLUGIN_ROOT}` form is reserved for `../skills/` and `../agents/`.
- For recovery references, you may name the script via its relative path (`../scripts/validate.py --fix`, `../scripts/allocate_id.py`) or describe behavior ("the cascade hook", "the validator"). Do **not** cite skill commands (`/a4:...`) — that creates a cross-layer reference back into `../skills/`. Do **not** describe script implementation (module paths, internal registries, function names) — that belongs in `../dev/`.

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
