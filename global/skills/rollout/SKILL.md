---
name: rollout
description: "Create and commit a session handoff."
argument-hint: "[additional requirements]"
disable-model-invocation: true
---

# Session Handoff

Create a self-contained handoff for a fresh session. Assume the next session cannot see this conversation.

## Context

- Now: !`date +"%Y-%m-%d_%H%M %Z %z"`
- Ensure handoff directory: !`mkdir -p "$(git rev-parse --show-toplevel)/.handoff"`
- Next handoff number: !`"${CLAUDE_SKILL_DIR}/scripts/next-handoff-number.sh"`
- Git status preview: !`git status --short | head -5`

## Workflow

1. Commit relevant non-handoff work first.
   - Inspect `git status --short` and `git diff --stat`.
   - Stage only changes that clearly belong to this session.
   - Split commits by meaningful unit, such as implementation, tests, docs, cleanup, or unrelated feature slices.
   - Leave unrelated user changes unstaged and mention them in the handoff.
   - Ask only when ownership of a pending change is unclear.
   - Skip this step if there is no relevant non-handoff work; do not create an empty commit.
   - Use specific commit messages, not generic "pre-handoff" labels.
   - Do not include the handoff file in these commits.
2. Choose the handoff path.
   - Write directly under `<repo-root>/.handoff/`; do not create subdirectories.
   - Use the Context-provided handoff number as `<n>`. Do not reimplement numbering.
   - Name the file `<n>-<TIMESTAMP>-<slug>.md`.
   - Use a short kebab-case filename slug for this session's focus. Do not prefix it with `handoff-`.
   - Inspect existing `.handoff/*.md` files before choosing `topic:`.
   - Reuse the prior `topic:` if this session continues an existing thread or began from a specific handoff.
   - Create a new `topic:` only for a genuinely new thread.
   - Never overwrite an existing handoff file; increment `<n>` until the path is unique.
3. Write the handoff in English.
   - Make it self-contained enough for the next session to resume from the file alone.
   - Link durable records, such as wiki pages, issues, PRs, and design docs, when relevant.
   - Do not paste large diffs or changed file contents. Point to `git show` or `git diff` instead.
   - Apply `$ARGUMENTS` as extra user constraints within the relevant sections.
4. Verify and record state.
   - Run relevant tests, linters, validators, or smoke checks when feasible.
   - Record exact commands and outcomes.
   - If checks are skipped or fail, explain why and preserve the risk or failure.
5. Commit the handoff file alone.
   - Commit it after the pre-handoff commits, or on top of `HEAD` if none were needed.
   - Ensure only the new handoff file is in this commit's diff.
   - Use a message like `docs(handoff): snapshot <topic> session state`.

## Additional Requirements

$ARGUMENTS

## File Format

Every handoff file must start with YAML frontmatter, followed by the banner below.

```yaml
---
sequence: <n>                         # same numeric prefix as the filename
timestamp: <TIMESTAMP>                # same timestamp as the filename, e.g. 2026-05-08_1245
timezone: <TIMEZONE>                  # timezone from Context
topic: <topic-slug>                   # long-lived thread identifier
previous: <previous-handoff-filename> # optional; only if this session started from that file
---
```

Frontmatter rules:

- `sequence`, `timestamp`, and `timezone` must match the filename or Context values.
- `topic` identifies the long-lived thread, not this handoff's filename slug.
- Reuse an existing thread's `topic:` verbatim when continuing it.
- Include `previous:` only when this session started from a known handoff file; otherwise omit it.

Banner:

```markdown
> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at <TIMESTAMP>. To record a later state, create a new handoff file via `/handoff` — never edit this one.
```

Use these sections unless one is genuinely irrelevant:

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

Section guidance:

- `Goal`: what the user wanted.
- `Current State`: branch, commit context, and starting handoff when useful.
- `Changes Made`: substantive completed work, with commit references for exact diffs.
- `Key Files`: paths and why they matter.
- `Related Links`: durable project records and their current relevance.
- `Decisions and Rationale`: choices expensive to rediscover.
- `Important Dialog`: concise user constraints, corrections, or preferences.
- `Validation`: commands run and pass/fail/skip status.
- `Known Issues and Risks`: unfinished work, failures, edge cases, or user-visible risks.
- `Next Steps`: prioritized continuation steps.
- `Open Questions`: unresolved product, design, or implementation questions.
- `Useful Commands and Outputs`: only high-signal commands or snippets needed to resume.

## Output

After writing the handoff and creating the required commits, report only:

- handoff file path
- pre-handoff commit SHA(s), or `skipped`
- handoff-only commit SHA
