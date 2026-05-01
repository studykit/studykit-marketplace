---
name: handoff
description: "This skill should be used when the user explicitly invokes /a4:handoff. It writes a session handoff file under <repo-root>/.handoff/ that LINKS to in-flight a4 workspace files (task / bug / spike / research / spec / usecase / roadmap / architecture / domain) instead of duplicating their content, so a fresh Claude Code session can resume the current work."
argument-hint: "[additional requirements]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# a4 Session Handoff

Write a handoff file that captures everything a fresh Claude Code session needs to continue the current a4 work. Assume the next session will not have access to this conversation.

This is the a4-flavored variant of the global handoff skill. The a4 workspace already records in-flight work as durable, versioned files under `<project-root>/a4/` — issue-family files (`task/`, `bug/`, `spike/`, `research/`), wiki pages (`usecase/`, `spec/`, `roadmap.md`, `architecture.md`, `domain.md`), and review items. The handoff **links** to those files rather than restating their content, and only captures session-level state that does not belong in any single workspace file.

## Context

- Timestamp: !`date +"%Y-%m-%d_%H%M"`
- Timezone: !`date +"%Z %z"`
- Ensure handoff directory: !`mkdir -p "$(git rev-parse --show-toplevel)/.handoff"`
- Next handoff number: !`"${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/next-handoff-number.sh"`
- Git status preview: !`git status --short | head -10`
- a4 workspace touchpoints (status preview): !`cd "$(git rev-parse --show-toplevel)" && git diff --name-only HEAD~5..HEAD -- 'a4/**' 2>/dev/null | head -20; git status --short -- 'a4/**' 2>/dev/null | head -10`

## Task

1. **Commit relevant non-handoff changes first, split by meaningful unit.**
   - Use the Git status preview in Context as an early signal: empty → likely no non-handoff work to commit; entries → one or more pre-handoff commits may be needed.
   - Before deciding, inspect `git status --short` and `git diff --stat`.
   - Stage and commit pending working-tree changes that clearly belong to this session, splitting them into separate commits by coherent meaning. For a4 work, common splits are: workspace artifact authoring (`a4/<type>/<id>-<slug>.md` writes), wiki updates (`a4/architecture.md`, `a4/domain.md`, `a4/roadmap.md`), implementation source under the project's source tree, tests, and unrelated cleanup.
   - Follow the project's commit-message convention. The a4 workspace's convention lives in `${CLAUDE_PLUGIN_ROOT}/authoring/commit-message-convention.md` — consult it when staging a4 file changes.
   - Do not sweep in unrelated user changes just because they are pending. Leave them untouched and mention in the handoff that they were left out. Ask the user only if you cannot tell whether a pending change belongs to this session.
   - If there are no relevant non-handoff changes to commit, skip this step entirely — do not create an empty commit.
   - Do **not** include the handoff file in this commit. The handoff file must be committed separately in its own commit (see step 5).
2. Decide the handoff path:
   - **Directory**: always write the file directly under the repo-root `.handoff/` directory (`<repo-root>/.handoff/`). Do not create plugin, topic, or date subdirectories. The handoff file lives outside `<project-root>/a4/` because it is a session snapshot, not a typed workspace artifact — placing it under `a4/` would trip the validator (which expects every `a4/**/*.md` to declare a known `type:` per `${CLAUDE_PLUGIN_ROOT}/authoring/frontmatter-universals.md`).
   - **Number**: use the value already produced by *Next handoff number* in Context as `<n>`. The bundled `scripts/next-handoff-number.sh` resolves the repo root and returns one greater than the largest existing `<number>-*.md` prefix in `<repo-root>/.handoff/` (or `1` if none). Do not reimplement the scan inline.
   - **Filename**: `<n>-<TIMESTAMP>-<slug>.md`, where `<slug>` is a short kebab-case summary of this session's focus (e.g., `12-2026-04-24_0233-task-17-search-history.md`, `13-2026-04-24_0317-roadmap-cycle-3-replan.md`). Do not prefix the slug with `handoff-` — the `.handoff/` directory already identifies the file kind. The filename slug differs from the frontmatter `topic:` field (see File Format): `topic:` is the long-lived thread identifier; the filename slug describes this specific handoff.
   - **Topic discovery**: before choosing a new topic, inspect existing handoff files directly under `<repo-root>/.handoff/`. If this session began from an opened handoff file, treat that file as the prior context and reuse its `topic:`. Otherwise, reuse an existing `topic:` value when this session clearly continues that thread; create a new topic only when the session is genuinely unrelated to existing topics. To review prior context for the same thread, sort files with the same `topic:` by `sequence:`.
   - **Never overwrite** an existing handoff file — if the exact path already exists, increment `<n>` until the filename is unique.
3. Write the handoff **in English**. Make it self-contained for *session-level* meta — branch state, cross-cutting decisions, dialog excerpts, validation results, the next-step plan — but **link** rather than restate any content already captured in an `a4/` workspace file. The next session opens the handoff, follows the links into the workspace, and reads the live source. Do not paste:
   - Issue-family file content (description, files table, AC, unit-test strategy) — link to `a4/task/<id>-<slug>.md`, `a4/bug/<id>-<slug>.md`, etc. instead.
   - Wiki section content (architecture decisions, UC flows, domain definitions) — link to the wiki page (and section anchor when useful).
   - Large diffs or changed file contents — point to the relevant commits and `git show` / `git diff` commands.
4. **Record validation state — do not run `/a4:validate` from this skill.** A workspace-wide validate sweep walks every `a4/**/*.md` and inflates the handoff session's context budget; this skill must not trigger it. Instead, capture verification work the user already produced this session — `/a4:run` test-runner output, project tests / linters, an explicit `/a4:validate` invocation the user requested. Record the exact commands and outcomes. If nothing was verified this session, say so explicitly under `Validation` rather than smoothing it over. Run `/a4:validate` (or `validate.py`) here only when the user explicitly asks for it via `$ARGUMENTS`.
5. **Commit the handoff file alone** as a separate commit, on top of the pre-handoff commit(s) from step 1 (or on top of HEAD if step 1 was skipped). Only the new handoff file should be in this commit's diff. Use a commit message that references the `topic:` (e.g., `docs(handoff): snapshot <topic> session state`).

## Additional Requirements

Treat `$ARGUMENTS` as extra emphasis or constraints from the user (e.g., "focus on the cycle-3 replan", "run /a4:validate and include the output", "include the failing test output verbatim"). Incorporate these into the relevant sections rather than tacking them on at the end. Running `/a4:validate` from this skill is opt-in via this channel; the default flow does not invoke it.

$ARGUMENTS

## File Format

Every handoff file must begin with YAML frontmatter followed by a "do not edit" banner.

### Frontmatter

```yaml
---
sequence: <n>                       # same numeric prefix as the filename, e.g., 12
timestamp: <TIMESTAMP>              # same value as in the filename, e.g. 2026-04-24_0233
timezone: <TIMEZONE>                # e.g., KST +0900
topic: <topic-slug>                 # kebab-case identifier for the long-lived thread this handoff belongs to (e.g., a4-cycle-3-roadmap)
previous: <previous-handoff-filename>  # optional; filename of the handoff this session started from, if known
---
```

- `sequence` — must match the numeric prefix in the filename.
- `timestamp` — must match the timestamp in the filename.
- `timezone` — must match the timezone captured in Context.
- `topic` — the **thread** this session advances, not the specific session focus. Handoffs with the same topic form an implicit thread when sorted by `sequence:`. If a prior handoff on the same thread exists, reuse its `topic:` value verbatim. Choose a new `topic:` only when starting a genuinely new thread. Note: this is distinct from the filename slug, which describes only the current session focus (see Task step 2 *Filename*).
- `previous` — optional. If this session began by opening or following a specific handoff file, set `previous:` to that filename only, not a path. Omit the field entirely if there was no specific starting handoff or if it is uncertain; do not infer it just because another file has the same `topic:`.

The handoff frontmatter intentionally **omits** the a4 workspace `type:` field — handoffs live outside `a4/` and are not validated against the a4 frontmatter contract.

### Banner

Immediately after the frontmatter, include this banner so future sessions know not to edit the file:

```markdown
> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at <TIMESTAMP>. To record a later state, create a new handoff file via `/a4:handoff` — never edit this one.
```

### Body

Below the banner, adapt the document to the session, but include these sections unless one is genuinely irrelevant:

```markdown
## Goal
## Current State
## a4 Workspace Touchpoints
## Cross-Cutting Changes and Rationale
## Related Wiki and External Links
## Important Dialog
## Validation
## Known Issues and Risks
## Next Steps
## Open Questions
## Useful Commands and Outputs
```

- `Goal` — what the user was trying to accomplish this session.
- `Current State` — branch / commit context, the starting handoff file when useful, and which a4 pipeline stage(s) the session is currently in (`usecase` / `domain` / `arch` / `roadmap` / `run` / `bug` / etc.).
- `a4 Workspace Touchpoints` — **the link-first section.** Group by issue family and wiki page, listing every workspace file touched or relied on this session with its **current `status:`** (for issue-family files) and a one-line note on *why this session interacted with it*. Do not restate the file's description, files table, AC, or body — the next session opens the file. Suggested layout:

  ```markdown
  ### Tasks (`a4/task/`)
  - `a4/task/17-search-history.md` — `status: progress`, cycle 2 — coder loop hit a regression in `SearchService`; failing `/a4:run` output noted under Validation.

  ### Bugs (`a4/bug/`)
  - `a4/bug/9-cache-key-collision.md` — `status: pending` — written this session; awaiting `/a4:run`.

  ### Specs and UCs (`a4/spec/`, `a4/usecase/`)
  - `a4/spec/12-cache-key-format.md` — anchor for bug 9; no body changes this session.

  ### Wiki (`a4/architecture.md`, `a4/domain.md`, `a4/roadmap.md`)
  - `a4/roadmap.md` — milestone M3 dependency reordered; see commit `<sha>`.
  ```

  If the workspace was untouched (e.g., a pure source-code session that did not write any `a4/` file), say so explicitly — do not omit the section silently.
- `Cross-Cutting Changes and Rationale` — *only* the substantive work that does **not** belong in any single `a4/` file. Examples: implementation source under `src/` not yet anchored to a task, scaffolding decisions across multiple modules, tooling changes. For changes that *are* captured in an `a4/` file, link to that file from `a4 Workspace Touchpoints` instead. Use this section for the diff narrative, with `git show <sha>` pointers for exact contents.
- `Related Wiki and External Links` — durable links beyond `a4/`: GitHub issues, pull requests, design docs, dashboards, vendor docs. Keep self-contained: explain why each link matters and what state it was in at handoff time.
- `Important Dialog` — short, high-signal user statements, corrections, constraints, or preferences that shaped the work. Quote sparingly; paraphrase otherwise.
- `Validation` — exact commands and outcomes from verification the user already ran this session (e.g., `/a4:run` test-runner output, project tests, an explicit `/a4:validate` invocation). This skill does not run validators on its own — see Task step 4. If nothing was verified this session, say so explicitly. Include trailing failure output verbatim when it matters; trim noisy success output.
- `Known Issues and Risks` — unfinished work, failing checks, edge cases, user-visible risks. If a single workspace file already captures the failure (e.g., a `task` at `status: failing` with a Log entry), link to it and only summarize what cannot be inferred from that file.
- `Next Steps` — concrete continuation steps in priority order. Name the a4 entry point per step (`/a4:run`, `/a4:roadmap`, `/a4:bug`, `/a4:spec`, `/a4:validate`, etc.) so the next session can re-enter the pipeline directly.
- `Open Questions` — unresolved product, design, or implementation questions not already captured as a review item under the relevant wiki page. If the question fits an existing review-item walk, log it there instead and link from this section.
- `Useful Commands and Outputs` — only commands or output snippets that help the next session resume quickly. Include `git show` / `git diff` commands for reviewing exact changed file contents when that detail matters. Include `Glob` / `Grep` patterns the session relied on if they would be expensive to rediscover.

## Output

After writing the file and creating the required commits, tell the user:

1. The handoff file path.
2. The pre-handoff commit SHA(s) from step 1 (or `skipped`).
3. The handoff-only commit SHA from step 5.
4. The validation summary line (e.g., `validation: not run — handoff does not invoke validators by default`, or a one-line summary of checks the user ran this session).

Do not restate the handoff body in the output.
