---
name: handoff
description: "This skill should be used when the user explicitly invokes /a4:handoff. It first refreshes the `## Resume` snapshot of every mid-flight a4 workspace file the session touched (current approach, current blocker, open questions, next step) so each file alone is enough to continue, optionally appends to `## Log` when the session produced narrative-worthy events (decision pivots, blocker resolutions, approach changes), and then writes a session handoff file under <repo-root>/.handoff/ ONLY for residual session-level meta — meta that cannot be folded into any touched file's `## Resume` / `## Log`, the parent's `## Log`, or this session's commit messages. Candidate triggers (a4-anchorless work, session-level validation results, important user dialog, branch/commit state, cross-cutting decisions) are folded into their natural anchor first; the handoff file captures only what survives that fold. Sessions whose entire substance is reachable from the touched files plus `git log` skip the handoff file."
argument-hint: "[additional requirements]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# a4 Session Handoff

Write a handoff file that captures everything a fresh Claude Code session needs to continue the current a4 work. Assume the next session will not have access to this conversation.

This is the a4-flavored variant of the global handoff skill. The a4 workspace already records in-flight work as durable, versioned files under `<project-root>/a4/` — issue-family files (`task/`, `bug/`, `spike/`, `research/`), wiki pages (`usecase/`, `spec/`, `architecture.md`, `domain.md`), and review items.

Two-part handoff (the handoff file is conditional):

1. **In-file resume context** — for every mid-flight a4 file the session touched, refresh its `## Resume` snapshot so a fresh reader sees current approach, current blocker, open questions, and next step. Where the session produced a narrative-worthy event (a decision pivot, a blocker resolution, an approach change worth remembering), append a dated bullet to `## Log` as well. Per `${CLAUDE_PLUGIN_ROOT}/authoring/issue-body.md`. This is what makes each file self-sufficient for the next session: opening that one file is enough to continue.
2. **Session-level handoff file (conditional)** — a snapshot at `<repo-root>/.handoff/<n>-...md` for state that does not belong in any single workspace file. Created **only when session-level meta exists** (see *Handoff file gate* below). When the entire session's substance fits inside the touched files' `## Resume` / `## Log` updates, skip the handoff file — its only contribution would be ceremonial.

When written, the handoff file is the session index plus session-only meta, and it **links** to workspace files rather than restating their content. Each touched workspace file's `## Resume` carries the per-artifact current state, and its `## Log` carries narrative-worthy events.

### Handoff file gate

The handoff file is the **residual** home for session-level meta — *not* the first-resort home for anything notable. Decide in two stages.

**Stage 1 — Fold candidates into their natural anchor first.** For every candidate below, try to fold it into a workspace file's `## Resume` / `## Log`, the parent's `## Log`, or this session's commit messages *before* treating it as a handoff trigger. Only what genuinely cannot be folded survives to Stage 2.

| Candidate | Fold target (try first) | What stays as residual |
|-----------|-------------------------|------------------------|
| **a4-anchorless work** — production source, build / tooling / config changes | When the work has a clean parent issue-family file, link from its `## Resume` / `## Log` and put rationale in the commit message | Source / tooling change with no parent **and** rationale that matters past the commit body |
| **Session-level validation** — `/a4:auto-coding`, project tests, lint, type-check, smoke verification | When the result is one task's cycle outcome, log under that task (`## Resume` Blocked-on slot if failing, `## Log` if narrative-worthy) | Validation that is genuinely cross-cutting (e.g., full-suite green after a multi-task rebase) **and** the outcome matters to the next session beyond a re-run |
| **Important user dialog** — corrections, constraints, preferences | When the dialog *triggered* a single file's pivot / blocker resolution / approach change, fold into that file's `## Log` as a narrative event per `${CLAUDE_PLUGIN_ROOT}/authoring/issue-body.md`; unresolved constraints go into the file's `## Resume` Open-questions slot | Dialog with no single-file anchor (cross-cutting preference, session-level constraint) |
| **Branch / commit state** | When the state is obvious from `git status` and `git log --oneline origin/main..HEAD`, do nothing | Non-obvious state — mid-merge, mid-rebase, divergent, commits whose meaning is not visible from a glance |
| **Cross-cutting decision** | When the touched files share a `parent:` (possibly cross-type per `${CLAUDE_PLUGIN_ROOT}/authoring/frontmatter-issue.md` § `parent`), record in the parent's `## Log` and inline-cite from each child | A decision that spans genuinely unrelated parents with no common anchor |

**Stage 2 — Check residual.** After Stage 1, ask: *can the next session reach the Next Steps slot of every mid-flight task by opening only the touched workspace files plus `git log --oneline origin/main..HEAD` plus the commit messages?* If yes, skip the handoff file. If no, the unreachable meta is the residual — proceed to write the file scoped to that residual.

**Non-triggers (do not pass the gate on their own).** A handoff file that only carries these is the ceremonial-duplicate failure mode this gate exists to prevent.

- Routine validation green — the next session re-runs anyway.
- General-guideline CLAUDE.md edits that are not session-meta (e.g., a project-wide logging-style refinement) — the file is auto-loaded on the next session.
- Test-infrastructure or tooling choices that are not decision forks affecting future continuation steps.
- Background context the next session can rederive from the task doc and git history.

If no residual survives, skip the handoff file. Report the pre-handoff workspace commit (or `none`), the touched files whose `## Resume` (and `## Log` where applicable) was updated, and "no session-level meta — handoff file skipped".

## Context

- Timestamp: !`date +"%Y-%m-%d_%H%M"`
- Timezone: !`date +"%Z %z"`
- Ensure handoff directory: !`mkdir -p "$(git rev-parse --show-toplevel)/.handoff"`
- Next handoff number: !`"${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/next-handoff-number.sh"`
- Git status preview: !`git status --short | head -10`
- a4 workspace touchpoints (status preview): !`cd "$(git rev-parse --show-toplevel)" && git diff --name-only HEAD~5..HEAD -- 'a4/**' 2>/dev/null | head -20; git status --short -- 'a4/**' 2>/dev/null | head -10`

## Task

1. **Refresh the `## Resume` snapshot (and append to `## Log` when narrative-worthy) of every mid-flight a4 file this session touched, before anything else.** This is the resume-context step — the next Claude Code session must be able to open any one of those files alone and continue the work without your conversation transcript.
   - Scope: every `a4/<type>/<id>-<slug>.md` the session edited or relied on whose `status:` is mid-flight. Skip files that are terminal (`done`, `discarded`, `superseded`) or that were untouched. Wiki pages do not carry `## Resume` / `## Log` — see `${CLAUDE_PLUGIN_ROOT}/authoring/wiki-body.md` for their `## Change Logs` discipline.
   - **`## Resume` is a snapshot — rewrite + compact every edit.** Rewrite the slots (Approach / Blocked on / Open questions / Next) with what is true *now*, and compact every slot per `${CLAUDE_PLUGIN_ROOT}/authoring/issue-body.md` § `## Resume` (remove items no longer in flight or next to do; fold narrative-worthy ones to `## Log`).
   - **`## Log` is append-only and narrative-only:** add a dated bullet only when the session produced an event worth remembering past the current state — a decision pivot, a blocker resolution, an approach change. Routine status moves do not belong here.
   - The contract for entry content, what to write vs. not, and inline cross-references is in `${CLAUDE_PLUGIN_ROOT}/authoring/issue-body.md`. Follow it; do not restate it here.
   - When several touched files share a `parent:` (issue-family parent, possibly cross-type — see `${CLAUDE_PLUGIN_ROOT}/authoring/frontmatter-issue.md` §`parent` and shared narrative), record the cross-cutting decision in the parent's `## Log` and inline-cite the parent path from each affected child's `## Resume` / `## Log` entry. The contract requires the inline citation; without it the parent's narrative is invisible to a session reading a child file alone.
   - These `## Resume` / `## Log` edits are part of the pre-handoff workspace commit produced by step 2 — do **not** put them in the handoff-only commit.
2. **Commit relevant non-handoff changes, split by meaningful unit.**
   - Use the Git status preview in Context as an early signal: empty → likely no non-handoff work to commit; entries → one or more pre-handoff commits may be needed.
   - Before deciding, inspect `git status --short` and `git diff --stat`.
   - Stage and commit pending working-tree changes that clearly belong to this session, splitting them into separate commits by coherent meaning. For a4 work, common splits are: workspace artifact authoring (`a4/<type>/<id>-<slug>.md` writes), wiki updates (`a4/architecture.md`, `a4/domain.md`), implementation source under the project's source tree, tests, and unrelated cleanup.
   - Follow the project's commit-message convention. The a4 workspace's convention lives in `${CLAUDE_PLUGIN_ROOT}/authoring/commit-message-convention.md` — consult it when staging a4 file changes.
   - Do not sweep in unrelated user changes just because they are pending. Leave them untouched and mention in the report that they were left out. Ask the user only if you cannot tell whether a pending change belongs to this session.
   - If there are no relevant non-handoff changes to commit, skip this step entirely — do not create an empty commit.
   - Do **not** include any handoff file in this commit. The handoff file (when created) must be committed separately in its own commit (see step 7).
3. **Apply the handoff file gate (fold-then-residual).** Decide whether to create a handoff file at all.
   - **Stage 1 — fold first.** Walk the candidate table in *Handoff file gate* above and fold each candidate into its natural anchor (workspace file `## Resume` / `## Log`, parent's `## Log`, or commit message) before treating it as a handoff trigger. Folds that affect a workspace file are part of the pre-handoff commit(s) from step 2; folds that affect commit messages must be reflected when you author those commits.
   - **Stage 2 — check residual.** Ask: *can the next session reach the Next Steps slot of every mid-flight task by opening only the touched workspace files plus `git log --oneline origin/main..HEAD` plus the commit messages?* If yes, **skip** steps 4–7 and go straight to *Output*: report the pre-handoff workspace commit SHA(s) (or `skipped` from step 2), the touched files whose `## Resume` (and `## Log` where applicable) was updated, and "no session-level meta — handoff file skipped". If no, the unreachable meta is the residual — proceed to step 4 and scope the handoff file to that residual.
   - Be honest. The failure mode this gate exists to prevent is a ceremonial duplicate — a handoff file that only restates what the task doc and commit messages already say.
4. Decide the handoff path:
   - **Directory**: always write the file directly under the repo-root `.handoff/` directory (`<repo-root>/.handoff/`). Do not create plugin, topic, or date subdirectories. The handoff file lives outside `<project-root>/a4/` because it is a session snapshot, not a typed workspace artifact — placing it under `a4/` would trip the validator (which expects every `a4/**/*.md` to declare a known `type:` per `${CLAUDE_PLUGIN_ROOT}/authoring/frontmatter-common.md`).
   - **Number**: use the value already produced by *Next handoff number* in Context as `<n>`. The bundled `scripts/next-handoff-number.sh` resolves the repo root and returns one greater than the largest existing `<number>-*.md` prefix in `<repo-root>/.handoff/` (or `1` if none). Do not reimplement the scan inline.
   - **Filename**: `<n>-<TIMESTAMP>-<slug>.md`, where `<slug>` is a short kebab-case summary of this session's focus (e.g., `12-2026-04-24_0233-task-17-search-history.md`, `13-2026-04-24_0317-breakdown-payment-flow.md`). Do not prefix the slug with `handoff-` — the `.handoff/` directory already identifies the file kind. The filename slug differs from the frontmatter `topic:` field (see File Format): `topic:` is the long-lived thread identifier; the filename slug describes this specific handoff.
   - **Topic discovery**: before choosing a new topic, inspect existing handoff files directly under `<repo-root>/.handoff/`. If this session began from an opened handoff file, treat that file as the prior context and reuse its `topic:`. Otherwise, reuse an existing `topic:` value when this session clearly continues that thread; create a new topic only when the session is genuinely unrelated to existing topics. To review prior context for the same thread, sort files with the same `topic:` by `sequence:`.
   - **Never overwrite** an existing handoff file — if the exact path already exists, increment `<n>` until the filename is unique.
5. Write the handoff **in English**, scoped to the session-level meta that triggered the gate. **Link** rather than restate any content already captured in an `a4/` workspace file (the next session opens the workspace files for per-artifact narrative; the handoff carries only what does not fit there). Do not paste:
   - Issue-family file content (description, files table, AC, unit-test strategy) — link to `a4/task/<id>-<slug>.md`, `a4/bug/<id>-<slug>.md`, etc. instead.
   - Wiki section content (architecture decisions, UC flows, domain definitions) — link to the wiki page (and section anchor when useful).
   - Per-task current state — that lives in each touched file's `## Resume` now (and narrative-worthy events in `## Log`). The handoff Touchpoints section is an index, not a re-statement.
   - Large diffs or changed file contents — point to the relevant commits and `git show` / `git diff` commands.
6. **Record verification the user already ran this session.** Capture the exact commands and outcomes — `/a4:auto-coding` test-runner output, project tests / linters, anything explicit the user produced. If session-level validation was the gate trigger, this is its primary home. If nothing was verified this session and the gate triggered for some other reason, say so under `Validation` instead of smoothing it over.
7. **Commit the handoff file alone** as a separate commit, on top of the pre-handoff commit(s) from step 2 (or on top of HEAD if step 2 was skipped). Only the new handoff file should be in this commit's diff. Use a commit message that references the `topic:` (e.g., `docs(handoff): snapshot <topic> session state`).

## Additional Requirements

Treat `$ARGUMENTS` as extra emphasis or constraints from the user (e.g., "focus on the cycle-3 replan", "include the failing test output verbatim"). Incorporate these into the relevant sections rather than tacking them on at the end.

$ARGUMENTS

## File Format

Every handoff file must begin with YAML frontmatter followed by a "do not edit" banner.

### Frontmatter

```yaml
---
sequence: <n>                       # same numeric prefix as the filename, e.g., 12
timestamp: <TIMESTAMP>              # same value as in the filename, e.g. 2026-04-24_0233
timezone: <TIMEZONE>                # e.g., KST +0900
topic: <topic-slug>                 # kebab-case identifier for the long-lived thread this handoff belongs to (e.g., a4-payment-flow-breakdown)
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

Below the banner, **emit only the sections whose content actually exists for this session**. The handoff file is session-meta only; per-task current state lives in each touched file's `## Resume` (and narrative-worthy events in `## Log`) and must not be duplicated here.

Available sections (drop any that have no content):

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

- `Goal` — what the user was trying to accomplish this session, if not obvious from the touched files alone.
- `Current State` — branch / commit context, the starting handoff file when useful, and which a4 skill(s) the session has been running (`usecase` / `domain` / `arch` / `breakdown` / `auto-coding` / `bug` / etc.). Drop the section if the branch is at `origin/HEAD` and there is nothing non-obvious to record.
- `a4 Workspace Touchpoints` — **index only.** A flat list of every workspace file touched or relied on this session, each as: file path → current `status:` (for issue-family / UC / spec / review files) → one-line *why this session interacted with it*. Do **not** restate the file's description, files table, AC, body, or current state; per-artifact resume context lives in each file's `## Resume` (per step 1). Group by issue family / wiki page only when the list is long enough to benefit. Suggested layout:

  ```markdown
  ### Tasks (`a4/task/`)
  - `a4/task/17-search-history.md` — `status: progress`, cycle 2 — coder loop hit a regression; details in the file's `## Resume`.

  ### Bugs (`a4/bug/`)
  - `a4/bug/9-cache-key-collision.md` — `status: queued` — written this session; details in the file's `## Resume`.

  ### Wiki
  - `a4/architecture.md` — component boundary clarified for SessionService; see commit `<sha>`.
  ```

  If no a4 files were touched (a4-anchorless session), drop the section entirely — the gate trigger is recorded under the relevant section below (`Cross-Cutting`, `Validation`, etc.).
- `Cross-Cutting Changes and Rationale` — substantive work that does **not** belong in any single `a4/` file. Examples: implementation source under `src/` not yet anchored to a task, scaffolding decisions across multiple modules, tooling changes, build / config edits. For changes that *are* captured in an `a4/` file (single anchor or common parent), link to that file from `a4 Workspace Touchpoints` and the file's `## Resume` (or `## Log` for narrative pivots) carries the rationale; do not duplicate here. Use this section for the diff narrative, with `git show <sha>` pointers for exact contents.
- `Related Wiki and External Links` — durable links beyond `a4/`: GitHub issues, pull requests, design docs, dashboards, vendor docs. Keep self-contained: explain why each link matters and what state it was in at handoff time.
- `Important Dialog` — short, high-signal user statements, corrections, constraints, or preferences that shaped the work and do not naturally belong in any single file's `## Resume` / `## Log`. Quote sparingly; paraphrase otherwise. When the dialog triggered a single file's decision pivot, blocker resolution, or approach change, fold it into that file's `## Log` as a narrative event per `${CLAUDE_PLUGIN_ROOT}/authoring/issue-body.md` instead of recording it here; an unresolved constraint or question given only in conversation belongs in that file's `## Resume` Open-questions slot.
- `Validation` — exact commands and outcomes from verification the user already ran this session (e.g., `/a4:auto-coding` test-runner output, project tests / linters / type-check). Include trailing failure output verbatim when it matters; trim noisy success output. If validation was the gate trigger, this is the primary section.
- `Known Issues and Risks` — unfinished work, failing checks, edge cases, user-visible risks **that are not already captured in a single workspace file's `## Resume`**. When the failure is captured there (e.g., a `task` at `status: failing` whose `## Resume` records the cause and next step), link to that file and *do not* re-summarize.
- `Next Steps` — concrete continuation steps in priority order, **for the session as a whole**. Name the a4 entry point per step (`/a4:auto-coding`, `/a4:breakdown`, `/a4:bug`, `/a4:spec`, `/a4:validate`, etc.). Per-task next steps belong in the task's own `## Resume`; this section captures cross-task ordering or non-task next steps only.
- `Open Questions` — unresolved product, design, or implementation questions not already captured as a review item or in a single workspace file's `## Resume`. If the question fits an existing review-item walk, log it there instead and link from this section.
- `Useful Commands and Outputs` — only commands or output snippets that help the next session resume quickly. Include `git show` / `git diff` commands for reviewing exact changed file contents when that detail matters. Include `Glob` / `Grep` patterns the session relied on if they would be expensive to rediscover.

## Output

After completing the run, tell the user:

**When the gate triggered and a handoff file was written:**

1. The handoff file path.
2. The pre-handoff commit SHA(s) from step 2 (or `skipped`). The `## Resume` / `## Log` updates from step 1 are part of these commit(s) when present.
3. The handoff-only commit SHA from step 7.
4. A one-line validation summary (e.g., a brief recap of checks the user ran this session, or `none recorded`).

**When the gate did not trigger (handoff file skipped):**

1. `handoff file: skipped — no session-level meta`.
2. The pre-handoff commit SHA(s) from step 2 (or `skipped`). The `## Resume` / `## Log` updates from step 1 are part of these commit(s) when present.
3. The list of touched files whose `## Resume` (and `## Log` where applicable) was updated, so the user can confirm the resume context is in place.

Do not restate the handoff body in the output.
