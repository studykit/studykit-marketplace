---
timestamp: 2026-04-28_1328
topic: a4-xml-body-format
previous: 2026-04-28_0356_docs-rewrite-for-tag-format.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-28_1328. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## What changed in this session

### Code (committed)

- `plugins/a4/scripts/validate_body.py` — `_scan_sections` is now fence-aware. Inside an open section block, lines that match `OPEN_TAG_RE` / `CLOSE_TAG_RE` shape but sit inside a `` ``` `` or `~~~` fence are no longer mistaken for section boundaries. Top-level scan (between sections) is intentionally unchanged — body-conventions still treats fences outside sections as `body-stray-content`. Implementation mirrors the fence-tracking shape already used by `Body.extract_headings` in `markdown.py`. Commit: `fix(a4): ignore outline tags inside fenced code blocks`.

### Docs

- No doc edits this session. The CDATA-handling note in `references/body-conventions.md §CDATA handling` already promised "Authors should not need to escape anything in body markdown" and "Fenced code blocks are passed through verbatim"; the scanner change closes the gap rather than introducing a new rule. Adding a "tags-inside-fences are auto-ignored" sentence was explicitly considered and rejected — it would only add cognitive load for a guarantee authors already had.

## Decisions reached (not yet implemented)

The bulk of the session was a design conversation on **how an LLM should discover and read individual sections of a4 documents** (instead of always Read-ing the whole file). The decisions below are what the next session should execute.

### 1. Discovery channel for plugin → user-project context

Established constraints (from `code.claude.com/docs/en/memory`):

- `plugins/a4/CLAUDE.md` does **not** auto-load in user projects that install the plugin. It is a developer working note, scoped to this repo.
- `<project-root>/.claude/rules/*.md` files **do** auto-load. Files with `paths:` frontmatter are *path-scoped* — they enter context only when Claude reads files matching the glob. This is the native mechanism for "per-type writing guide".
- `references/` files are lazy and require an LLM-side decision to Read. Reliable only when something points at them.
- SessionStart hook `additionalContext` is the only "always-on" channel a plugin can reach in user projects.

### 2. Adopt option B: a `/a4:install-rules` slash command

Plugins cannot directly populate `<project-root>/.claude/rules/`. Three delivery options were weighed (auto-sync via SessionStart hook / install command / lazy references). User chose **option B**: an explicit, opt-in slash command. Rationale: minimum surprise, sym-link based so plugin updates flow through automatically, no automatic mutation of the user's rules directory.

### 3. Consolidate section-enum into the rule mechanism (do NOT add to SessionStart hook)

An earlier branch of the conversation considered injecting a per-type section-enum table via SessionStart `additionalContext`. That was superseded — once the rule mechanism is in place, the same content is delivered via a path-scoped rule that triggers on any `a4/**/*.md` read. Avoiding the duplicate keeps SessionStart hook focused on **dynamic** info (`refresh_implemented_by`, status-consistency mismatches). Section enum is **schema-derived**, hence belongs in a rule + auto-generator + pre-commit triplet (mirrors the existing `generate_status_diagrams.py` pattern).

### 4. Ship `extract_section.py` script alongside the rules

Per-section reading needs a tool. Plan: `plugins/a4/scripts/extract_section.py` reusing `validate_body._scan_sections`, with three modes: `<file> <tag>`, `<file> --list`, `<file> <tag> --json`. The rule file mentions the invocation so LLM learns about it through path-scoped trigger.

## Concrete implementation plan for the next session

The user explicitly endorsed the **infrastructure-first slice** ("recommendation"): build the install command, the section-enum rule, the generator, and the pre-commit check. Per-type *authoring* guides (the substantive content of `a4-<type>-authoring.md`) are deferred to follow-up sessions, one type at a time.

### Files to create

1. **`plugins/a4/rules/a4-section-enum.md`** — generated, not hand-edited. Frontmatter `paths: ["a4/**/*.md"]` so it triggers on any a4 file. Body: human-friendly preamble + the per-type section enum block (one bullet per type, `R{required} O{optional}`). Generator overwrites the body block between sentinel markers.

2. **`plugins/a4/scripts/generate_section_enum.py`** — same shape as `generate_status_diagrams.py`. Reads every `body_schemas/*.xsd` via `xml.etree.ElementTree` (stdlib, no `xmlschema` dep), builds the bullet block, and writes/checks against `plugins/a4/rules/a4-section-enum.md`. CLI: emit (default), `--check` (exit 2 on drift), `--write`. Reuse `body_schemas.all_types()` to enumerate.

3. **`plugins/a4/scripts/extract_section.py`** — modes:
   - `extract_section.py <file> <tag>` → emit section content to stdout (no CDATA, just the markdown).
   - `extract_section.py <file> --list` → emit `<name>  line <N>` per section.
   - `extract_section.py <file> <tag> --json` → structured output for downstream scripts.
   Reuses `validate_body._scan_sections` (same fence-aware semantics now landed). Inline-script header `# /// script` so `uv run` works the same as other a4 scripts.

4. **`plugins/a4/commands/install-rules.md`** — slash command `/a4:install-rules`. Behavior:
   - Resolve project root via `git rev-parse --show-toplevel`. Abort if not in a git repo.
   - For each `${CLAUDE_PLUGIN_ROOT}/rules/*.md`, target path is `<project-root>/.claude/rules/<basename>`.
   - If target absent → create symlink (`ln -s` to plugin source).
   - If target is already a symlink to the same plugin source → skip silently.
   - If target exists as a regular file or symlink to a different target → warn, list it, do not overwrite. User decides.
   - Create `<project-root>/.claude/rules/` if missing.
   - Report `installed: N, skipped: M, conflicted: K` summary.
   - Idempotent.

5. **`plugins/a4/commands/uninstall-rules.md`** — symmetric removal. Only removes symlinks that point into `${CLAUDE_PLUGIN_ROOT}/rules/`. Leaves user-owned files alone. Reports counts.

### Files to modify

6. **`.githooks/pre-commit`** — add a section enum drift trigger. Pattern: when any of `plugins/a4/scripts/body_schemas/*.xsd` or `plugins/a4/rules/a4-section-enum.md` is staged, run `uv run plugins/a4/scripts/generate_section_enum.py --check`. Exit 1 with the same "Fix: ... --write" guidance used for status diagrams.

7. **`plugins/a4/CLAUDE.md`** — short pointer noting (a) `extract_section.py` exists for per-section reads, (b) `plugins/a4/rules/` ships path-scoped rules and `/a4:install-rules` symlinks them into `<project-root>/.claude/rules/`, (c) `a4-section-enum.md` is generator-owned. This block is for the plugin developer audience (not user projects). Likely fits near the existing "Skill-generated frontmatter is script-managed" paragraph.

### Files explicitly NOT to create yet

- `plugins/a4/rules/a4-spec-authoring.md`, `a4-usecase-authoring.md`, `a4-task-authoring.md`, etc. — the per-type authoring guides. Deferred to follow-up sessions because the content has to be extracted from the corresponding `plugins/a4/skills/<type>/SKILL.md` and `references/` chapters, and is best reviewed type-by-type.

### Sample SessionStart payload (reference only — NOT to ship)

For context, the section-enum block that would have gone into SessionStart `additionalContext` (now belongs in the rule file body instead):

```markdown
Folder = `type:` (`usecase/`, `task/`, `spec/`, `review/`, `idea/`, `archive/`).
Wiki pages: `type:` matches basename (`actors.md` → `type: actors`, etc.).
`spark/<...>.brainstorm.md` → `type: brainstorm`.

Per-type body sections (from `body_schemas/<type>.xsd` — R required, O optional;
unknown kebab-case tags also accepted via openContent):

- actors        — R{roster} O{change-logs}
- architecture  — R{components, overview, technology-stack, test-strategy} O{change-logs, component-diagram, external-dependencies}
- bootstrap     — R{environment, launch, verify} O{change-logs}
- brainstorm    — R{ideas} O{change-logs, notes}
- context       — R{original-idea, problem-framing} O{change-logs, screens}
- domain        — R{concepts} O{change-logs, relationships, state-transitions}
- idea          — R{} O{change-logs, log, notes, why-this-matters}
- nfr           — R{requirements} O{change-logs}
- research      — R{context} O{change-logs, cited-by, findings, options}
- review        — R{description} O{change-logs, log}
- roadmap       — R{plan} O{change-logs}
- spec          — R{context, specification} O{change-logs, consequences, decision-log, examples, log, open-questions, rejected-alternatives, research}
- task          — R{acceptance-criteria, description, files, unit-test-strategy} O{change-logs, interface-contracts, log, why-discarded}
- usecase       — R{expected-outcome, flow, goal, situation} O{change-logs, dependencies, error-handling, log, validation}

Read one section instead of the whole file:
  uv run "${CLAUDE_PLUGIN_ROOT}/scripts/extract_section.py" <file> <tag|--list>
```

This text was generated live in-session by walking each XSD with `xml.etree.ElementTree` and reading `xs:all/xs:element` `name` and `minOccurs`. The generator script must reproduce it deterministically.

## Pointers / context the next session needs

- **Fence-handling implementation** for reuse: `plugins/a4/scripts/validate_body.py:78-130` shows the fence-state tracking shape inside `_scan_sections`. The same `FENCE_RE = re.compile(r"^(\`{3,}|~{3,})")` and `lstrip()` + `startswith(fence)` toggle is what `extract_section.py` should reuse (preferably by importing `_scan_sections` directly rather than duplicating).
- **Existing generator pattern** to mirror: `plugins/a4/scripts/generate_status_diagrams.py` (modes `emit`/`--check`/`--write`, `_block_pattern` regex anchored on heading + fenced block, drift detection in `find_drifts`).
- **Existing pre-commit drift trigger** to mirror: `.githooks/pre-commit` lines 127-143 (a4 status-diagram drift block).
- **XSD section discovery**: every XSD has `<xs:element name="<type>">` at root, and sections live as `<xs:element name="<section>" minOccurs="0|1">` inside. `xml.etree.ElementTree` is sufficient; no need for `xmlschema` (heavy import).
- **SessionStart hook current shape**: `plugins/a4/scripts/a4_hook.py:319-346` (`_session_start`) shows the `additionalContext` emission pattern. It is **not** to be extended this round — confirm before adding.
- **Plugin command location**: existing commands live under `plugins/a4/skills/` as SKILL.md (skills, not commands). Commands as a separate primitive may not be present yet — check `plugins/a4/commands/` exists; if not, create it. The `/a4:install-rules` invocation needs to be recognized via the plugin's `plugin.json` command discovery.
- **`plugin.json`**: verify whether commands need explicit registration there or if file presence in `commands/` is enough. If unsure, look at any other plugin in this marketplace that ships commands and copy the convention. Marketplace-level entry in `.claude-plugin/marketplace.json` may also need a version bump per the project CLAUDE.md ("When a new plugin is added or new features are added to an existing plugin, update `.claude-plugin/marketplace.json`").

## What was deliberately left out

- **Workspace layout block** in SessionStart `additionalContext`: dropped after weighing. Folder structure is visible from `ls a4/`; only the folder→type mapping is non-obvious, and that ends up captured in the rule file's preamble anyway.
- **Auto-sync of rules from SessionStart hook (option A)**: rejected. Modifying `<project-root>/.claude/rules/` without explicit user action exceeds the plugin's appropriate authority — rules is a user-owned directory.
- **References-only fallback (option C)**: rejected. Lazy disclosure via reference files relies on LLM judgment to read them; path-scoped rules give a hard guarantee on file match. Once the rule infrastructure exists, references stay as deeper background, not as the discovery surface.

## Open questions for the next session

1. **Symlink portability**: `/a4:install-rules` plans to use `ln -s`. On Windows this requires either developer-mode-enabled symlinks or junctions. Check whether the marketplace targets cross-platform; if Windows is in scope, consider `mklink /J` fallback or document the limitation.
2. **Rule filename collision**: chosen prefix is `a4-` (e.g., `a4-section-enum.md`). If another plugin also installs `a4-...` rules into the same `<project-root>/.claude/rules/`, collisions are silent overwrites of symlink targets. Acceptable risk for now (a4 is the only namespace using `a4-`), but worth a note in the install command's output.
3. **Whether to ship a real authoring guide for one type as proof-of-concept** in the same PR, or keep this PR strictly infrastructure. Recommendation in-conversation was strict infrastructure; revisit if the install command feels untestable without at least one substantive rule file.

## Verification checklist for the next session

After implementing the plan above, before declaring done:

- [ ] `uv run plugins/a4/scripts/generate_section_enum.py --check` exits 0 against the freshly written `a4-section-enum.md`.
- [ ] `uv run plugins/a4/scripts/generate_section_enum.py --write` is a no-op on second run (idempotent).
- [ ] Hand-edit one XSD (add a dummy optional element), re-run `--check`, expect exit 2 with diff. Revert.
- [ ] Hand-edit `a4-section-enum.md`, stage it, attempt `git commit` — pre-commit hook should block with the "Fix: ... --write" guidance. Reset.
- [ ] `uv run plugins/a4/scripts/extract_section.py <some-a4-file> --list` prints a `<name>  line <N>` table.
- [ ] `uv run plugins/a4/scripts/extract_section.py <some-a4-file> <tag>` prints just that section's body (no CDATA, no surrounding tags).
- [ ] Run `extract_section.py` against the fence-test fixture pattern (a section containing a fenced code block whose interior has outline-shaped tags) — confirm extraction is correct, mirroring the validator's fence-aware semantics.
- [ ] In a throwaway test project (or this repo's own a4 if one exists), run the equivalent of `/a4:install-rules`, then `ls -la .claude/rules/` to verify symlinks point at `${CLAUDE_PLUGIN_ROOT}/rules/`.
- [ ] Re-run `/a4:install-rules`: should report all skipped, no-op.
- [ ] Touch a file at `<project>/.claude/rules/a4-section-enum.md` (replace symlink with a regular file): re-run install command, expect a `conflicted` warning, no overwrite. Restore.
- [ ] Run `/a4:uninstall-rules`: only the plugin-sourced symlinks disappear; user-owned files at the same path are untouched.

## Non-goals (still — reaffirm)

- Do **not** extend SessionStart hook with section-enum content. The rule mechanism owns that channel.
- Do **not** auto-install rules. Always opt-in via the slash command.
- Do **not** copy rule files; symlink so plugin updates propagate.
- Do **not** populate `a4-<type>-authoring.md` content in the infrastructure PR — defer to per-type review sessions.
