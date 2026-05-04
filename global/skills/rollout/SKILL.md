---
name: rollout
description: "This skill should be used when the user explicitly invokes /handoff. It writes a session handoff file so a fresh Claude Code session can resume the current work."
argument-hint: "[additional requirements]"
disable-model-invocation: true
---

# Session Handoff

Write a handoff file that captures everything a fresh Claude Code session needs to continue the current work. Assume the next session will not have access to this conversation.

## Context

- Timestamp: !`date +"%Y-%m-%d_%H%M"`
- Timezone: !`date +"%Z %z"`
- Ensure handoff directory: !`mkdir -p "$(git rev-parse --show-toplevel)/.handoff"`
- Next handoff number: !`"${CLAUDE_SKILL_DIR}/scripts/next-handoff-number.sh"`
- Git status preview: !`git status --short | head -5`

## Task

1. **Commit relevant non-handoff changes first, split by meaningful unit.**
   - Use the Git status preview in Context as an early signal: if it is empty, there may be no non-handoff work to commit; if it has entries, one or more pre-handoff commits may be needed.
   - Before deciding, inspect `git status --short` and `git diff --stat`.
   - Stage and commit pending working-tree changes that clearly belong to this session, splitting them into separate commits by coherent meaning (for example, implementation, tests, docs, cleanup, or unrelated feature slices).
   - Do not sweep in unrelated user changes just because they are pending. If unrelated changes exist, leave them untouched and mention in the handoff that they were left out. Ask the user only if you cannot tell whether a pending change belongs to this session.
   - If there are no relevant non-handoff changes to commit, skip this step entirely — do not create an empty commit.
   - Use commit messages that describe each substantive change, not generic "pre-handoff" labels.
   - Do **not** include the handoff file in this commit. The handoff file must be committed separately in its own commit (see step 5) so the diff stays clean and the handoff's "state at this moment" snapshot is unambiguous.
2. Decide the handoff path:
   - **Directory**: always write the file directly under the repo-root `.handoff/` directory (`<repo-root>/.handoff/`). Do not create plugin, topic, or date subdirectories.
   - **Number**: use the value already produced by *Next handoff number* in Context as `<n>`. The bundled `scripts/next-handoff-number.sh` resolves the repo root and returns one greater than the largest existing `<number>-*.md` prefix in `<repo-root>/.handoff/` (or `1` if none). Do not reimplement the scan inline.
   - **Filename**: `<n>-<TIMESTAMP>-<slug>.md`, where `<slug>` is a short kebab-case summary of this session's focus (e.g., `12-2026-04-24_0233-scripts-and-task-rename.md`, `13-2026-04-24_0317-a4-wiki-issue-model-locked.md`). Do not prefix the slug with `handoff-` — the `.handoff/` directory already identifies the file kind. The filename slug differs from the frontmatter `topic:` field (see File Format): `topic:` is the long-lived thread identifier; the filename slug describes this specific handoff.
   - **Topic discovery**: before choosing a new topic, inspect existing handoff files directly under `<repo-root>/.handoff/`. If this session began from an opened handoff file, treat that file as the prior context and reuse its `topic:`. Otherwise, reuse an existing `topic:` value when this session clearly continues that thread; create a new topic only when the session is genuinely unrelated to existing topics. To review prior context for the same thread, sort files with the same `topic:` by `sequence:`.
   - **Never overwrite** an existing handoff file — if the exact path already exists, increment `<n>` until the filename is unique.
3. Write the handoff **in English**. Make it self-contained: the next session should be able to resume from this file alone, without reconstructing prior conversation or broadly exploring the codebase. When related wiki pages, GitHub issues, pull requests, or other durable project records exist, link to them so the next session can follow the live source. Do not paste changed file contents or large diffs into the handoff; tell the next session to inspect the relevant commits with `git show` / `git diff` for exact file changes.
4. **Verify and record state.** Run the relevant tests, linters, validators, or smoke checks when feasible. Record exact commands and outcomes in the handoff. If verification is skipped or fails, say why and include the current failure or risk instead of smoothing it over.
5. **Commit the handoff file alone** as a separate commit, on top of the pre-handoff commit(s) from step 1 (or on top of HEAD if step 1 was skipped). Only the new handoff file should be in this commit's diff. Use a commit message that references the `topic:` (e.g., `docs(handoff): snapshot <topic> session state`).

## Additional Requirements

Treat `$ARGUMENTS` as extra emphasis or constraints from the user (e.g., "focus on the auth refactor", "include the failing test outputs verbatim"). Incorporate these into the relevant sections rather than tacking them on at the end.

$ARGUMENTS

## File Format

Every handoff file must begin with YAML frontmatter followed by a "do not edit" banner.

### Frontmatter

```yaml
---
sequence: <n>                       # same numeric prefix as the filename, e.g., 12
timestamp: <TIMESTAMP>              # same value as in the filename, e.g. 2026-04-24_0233
timezone: <TIMEZONE>                # e.g., KST +0900
topic: <topic-slug>                 # kebab-case identifier for the long-lived thread this handoff belongs to (e.g., a4-redesign)
previous: <previous-handoff-filename>  # optional; filename of the handoff this session started from, if known
---
```

- `sequence` — must match the numeric prefix in the filename.
- `timestamp` — must match the timestamp in the filename.
- `timezone` — must match the timezone captured in Context.
- `topic` — the **thread** this session advances, not the specific session focus. Handoffs with the same topic form an implicit thread when sorted by `sequence:`. If a prior handoff on the same thread exists, reuse its `topic:` value verbatim. Choose a new `topic:` only when starting a genuinely new thread. Note: this is distinct from the filename slug, which describes only the current session focus (see Task step 2 *Filename*).
- `previous` — optional. If this session began by opening or following a specific handoff file, set `previous:` to that filename only, not a path. Omit the field entirely if there was no specific starting handoff or if it is uncertain; do not infer it just because another file has the same `topic:`.

### Banner

Immediately after the frontmatter, include this banner so future sessions know not to edit the file:

```markdown
> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at <TIMESTAMP>. To record a later state, create a new handoff file via `/handoff` — never edit this one.
```

### Body

Below the banner, adapt the document to the session, but include these sections unless one is genuinely irrelevant:

```markdown
## Goal
## Current State
## Changes Made
## Key Files
## Related Links
## Decisions and Rationale
## Important Dialog
## Validation
## Known Issues and Risks
## Next Steps
## Open Questions
## Useful Commands and Outputs
```

- `Goal` — explain what the user was trying to accomplish.
- `Current State` — summarize what is true now, including branch/commit context and the starting handoff file when useful.
- `Changes Made` — list substantive completed work, not every tiny edit. Summarize behavior and intent; for exact file contents, point to the relevant commit(s) and `git diff` / `git show` commands instead of copying the diff.
- `Key Files` — include paths and why they matter.
- `Related Links` — link any related wiki pages, GitHub issues, pull requests, design docs, or other durable records. Keep the handoff self-contained even when links are present: explain why each link matters and what state it was in at handoff time.
- `Decisions and Rationale` — capture choices that would be expensive to rediscover.
- `Important Dialog` — capture short, high-signal user statements, corrections, constraints, or preferences that shaped the work. Quote sparingly and paraphrase when exact wording is not important.
- `Validation` — include commands run and whether they passed, failed, or were skipped.
- `Known Issues and Risks` — preserve unfinished work, failing checks, edge cases, or user-visible risks.
- `Next Steps` — give concrete continuation steps in priority order.
- `Open Questions` — record unresolved product, design, or implementation questions.
- `Useful Commands and Outputs` — include only commands or output snippets that help the next session resume quickly. Include `git show` / `git diff` commands for reviewing exact changed file contents when that detail matters.

## Output

After writing the file and creating the required commits, tell the user the handoff file path, the pre-handoff commit SHA(s) from step 1 (or `skipped`), and the handoff-only commit SHA from step 5. Do not restate the contents.
