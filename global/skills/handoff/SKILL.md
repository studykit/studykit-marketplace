---
name: handoff
description: "This skill should be used when the user explicitly invokes /handoff. Write a session handoff file so a fresh Claude Code session can resume the current work."
argument-hint: "[additional requirements]"
disable-model-invocation: true
---

# Session Handoff

Write a handoff file that captures everything a fresh Claude Code session needs to continue the current work. Assume the next session will not have access to this conversation.

## Context

- Timestamp: !`date +"%Y-%m-%d_%H%M"`
- Timezone: !`date +"%Z %z"`
- Git status preview: !`git status --short | head -5`

## Task

1. **Update project docs.** Identify anything from this session that belongs in long-lived documentation — architectural decisions, design rationale, new conventions, decision records, CLAUDE.md rules, README changes — and update those docs. This runs in parallel with the handoff, not instead of it: the handoff remains self-contained even if the same knowledge also lives in the proper doc.
2. **Commit relevant non-handoff changes first.** Use the Git status preview in Context as an early signal: if it is empty, there may be no non-handoff work to commit; if it has entries, a pre-handoff commit may be needed. Before deciding, inspect `git status --short` and `git diff --stat`. Stage and commit the doc updates from step 1 along with any other pending working-tree changes that clearly belong to this session. Do not sweep in unrelated user changes just because they are pending. If unrelated changes exist, leave them untouched and mention that they were left out; ask the user only if you cannot tell whether a pending change belongs to this session. If there are no relevant non-handoff changes to commit, skip this step entirely (do not create an empty commit). Use a commit message that describes the substantive change (e.g., `docs(handoff): clarify path selection`), not a generic "pre-handoff" label. The handoff must be its own separate commit (see step 6) so the diff stays clean and the handoff's "state at this moment" snapshot is unambiguous.
3. Decide the handoff path:
   - **Directory**: scope to the area of work. If the session centered on a specific plugin or subtree, use that subtree's `.handoff/` (e.g., `plugins/a4/.handoff/`). If the work spans multiple areas or the scope is unclear, fall back to the repo-root `.handoff/`. Always write the file directly under the chosen `.handoff/` directory; do not create topic or date subdirectories.
   - **Number**: choose `<n>` as one greater than the largest numeric prefix already present in the chosen `.handoff/` directory. Match files named `<number>-*.md`; if none exist, use `1`.
   - **Filename**: `<n>-<TIMESTAMP>-<slug>.md`, where `<slug>` is a short kebab-case summary of this session's focus (e.g., `12-2026-04-24_0233-scripts-and-task-rename.md`, `13-2026-04-24_0317-a4-wiki-issue-model-locked.md`). Do not prefix the slug with `handoff-` — the `.handoff/` directory already identifies the file kind. The filename slug differs from the frontmatter `topic:` field (see File Format): `topic:` is the long-lived thread identifier; the filename slug describes this specific handoff.
   - **Topic discovery**: before choosing a new topic, inspect existing handoff files directly under the chosen `.handoff/` directory. If this session began from an opened handoff file, treat that file as the prior context and reuse its `topic:`. Otherwise, reuse an existing `topic:` value when this session clearly continues that thread; create a new topic only when the session is genuinely unrelated to existing topics. To review prior context for the same thread, sort files with the same `topic:` by `sequence:`.
   - **Never overwrite** an existing handoff file — if the exact path already exists, increment `<n>` until the filename is unique.
4. Write the handoff **in English**. Make it self-contained: the next session should be able to resume from this file alone, without reconstructing prior conversation or broadly exploring the codebase.
5. **Verify and record state.** Run the relevant tests, linters, validators, or smoke checks when feasible. Record exact commands and outcomes in the handoff. If verification is skipped or fails, say why and include the current failure or risk instead of smoothing it over.
6. **Commit the handoff file alone** as a separate commit, on top of the commit from step 2 (or on top of HEAD if step 2 was skipped). Only the new handoff file should be in this commit's diff. Use a commit message that references the `topic:` (e.g., `docs(handoff): snapshot <topic> session state`).

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
- `topic` — the **thread** this session advances, not the specific session focus. Handoffs with the same topic form an implicit thread when sorted by `sequence:`. If a prior handoff on the same thread exists, reuse its `topic:` value verbatim. Choose a new `topic:` only when starting a genuinely new thread.
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
- `Changes Made` — list substantive completed work, not every tiny edit.
- `Key Files` — include paths and why they matter.
- `Decisions and Rationale` — capture choices that would be expensive to rediscover.
- `Important Dialog` — capture short, high-signal user statements, corrections, constraints, or preferences that shaped the work. Quote sparingly and paraphrase when exact wording is not important.
- `Validation` — include commands run and whether they passed, failed, or were skipped.
- `Known Issues and Risks` — preserve unfinished work, failing checks, edge cases, or user-visible risks.
- `Next Steps` — give concrete continuation steps in priority order.
- `Open Questions` — record unresolved product, design, or implementation questions.
- `Useful Commands and Outputs` — include only commands or output snippets that help the next session resume quickly.

## Output

After writing the file and creating the required commits, tell the user the handoff file path, the pre-handoff commit SHA from step 2 (or `skipped`), and the handoff-only commit SHA from step 6. Do not restate the contents.
