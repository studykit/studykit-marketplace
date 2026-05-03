# a4 plugin — contributor notes

These notes apply to anyone editing files under `plugins/a4/`. End-user behavior is documented in `README.md`; this file is for plugin developers.

`a4` ships an Obsidian-flavored wiki + issue tracker that lives in a user's `<project-root>/a4/` workspace. The plugin code itself is split across several directories that play distinct roles — keep edits in the right one.

## Audience routing — read this first

Each per-directory `CLAUDE.md` (including this one) is itself for **plugin contributors**; the audience listed below is for the *other `*.md` files* in that directory.

Two distinct audiences read this plugin, and confusing them causes drift:

| Your task | Audience | Read these |
|---|---|---|
| Editing files inside `<project-root>/a4/**/*.md` (workspace authoring), authoring or running an a4 skill (skill runtime — LLM executing a skill), or any other read at runtime | **Workspace / skill runtime** | `authoring/` |
| Modifying anything inside `plugins/a4/` itself (this plugin) | **Plugin contributor** | `authoring/` + `dev/` (plugin internals) |

Each of `authoring/` and `dev/` carries its own `CLAUDE.md` with directory-local contributor guardrails — audience statement, citation rules, "when to add a file here / when not", and tone. Those auto-load alongside this file when you edit anything in the directory; consult them as the binding rule for that directory. (Per-file `**Audience:**` banners that used to live at the top of each `*.md` were removed — the per-directory `CLAUDE.md` is the single source of truth, and a contributor-side hook registered in repo `.claude/settings.json` injects a layer map and per-file audience pointer on first Read/Edit.)

If you find yourself reading a `dev/` doc while editing a workspace file or running a skill, you are probably overshooting — back off to `authoring/`.

a4 skills are **independent**. Each skill is its own entry point with its own preconditions; there is no enforced pipeline order, no pipeline shapes, and no orchestrator skill. The plugin used to host a `pipeline-shapes.md` / `wiki-authorship.md` / `compass` orchestration layer; that layer was retired in v21.0.0. Each skill now describes its own contract and behavior in its own `SKILL.md` + `references/`.

## Directory layout

| Path | Role | Audience |
|------|------|----------|
| `authoring/` | **Workspace / skill-runtime authoring contracts.** Single source of truth for frontmatter schemas, body conventions, commit message form, per-type contracts. Cited by skills/agents at runtime and surfaced to the LLM by the PreToolUse contract-injection hook on the first edit of each a4/*.md per session. Implementation script paths must NOT appear here — use command surface (e.g. `/a4:validate`) or cross-ref into `dev/`. | Workspace authors + skill runtime |
| `dev/` | **Plugin contributor docs.** Hook conventions, cascade implementation, validator implementation, shared procedure design memos (e.g., `iterate-mechanics.md`). Source-code anchor lists live here. Read only when modifying `plugins/a4/` itself. Skills MUST NOT cite `dev/` at runtime — each skill's `references/` is self-contained. | Plugin contributors |
| `skills/<name>/` | `SKILL.md` is **orchestration only** (preflight + step list + non-goals). Stage-specific procedures live in `skills/<name>/references/*.md`. The cross-cutting authoring contract for the artifact lives in `plugins/a4/authoring/<type>-authoring.md`. | Skill runtime |
| `agents/` | Subagent definitions (reviewers, composers, implementers, workspace-assistant). | Skill runtime |
| `hooks/` + `scripts/a4_hook.py` | All hook flows dispatch through one Python entry point. PreToolUse handles two responsibilities on the same a4/*.md gate — pre-status snapshot for the cascade engine and one-shot authoring-contract injection per (file, type) per session. Shell wrappers in `hooks/` only handle SessionStart/SessionEnd file housekeeping. | Hook runtime |
| `scripts/` | Validators, status transitions, allocator, search, drift detector, hook dispatcher, body-schema XSDs. | Skill / hook runtime |

## Recent structural moves (read before editing)

The split between these folders is recent — consult `git log --oneline plugins/a4/` for the full sequence. The defining commits:

- **(v21.0.0 pipeline dismantling)** — retired the orchestration layer. Deleted `workflows/pipeline-shapes.md` (Full / Reverse / Minimal shapes), `workflows/wiki-authorship.md` (cross-skill authorship policy), and the `compass` skill (catalog / next-step recommendation). Moved `workflows/iterate-mechanics.md` to `dev/iterate-mechanics.md` as a contributor design memo (skills now describe their own iterate procedures inline). Renamed `auto-bootstrap` → `auto-scaffold` (scaffold-only) and added a separate `ci-setup` skill that owns the test environment and writes `a4/ci.md` (the new test-execution wiki page; `bootstrap.md` was retired with no migration). Renamed `auto-usecase` → `extract-usecase` and dropped the Reverse-only / Reverse-then-forward sub-variants. Each skill is now an independent entry point.
- **(audience routing refactor)** — renamed `references/` → `authoring/` and `docs/` → `dev/` to make audience explicit; enforced path purity (script paths only in `dev/`); replaced the workspace-rules layer with a PreToolUse contract-injection hook (`scripts/a4_hook.py:_pre_edit`). Per-file `**Audience:**` banners were added then later removed in favor of per-directory `CLAUDE.md` audience statements + a contributor hook (`dev/scripts/contributor_hook.py`, registered in repo `.claude/settings.json`).
- **(skill-modes consolidation)** — retired the per-stage mode table (it was redundant with each `SKILL.md`'s frontmatter). The missing-pair design rationale moved to `dev/skill-mode-design.md` as a contributor design memo.
- `04ca63a` — slimmed `SKILL.md` files to orchestration; moved skill procedures into `skills/<name>/references/`.

If you find script paths or implementation pointers leaking into `authoring/`, push them into `dev/` and leave a single cross-ref behind.

## Required reading before editing

- **Anything touching frontmatter** → `authoring/frontmatter-common.md` (cross-cutting rules), `authoring/frontmatter-wiki.md` (wiki contract), `authoring/frontmatter-issue.md` (issue-side rules — `id`, title placeholders, relationships, status changes and cascades, structural relationship fields), and the matching `authoring/<type>-authoring.md` (per-type field table and lifecycle). The project-root `CLAUDE.md` calls these out as a hard prerequisite. Enforcement messages from `/a4:validate` and the Stop hook are self-explanatory; they cite the same per-type / universals contract.
- **Anything touching body sections, tag form, or links** — pick by audience:
  - Cross-cutting (heading form, link form) → `authoring/body-conventions.md`. (`updated:` is hook-owned per `authoring/frontmatter-common.md` — never hand-edited.)
  - Issue body sections (`## Resume`, `## Log`) → `authoring/issue-body.md`.
  - Wiki body sections (`## Change Logs`, Wiki Update Protocol) → `authoring/wiki-body.md`.
- **A new or modified skill** → the skill's own `SKILL.md` + `references/`. Skills are independent — they describe their own preconditions, inputs, outputs, and behavior. There is no shared orchestration contract to conform to. For the design rationale behind the current skill set (why some pairs are intentionally missing), see `dev/skill-mode-design.md`.
- **A new or modified hook** → `dev/hook-conventions.md`. Covers state classification, lifecycle symmetry, in-event ordering, blocking vs non-blocking policy, output-channel choice.
- **An iterate flow (review-item walks)** → `dev/iterate-mechanics.md` (contributor design memo). Each skill's own `references/iteration-entry.md` is self-contained at runtime; the dev memo is the reference shape for adding a new iterate-using skill.

## Reading discipline — follow delegation arrows

a4 docs form a delegation graph: most contracts live in one file and are pointed at from many. A one-liner that says `see ./X.md`, `→ ./Y.md#section`, or `Companion to ./Z.md` is a **pointer, not a summary you can reason from**. The single source of truth lives at the *target*; the calling document only carries a hook into it.

Before any cross-document conclusion (consistency, conflict, over-listing, "X differs from Y", "minimum requires Z"):

- **Read the target of every delegation arrow you cite.** Examples that recur: issue body sections (`## Resume`, `## Log`) delegate to `authoring/issue-body.md`; universal heading/link/mistake rules delegate to `authoring/body-conventions.md`; issue family lifecycle delegates to `authoring/issue-family-lifecycle.md`; per-skill procedures delegate to `skills/<name>/references/*.md`. Reading the caller's one-liner is **not enough** — open the target.
- **List the files needed before drawing conclusions.** Comparing N docs requires reading all N. Don't read 1–2 and infer the rest.
- **Cite line numbers from files you opened in this session.** If you cannot point at a line, you have not finished reading. Statements like "spec L77 says X" must come from an actual Read in the current session, not from training intuition or a remembered earlier conversation.
- **Label any unread inference.** If you must hypothesize without reading (rare; usually wrong), mark it `(not read; presumed)` and prompt for the read before acting on the inference.

This guards against the recurring failure of reading one authoring file, noticing a cross-reference, and writing a "consistency analysis" without ever opening the referenced file. The `authoring/` ↔ `dev/` separation deliberately keeps each file pointer-rich rather than self-contained, so cross-cutting reasoning **must** chase the pointers.

## Conventions

- **Path references inside this plugin** — choose the form by load context:
  - `authoring/*.md` MUST use relative paths. These files are read in contexts where `${CLAUDE_PLUGIN_ROOT}` is not expanded, so env-var paths resolve to literal strings and break (see commits `350c2a6a`, `7abaaeae`). Inside `authoring/` use `./<file>.md` for siblings and `../scripts/<script>.py` when naming a script artifact in prose (no cross-dir refs to `skills/` or `dev/`).
  - `skills/<name>/**` and `agents/*.md` use `${CLAUDE_PLUGIN_ROOT}/<plugin-internal-path>` for both markdown citations and shell snippets. The env var is expanded at skill-invocation / agent-spawn time. Depth-independence and grep uniformity are the rationale (see commit `a665a92d`).
  - Shell snippets (`uv run`, `bash` code blocks) follow the same rule as their containing directory's path form. In `skills/<name>/**` and `agents/*.md`, use `${CLAUDE_PLUGIN_ROOT}/...` (env var expanded at invocation time). In `authoring/*.md`, use relative paths (`../scripts/<script>.py`) — the harness resolves them against the doc's filesystem location at command run time. Do not mix forms within one directory.
- **Path purity** — strict per-directory citation rules:
  - `authoring/*.md` cites `./` siblings and `../scripts/<script>.py` (script *usage* in prose only — not implementation). Scripts are independently usable, so naming them is fine. NO `../skills/`, `../dev/` — those layers consume `authoring/`; reverse refs invert the dependency.
  - `skills/<name>/**` and `agents/*.md` cite `${CLAUDE_PLUGIN_ROOT}/authoring/` for the workspace contract. NEVER `${CLAUDE_PLUGIN_ROOT}/dev/` — each skill is self-contained at runtime. Citing other skills is allowed (`${CLAUDE_PLUGIN_ROOT}/skills/<other>/...`).
  - `dev/*.md` may cite anything; it is the only directory plugin-internal references are allowed.
  - For author/skill-facing recovery commands, prefer the command surface (`/a4:validate`) over a script path.
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

## Running tests

Validator tests live under `tests/`. They use temp-dir fixtures (no real `a4/` workspace required) and run via `uv run --with pytest --with pyyaml pytest`:

```bash
cd plugins/a4 && uv run --with pytest --with pyyaml pytest tests/        # all tests
cd plugins/a4 && uv run --with pytest --with pyyaml pytest tests/ -v     # verbose
cd plugins/a4 && uv run --with pytest --with pyyaml pytest tests/test_parent_target.py
```

The `tests/conftest.py` injects `scripts/` onto `sys.path` and exposes an `a4_workspace` fixture (a thin `A4Workspace` helper that writes minimal-but-valid frontmatter for any type). New tests should use that fixture rather than re-rolling YAML by hand.

## When in doubt

If the substance of a rule, schema, or convention is not in `authoring/` or `dev/`, it is not authoritative. Do not infer rules from a single skill's behavior — each skill is independent, but shared workspace contracts (frontmatter, body conventions, per-type lifecycle) must live in `authoring/`. To pick the right home, ask:

1. "Would a workspace author or runtime LLM care about this when reading or editing an `a4/` file?" → `authoring/`.
2. "Is this about how the plugin enforces something internally (hook flow, cascade engine, validator module, shared procedure shape)?" → `dev/`.
3. "Is this a single skill's procedure?" → `skills/<name>/references/`.
