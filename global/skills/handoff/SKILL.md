---
name: handoff
description: "This skill should be used when the user explicitly invokes /handoff. Write a session handoff file so a fresh Claude Code session can resume the current work."
argument-hint: "[additional requirements]"
disable-model-invocation: true
---

# Session Handoff

Write a handoff file that captures everything a fresh Claude Code session needs to continue the current work. The current session will end after this.

## Context

- Timestamp: !`date +"%Y-%m-%d_%H%M"`

## Task

1. **Update project docs.** Identify anything from this session that belongs in long-lived documentation — architectural decisions, design rationale, new conventions, decision records, CLAUDE.md rules, README changes — and update those docs. This runs in parallel with the handoff, not instead of it: the handoff remains self-contained even if the same knowledge also lives in the proper doc.
2. **Commit all pending non-handoff changes first.** Before writing the handoff, stage and commit the doc updates from step 1 along with any other pending working-tree changes. If there are no non-handoff changes to commit, skip this step entirely (do not create an empty commit). Use a commit message that describes the substantive change (e.g., `docs(handoff): clarify path selection`), not a generic "pre-handoff" label. The handoff must be its own separate commit (see step 5) so the diff stays clean and the handoff's "state at this moment" snapshot is unambiguous.
3. Decide the handoff path:
   - **Filename**: `<TIMESTAMP>_<slug>.md`, where `<slug>` is a short kebab-case summary of this session's focus (e.g., `scripts-and-task-rename`, `a4-wiki-issue-model-locked`). Do not prefix the slug with `handoff-` — the `.handoff/` directory already identifies the file kind. The filename slug differs from the frontmatter `topic:` field (see File Format): `topic:` is the long-lived thread identifier; the filename slug describes this specific handoff.
   - **Directory**: scope to the area of work. If the session centered on a specific plugin or subtree, use that subtree's `.handoff/` (e.g., `plugins/a4/.handoff/`). If the work spans multiple areas or the scope is unclear, fall back to the repo-root `.handoff/`. Within the chosen handoff directory, nest by topic: the final path is `<handoff-dir>/<topic>/<TIMESTAMP>_<slug>.md`. Create the `<topic>/` subdirectory if it does not yet exist.
   - **Never overwrite** an existing handoff file — if one exists at the same path, append a short suffix (e.g., `_2`).
4. Write the handoff **in English**. Make it self-contained: the next session should be able to resume from this file alone, without reconstructing prior conversation or broadly exploring the codebase.
5. **Commit the handoff file alone** as a separate commit, on top of the commit from step 2 (or on top of HEAD if step 2 was skipped). Only the new handoff file should be in this commit's diff. Use a commit message that references the `topic:` (e.g., `docs(handoff): snapshot <topic> session state`).

## Additional Requirements

Treat `$ARGUMENTS` as extra emphasis or constraints from the user (e.g., "focus on the auth refactor", "include the failing test outputs verbatim"). Incorporate these into the relevant sections rather than tacking them on at the end.

$ARGUMENTS

## File Format

Every handoff file must begin with YAML frontmatter followed by a "do not edit" banner.

### Frontmatter

```yaml
---
timestamp: <TIMESTAMP>              # same value as in the filename, e.g. 2026-04-24_0233
topic: <topic-slug>                 # kebab-case identifier for the long-lived thread this handoff belongs to (e.g., a4-redesign)
previous: <previous-handoff-filename>  # filename (not full path) of the latest prior handoff on the same topic, or omit the field entirely if this is the first
---
```

- `timestamp` — must match the timestamp in the filename.
- `topic` — the **thread** this session advances, not the specific session focus. Handoffs on the same topic link together via `previous:` into a chain, and they share a topic-named subdirectory under the handoff directory. If a prior handoff on the same thread exists, reuse its `topic:` value verbatim (and write into the same `<topic>/` subdirectory). Choose a new `topic:` only when starting a genuinely new thread. **To find candidate prior handoffs**, list the `<handoff-dir>/<topic>/` subdirectory (the topic name is the folder name, so no frontmatter scan is needed).
- `previous` — the filename of the most recent prior handoff in the same `<topic>/` subdirectory (the file with the highest `<TIMESTAMP>` prefix). Omit the field (do not set it to `null` or empty string) if this is the first handoff on the thread. Use just the filename (e.g., `2026-04-24_0143_a4-wiki-issue-model-locked.md`), not a path.

### Banner

Immediately after the frontmatter, include this banner so future sessions know not to edit the file:

```markdown
> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at <TIMESTAMP>. To record a later state, create a new handoff file via `/handoff` — never edit this one.
```

Below the banner, let the session shape the document. Structure and sections are your judgment call.

## Output

After writing the file and creating both commits, tell the user the handoff file path and both commit SHAs (the pre-handoff commit from step 2 and the handoff-only commit from step 5). Do not restate the contents.
