# a4 plugin — contributor notes

These notes apply to anyone editing files under `plugins/a4/`. End-user behavior is documented in `README.md`; this file is for plugin developers.

`a4` ships an Obsidian-flavored wiki + issue tracker that lives in a user's `<project-root>/a4/` workspace. The plugin code itself is split across several directories that play distinct roles — keep edits in the right one.

## Directory layout

| Path | Role | Audience |
|------|------|----------|
| `references/` | **Substantive data.** Single source of truth for frontmatter schemas, body conventions, commit message form, and per-type authoring contracts. Cited by both `rules/*.md` and `skills/*/SKILL.md`. | Authoring contracts (binding) |
| `rules/` | **Pointer-only rules.** Each file is a thin auto-load shim with `paths:` frontmatter that fires when the user opens or edits a matching `<project-root>/a4/**/*.md` file. Bodies are pointers into `references/`, not duplicated content. | Project-rule loader |
| `docs/` | **Cross-cutting workflow / design docs.** Hook conventions, skill-mode taxonomy, pipeline shapes, wiki authorship policy, iterate mechanics. Read by humans and cited from skills, not auto-loaded into the model. | Plugin developers |
| `skills/<name>/` | `SKILL.md` is **orchestration only** (preflight + step list + non-goals). Stage-specific procedures live in `skills/<name>/references/*.md`. The cross-cutting authoring contract for the artifact lives in `plugins/a4/references/<type>-authoring.md`. | Skill runtime |
| `agents/` | Subagent definitions (reviewers, composers, implementers, workspace-assistant). | Skill runtime |
| `commands/` | `/a4:install-rules` / `/a4:uninstall-rules`. | End users |
| `hooks/` + `scripts/a4_hook.py` | All four hook flows dispatch through one Python entry point. Shell wrappers in `hooks/` only handle SessionStart/SessionEnd file housekeeping. | Hook runtime |
| `scripts/` | Validators, status transitions, allocator, search, drift detector, hook dispatcher, body-schema XSDs. | Skill / hook runtime |

## Recent structural moves (read before editing)

The split between these folders is recent — consult `git log --oneline plugins/a4/` for the full sequence. Three commits define the current shape:

- `4e6e826` — split `references/` (data) from `docs/` (workflow); slimmed `rules/` to pointers.
- `04ca63a` — slimmed `SKILL.md` files to orchestration; moved skill procedures into `skills/<name>/references/`.
- `a014618` — moved per-type authoring guides (`spec-authoring.md`, `task-authoring.md`, …) from `rules/` to `references/`.

If you find yourself duplicating substance across `rules/` and `references/`, you are undoing one of these refactors — push the substance into `references/` and leave `rules/` as the pointer.

## Required reading before editing

- **Anything touching frontmatter** → `references/frontmatter-universals.md` (universal rules), the matching `references/<type>-authoring.md` (per-type field table and lifecycle), and `references/validator-rules.md` (enforcement). The project-root `CLAUDE.md` calls these out as a hard prerequisite.
- **Anything touching body sections, tag form, change-logs, or links** → `references/body-conventions.md`.
- **A new or modified skill** → `docs/skill-modes.md`, `docs/pipeline-shapes.md`, `docs/wiki-authorship.md`. Skills must conform to wiki-authorship; if a `SKILL.md` disagrees, the doc wins and the skill is updated.
- **A new or modified hook** → `docs/hook-conventions.md`. Covers state classification, lifecycle symmetry, in-event ordering, blocking vs non-blocking policy, output-channel choice.
- **An iterate flow (review-item walks)** → `docs/iterate-mechanics.md`.

## Conventions

- **Path references inside this plugin** — choose the form by load context:
  - `rules/*.md` and `references/*.md` MUST use relative paths. These files are read in contexts where `${CLAUDE_PLUGIN_ROOT}` is not expanded, so env-var paths resolve to literal strings and break (see commits `350c2a6a`, `7abaaeae`). Inside `rules/` use `../references/<file>.md`; inside `references/` use `./<file>.md` for siblings and `../<dir>/<file>.md` for other plugin-internal targets.
  - `skills/<name>/**` and `agents/*.md` use `${CLAUDE_PLUGIN_ROOT}/<plugin-internal-path>` for both markdown citations and shell snippets. The env var is expanded at skill-invocation / agent-spawn time. Depth-independence and grep uniformity are the rationale (see commit `a665a92d`).
  - Shell snippets (`uv run`, `bash` code blocks) anywhere ALWAYS use `${CLAUDE_PLUGIN_ROOT}` — they execute under the user's CWD, so relative paths from the file's location would break.
- **`rules/*.md` carries `paths:` frontmatter** that targets `a4/**/*.md` (the user's workspace), not paths inside this plugin. The rule fires when the end user opens an `a4/<type>/*.md` file.
- **Ids are globally monotonic.** Allocate via `scripts/allocate_id.py`; never reuse, never re-pack.
- **Plugin version lives in `.claude-plugin/marketplace.json`**, not in `plugin.json`. Bump the entry when adding a feature (per the project-root `CLAUDE.md`).

## Running plugin scripts

All Python in `scripts/` is invoked via `uv run` — never `python` directly. Examples:

```bash
uv run scripts/validate.py <a4-dir>                       # all checks
uv run scripts/validate.py <a4-dir> <file> [<file> ...]   # file-scoped
uv run scripts/validate.py <a4-dir> --only frontmatter    # one category
uv run scripts/validate.py <a4-dir> --fix [--dry-run]     # supersedes-chain recovery sweep
uv run scripts/validate.py --list-checks                  # registered checks
uv run scripts/search.py <query>
```

Status writes are not done by a CLI: edit `status:` directly and the
PostToolUse cascade hook (`scripts/a4_hook.py`) handles related-file
flips and `updated:` refresh. Cascade primitives live in
`scripts/status_cascade.py`. Use `validate.py --fix` only as a
recovery path for edits that bypassed the hook.

Type hints are required on anything that is not a one-off script.

## When in doubt

If the substance of an authoring rule, schema, or convention is not in `references/` or `docs/`, it is not authoritative. Do not infer rules from a single skill's behavior — promote shared behavior into the right reference / doc and have the skill point at it.
