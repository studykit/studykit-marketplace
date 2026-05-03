# authoring/ — contributor guardrails

## Audiences

- **This file (`CLAUDE.md`):** plugin contributors editing files in this directory.
- **Other files in this directory (`*.md`):** workspace authors (humans) and LLMs editing `<project-root>/a4/**/*.md`. They define the **binding contract** — what's valid in workspace files — not how the plugin enforces it.

The remainder describes the audience and rules for the *other files in this directory*; if you are editing `CLAUDE.md` itself, the contributor-guardrail framing applies to you.

## Audience of files in this directory (single source of truth — do not repeat per-file)

The audience is fixed by location: every `authoring/*.md` shares the same intended readers, so it lives here once instead of as a banner at the top of each file. Do **not** add an `**Audience:**` banner to new or existing files — restating it per-file invites drift, and the banner used to be the only sanctioned cross-layer reference (it named `../dev/`), so removing it also tightens path purity.

- **Primary readers:** workspace authors writing `<project-root>/a4/**/*.md` files, and LLMs editing those files on the user's behalf.
- **Not for plugin contributors.** If you find yourself reading `authoring/` while modifying `plugins/a4/` source, back off — implementation references (hook flow, cascade engine, validator internals, script module paths) live in `../dev/`.
- **Skill runtimes also read this directory.** Skills cite `authoring/` for the frontmatter / body contract — never the reverse. Each skill's own orchestration lives in its own `SKILL.md` + `references/`.
- **Two scope exceptions** worth keeping in mind:
  - `./commit-message-convention.md` extends to **anyone authoring commits derived from a4 artifacts** — workspace editors, plus humans or LLMs implementing or resolving what those artifacts track. Excludes commits inside `plugins/a4/` itself.
  - `./usecase-abstraction-guard.md` is **narrower** — scopes to `<project-root>/a4/usecase/*.md` only and is cited from `./usecase-authoring.md` § Abstraction discipline. Treat it as a sub-section of usecase authoring.

If the audience for a new file does not match any of the above, that is a signal the file probably belongs in a single skill's `../skills/<name>/references/` or in `../dev/`, not here.

## Citation rules (binding)

- Cite `./` siblings only — `./<file>.md` for files in this directory.
- Cite `./` siblings (other `authoring/` files) and `../scripts/<script>.py` when naming a script artifact (script *usage*, not implementation — scripts are independently usable, so naming them in prose is fine). **Never** cite `../skills/` or `../dev/` in body content. With the audience banner gone, this rule has no exceptions: any cross-layer reference in body content is a bug.
- **Use relative paths for shell snippets too** — `../scripts/<script>.py ...` rather than `${CLAUDE_PLUGIN_ROOT}/scripts/<script>.py ...`. `authoring/` is loaded in contexts where the env var does not expand; the harness resolves the relative path against the doc's filesystem location. The `${CLAUDE_PLUGIN_ROOT}` form is reserved for `../skills/` and `../agents/`.
- For recovery references, you may name the script via its relative path (`../scripts/validate.py --fix`, `../scripts/allocate_id.py`) or describe behavior ("the cascade hook", "the validator"). Do **not** cite skill commands (`/a4:...`) — that creates a cross-layer reference back into `../skills/`. Do **not** describe script implementation (module paths, internal registries, function names) — that belongs in `../dev/`.

## When to add a file here

- New `type:` value → add `<type>-authoring.md` (per-type field table + lifecycle + body shape).
- Workspace-wide frontmatter rule (applies to every file) → extend `frontmatter-common.md`.
- Wiki-only frontmatter rule → extend `frontmatter-wiki.md`.
- Issue-only frontmatter rule (id, title placeholders, relationships, status changes and cascades, structural relationship fields) → extend `frontmatter-issue.md`.
- Workspace-wide body rule that applies to every file (heading form, link form) → extend `body-conventions.md`.
- Tooling-managed common field shared by every type → extend `frontmatter-common.md`.
- Issue-only body rule → extend `issue-body.md`.
- Wiki-only body rule → extend `wiki-body.md`.
- New artifact taxonomy → extend `artifacts.md`.
- Cross-type binding rule shared by several types (lifecycle, evidence-readiness gate, etc.) → standalone `<rule-name>.md`. Precedents: `issue-family-lifecycle.md`, `spike-before-task.md`. Per-type docs cite the standalone via `./` for the binding shape.

Pick by audience: `body-conventions.md` is read by everyone editing any `a4/` file, `issue-body.md` is read only by issue authors, `wiki-body.md` is read only by wiki authors. A rule that lands in the wrong file forces the wrong audience to read it. Per-type contracts (`<type>-authoring.md`) point at whichever of the three is relevant — they do not duplicate the contents.

## When NOT to add content here

- Plugin implementation, script paths, import graphs → `../dev/`.
- A single skill's procedure → `../skills/<name>/references/`.

## Tone

Authoring contracts are precise and conservative. State *what* is valid, not *how* it is checked. Avoid hedging language ("usually", "typically") when describing schema.

The full audience routing and plugin directory layout lives in `../CLAUDE.md`.
