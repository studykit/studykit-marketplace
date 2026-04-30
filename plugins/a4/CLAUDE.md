# a4 plugin — contributor notes

These notes apply to anyone editing files under `plugins/a4/`. End-user behavior is documented in `README.md`; this file is for plugin developers.

`a4` ships an Obsidian-flavored wiki + issue tracker that lives in a user's `<project-root>/a4/` workspace. The plugin code itself is split across several directories that play distinct roles — keep edits in the right one.

## Audience routing — read this first

Two distinct audiences read this plugin, and confusing them causes drift:

| Your task | Audience | Read these |
|---|---|---|
| Editing files inside `<project-root>/a4/**/*.md` (workspace authoring) — including LLMs guiding the user | **End user** | `authoring/` only |
| Modifying anything inside `plugins/a4/` itself (this plugin) | **Plugin contributor** | `authoring/` (the contract you must preserve) **plus** `dev/` (implementation references) |

Files clearly mark their audience with a `**Audience:**` banner near the top. If you find yourself reading a `dev/` doc while editing a workspace file, you are probably overshooting — back off to `authoring/`.

## Directory layout

| Path | Role | Audience |
|------|------|----------|
| `authoring/` | **End-user authoring contracts.** Single source of truth for frontmatter schemas, body conventions, commit message form, per-type contracts. Cited by `rules/*.md` (auto-load) and `skills/*/SKILL.md` (skill runtime). Implementation script paths must NOT appear here — use command surface (e.g. `/a4:validate`) or cross-ref into `dev/`. | End users (workspace authors) |
| `rules/` | **Pointer-only rules.** Each file is a thin auto-load shim with `paths:` frontmatter that fires when the user opens or edits a matching `<project-root>/a4/**/*.md` file. Bodies are pointers into `authoring/`, not duplicated content. | Project-rule loader (end-user-facing) |
| `dev/` | **Plugin contributor docs.** Hook conventions, skill-mode taxonomy, pipeline shapes, wiki authorship policy, iterate mechanics, cascade implementation. Source-code anchor lists live here. Read by humans and cited from skills, not auto-loaded into the model. | Plugin contributors |
| `skills/<name>/` | `SKILL.md` is **orchestration only** (preflight + step list + non-goals). Stage-specific procedures live in `skills/<name>/references/*.md`. The cross-cutting authoring contract for the artifact lives in `plugins/a4/authoring/<type>-authoring.md`. | Skill runtime |
| `agents/` | Subagent definitions (reviewers, composers, implementers, workspace-assistant). | Skill runtime |
| `commands/` | `/a4:install-rules` / `/a4:uninstall-rules`. | End users |
| `hooks/` + `scripts/a4_hook.py` | All four hook flows dispatch through one Python entry point. Shell wrappers in `hooks/` only handle SessionStart/SessionEnd file housekeeping. | Hook runtime |
| `scripts/` | Validators, status transitions, allocator, search, drift detector, hook dispatcher, body-schema XSDs. | Skill / hook runtime |

## Recent structural moves (read before editing)

The split between these folders is recent — consult `git log --oneline plugins/a4/` for the full sequence. The defining commits:

- **(this refactor)** — renamed `references/` → `authoring/` and `docs/` → `dev/` to make audience explicit; added `**Audience:**` banners; enforced path purity (script paths only in `dev/`).
- `4e6e826` — split former `references/` (data) from former `docs/` (workflow); slimmed `rules/` to pointers.
- `04ca63a` — slimmed `SKILL.md` files to orchestration; moved skill procedures into `skills/<name>/references/`.
- `a014618` — moved per-type authoring guides (`spec-authoring.md`, `task-authoring.md`, …) from `rules/` to (what was then) `references/`.

If you find yourself duplicating substance across `rules/` and `authoring/`, you are undoing one of these refactors — push the substance into `authoring/` and leave `rules/` as the pointer. If you find script paths or implementation pointers leaking into `authoring/`, push them into `dev/` and leave a single cross-ref behind.

## Required reading before editing

- **Anything touching frontmatter** → `authoring/frontmatter-universals.md` (universal rules), the matching `authoring/<type>-authoring.md` (per-type field table and lifecycle), and `authoring/validator-rules.md` (enforcement). The project-root `CLAUDE.md` calls these out as a hard prerequisite.
- **Anything touching body sections, tag form, change-logs, or links** → `authoring/body-conventions.md`.
- **A new or modified skill** → `dev/skill-modes.md`, `dev/pipeline-shapes.md`, `dev/wiki-authorship.md`. Skills must conform to wiki-authorship; if a `SKILL.md` disagrees, the doc wins and the skill is updated.
- **A new or modified hook** → `dev/hook-conventions.md`. Covers state classification, lifecycle symmetry, in-event ordering, blocking vs non-blocking policy, output-channel choice.
- **An iterate flow (review-item walks)** → `dev/iterate-mechanics.md`.

## Conventions

- **Path references inside this plugin** — choose the form by load context:
  - `rules/*.md` and `authoring/*.md` MUST use relative paths. These files are read in contexts where `${CLAUDE_PLUGIN_ROOT}` is not expanded, so env-var paths resolve to literal strings and break (see commits `350c2a6a`, `7abaaeae`). Inside `rules/` use `../authoring/<file>.md`; inside `authoring/` use `./<file>.md` for siblings and `../<dir>/<file>.md` for other plugin-internal targets.
  - `skills/<name>/**` and `agents/*.md` use `${CLAUDE_PLUGIN_ROOT}/<plugin-internal-path>` for both markdown citations and shell snippets. The env var is expanded at skill-invocation / agent-spawn time. Depth-independence and grep uniformity are the rationale (see commit `a665a92d`).
  - Shell snippets (`uv run`, `bash` code blocks) anywhere ALWAYS use `${CLAUDE_PLUGIN_ROOT}` — they execute under the user's CWD, so relative paths from the file's location would break.
- **`rules/*.md` carries `paths:` frontmatter** that targets `a4/**/*.md` (the user's workspace), not paths inside this plugin. The rule fires when the end user opens an `a4/<type>/*.md` file.
- **Path purity** — `authoring/*.md` must not name `../scripts/*.py` paths directly. Use the command surface (`/a4:validate`, `/a4:install-rules`) or refer authors to `dev/` via a single cross-ref. Implementation pointers belong in `dev/`.
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

If the substance of an authoring rule, schema, or convention is not in `authoring/` or `dev/`, it is not authoritative. Do not infer rules from a single skill's behavior — promote shared behavior into the right reference / doc and have the skill point at it. If you cannot tell whether content belongs in `authoring/` or `dev/`, ask: "Would a workspace author care about this if they never look at this plugin's source?" If yes → `authoring/`. If no (it's about how the plugin enforces something) → `dev/`.
