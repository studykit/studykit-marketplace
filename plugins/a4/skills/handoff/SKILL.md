---
name: handoff
description: "Use only when the user explicitly invokes /a4:handoff. Refresh every touched mid-flight a4 issue-family file's `## Resume` (and `## Log` for narrative events), commit relevant non-handoff work, then create and commit `<repo-root>/.handoff/<n>-...md` only for residual session-level meta that cannot live in touched files, review items, umbrellas, specs/wiki, durable project guidance, or commit messages. If touched files plus git history are enough to resume, skip the handoff file."
argument-hint: "[additional requirements]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# a4 Session Handoff

Leave durable continuation context for a fresh session that cannot see this conversation. Prefer the a4 workspace as the source of truth; create a handoff file only for residual session-level meta.

## Core rules

- Refresh in-file resume context first: for every touched mid-flight issue-family file under `a4/<type>/<id>-<slug>.md`, rewrite `## Resume` so the file alone shows current approach, blocker, open questions, and next step. Append to `## Log` only for narrative-worthy events: decision pivots, blocker resolutions, or approach changes. Follow `${CLAUDE_PLUGIN_ROOT}/authoring/issue-body.md`.
- Wiki pages do not carry `## Resume` / `## Log`; follow `${CLAUDE_PLUGIN_ROOT}/authoring/wiki-body.md` for `## Change Logs`.
- A handoff file is conditional. Write `<repo-root>/.handoff/<n>-...md` only for meta that cannot be folded into touched files, a review item, a common parent / umbrella, a spec or wiki page, durable project guidance, or commit messages.
- When written, the handoff is a session index plus session-only meta. Link to workspace files, wiki sections, commits, and commands; do not restate per-artifact state, issue/wiki bodies, or large diffs.

## Handoff file gate

Decide in two stages; the gate exists to avoid ceremonial duplicate handoffs.

### Stage 1 — fold first

Try each candidate's natural anchor before treating it as a handoff trigger:

| Candidate | Fold target first | Residual that can trigger a handoff |
|-----------|-------------------|--------------------------------------|
| **a4-anchorless work** — production source, build, tooling, config | Parent issue-family file `## Resume` / `## Log` when cleanly anchored; rationale in commit message | Unanchored change whose rationale still matters beyond the commit body |
| **Session-level validation** — `/a4:auto-coding`, tests, lint, type-check, smoke checks | One issue's `## Resume` Blocked-on slot if failing, or `## Log` if narrative-worthy | Genuinely cross-cutting validation whose result matters beyond a re-run |
| **Important user dialog** — session-scoped corrections or constraints | Single-file pivot/resolution in that file's `## Log`; unresolved constraint in that file's `## Resume` Open-questions slot; unresolved finding/gap/question in `a4/review/` (`target: []` for cross-cutting); shared sibling narrative in an umbrella; design/product decision in spec/wiki; long-lived user or project preference in durable project guidance (`CLAUDE.md`, or project memory only when explicitly requested / available) | Session-scoped continuation note with no durable artifact home, too provisional to justify a review/spec/umbrella/wiki/guidance update |
| **Branch / commit state** | Nothing when obvious from `git status` and `git log --oneline origin/main..HEAD` | Non-obvious state: mid-merge, mid-rebase, divergence, or opaque commits |
| **Cross-cutting decision** | Common parent's `## Log`, with inline citations from affected children per `${CLAUDE_PLUGIN_ROOT}/authoring/frontmatter-issue.md` § `parent`; create an umbrella when sibling issue-family files need a shared narrative home; create a review item when the decision exposes a finding/gap/question; create or update spec/wiki when the decision should become durable product/design knowledge | Only session-ordering or handoff-time context that still has no sensible durable anchor after those folds |

### Stage 2 — residual check

Ask: can the next session reach every mid-flight issue's Next Steps slot by opening only the touched workspace files (including any review / umbrella / spec / wiki anchors) plus `git log --oneline origin/main..HEAD` and commit messages?

- If yes, skip the handoff file and report: pre-handoff commit(s) or `skipped`, updated `## Resume` / `## Log` files, and `no session-level meta — handoff file skipped`.
- If no, write a handoff file scoped only to the unreachable residual.

Non-triggers on their own:

- Routine green validation.
- General-guideline `CLAUDE.md` edits that are auto-loaded next session.
- Test-infrastructure or tooling choices that are not future decision forks.
- Background context rederivable from workspace docs and git history.

## Context

- Timestamp: !`date +"%Y-%m-%d_%H%M"`
- Timezone: !`date +"%Z %z"`
- Ensure handoff directory: !`mkdir -p "$(git rev-parse --show-toplevel)/.handoff"`
- Next handoff number: !`"${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/next-handoff-number.sh"`
- Git status preview: !`git status --short | head -10`
- a4 workspace touchpoints (status preview): !`cd "$(git rev-parse --show-toplevel)" && git diff --name-only HEAD~5..HEAD -- 'a4/**' 2>/dev/null | head -20; git status --short -- 'a4/**' 2>/dev/null | head -10`

## Task

1. **Refresh touched mid-flight a4 files before anything else.**
   - Scope: every touched or relied-on mid-flight `a4/<type>/<id>-<slug>.md`. Skip untouched and terminal files (`done`, `discarded`, `superseded`).
   - Rewrite and compact `## Resume` as the current snapshot: Approach / Blocked on / Open questions / Next. Remove stale items; move narrative-worthy history to `## Log`.
   - Keep `## Log` append-only and narrative-only. Do not log routine status changes.
   - Follow `${CLAUDE_PLUGIN_ROOT}/authoring/issue-body.md` for entry content, exclusions, and inline cross-references.
   - For cross-cutting decisions across files with the same `parent:`, record the decision in the parent's `## Log` and inline-cite that parent from each affected child.
   - Include these edits in the pre-handoff workspace commit(s), not the handoff-only commit.

2. **Commit relevant non-handoff changes, split by meaningful unit.**
   - Inspect `git status --short` and `git diff --stat` before deciding.
   - Stage only changes that clearly belong to this session; leave unrelated user changes untouched and mention them in the report. Ask only if ownership is unclear.
   - Split commits by coherent meaning: a4 artifact authoring, wiki updates, implementation source, tests, or unrelated cleanup.
   - Follow the project convention; for a4 files, consult `${CLAUDE_PLUGIN_ROOT}/authoring/commit-message-convention.md`.
   - Skip this step if there are no relevant non-handoff changes. Never include a handoff file in these commits.

3. **Apply the handoff gate.**
   - During steps 1–2, fold all candidates into their natural anchors or commit messages first.
   - After pre-handoff commits, run the Stage 2 residual check. If no residual remains, skip steps 4–7 and report the skipped handoff.

4. **Choose the handoff path when residual exists.**
   - Directory: write directly under repo-root `.handoff/`; never under `a4/` or nested subdirectories.
   - Number: use the Context-provided next number; do not reimplement the scan. If the exact path exists, increment until unique.
   - Filename: `<n>-<TIMESTAMP>-<slug>.md`, with a short kebab-case session-focus slug and no `handoff-` prefix.
   - Topic: inspect existing `.handoff/*.md`. Reuse the prior handoff's `topic:` if this session began from one; otherwise reuse an existing topic only when clearly continuing that thread. Create a new topic only for a genuinely unrelated thread. Sort same-topic files by `sequence:` to review prior context.

5. **Write the handoff in English, scoped to residual meta only.**
   - Link instead of pasting issue-family content, wiki content, per-task current state, large diffs, or changed file contents.
   - Point to commits and commands such as `git show <sha>` / `git diff` for exact changes.

6. **Record verification already run this session.**
   - Capture exact commands and outcomes from `/a4:auto-coding`, project tests, linters, type-checks, smoke checks, or explicit user-provided output.
   - If validation triggered the gate, `Validation` is its primary home. If no verification occurred and the gate triggered for another reason, say so.

7. **Commit the handoff file alone.**
   - Commit only the new handoff file, on top of the pre-handoff commit(s) or current `HEAD` if step 2 was skipped.
   - Use a message referencing `topic:`, e.g. `docs(handoff): snapshot <topic> session state`.

## Additional Requirements

Treat `$ARGUMENTS` as extra emphasis or constraints from the user. Incorporate them into the relevant steps or sections instead of appending them at the end.

$ARGUMENTS

## File Format

Begin every handoff file with YAML frontmatter, then the exact banner below.

### Frontmatter

```yaml
---
sequence: <n>                       # same numeric prefix as the filename, e.g., 12
timestamp: <TIMESTAMP>              # same value as in the filename, e.g. 2026-04-24_0233
timezone: <TIMEZONE>                # e.g., KST +0900
topic: <topic-slug>                 # kebab-case long-lived thread id, e.g., a4-payment-flow-breakdown
previous: <previous-handoff-filename>  # optional; filename only, if this session started from a known handoff
---
```

- `sequence`, `timestamp`, and `timezone` must match the filename / Context values.
- `topic` is the long-lived thread, not the filename's session-focus slug. Reuse an existing same-thread topic verbatim; create a new one only for unrelated work.
- `previous` is optional. Set it only when this session began from a specific handoff file; omit it when uncertain.
- Do not add an a4 `type:` field; handoffs live outside `a4/`.

### Banner

```markdown
> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at <TIMESTAMP>. To record a later state, create a new handoff file via `/a4:handoff` — never edit this one.
```

### Body sections

Emit only sections with real content:

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

Section rules:

- `Goal`: session goal when not obvious from touched files.
- `Current State`: non-obvious branch / commit context, starting handoff, or active a4 skill(s). Drop if ordinary.
- `a4 Workspace Touchpoints`: index only. List each workspace file touched or relied on as `path` → `status:` where applicable → one-line why. Do not restate file contents or current state; the file's own `## Resume` / `## Log` carries that. Drop if no a4 files were touched.
- `Cross-Cutting Changes and Rationale`: substantive source, scaffolding, tooling, build, or config work that has no single a4 anchor. For anchored work, link via Touchpoints and let the anchor carry rationale.
- `Related Wiki and External Links`: durable external links such as issues, PRs, design docs, dashboards, or vendor docs, with why each matters and its handoff-time state.
- `Important Dialog`: session-scoped user corrections or constraints with no durable home after first trying the affected file, a review item, an umbrella, a spec/wiki page, durable project guidance, and commit messages. Do not use this section for long-lived preferences or unresolved findings/gaps/questions; those belong in durable guidance or `a4/review/`.
- `Validation`: exact commands and outcomes already run; include important trailing failure output, trim noisy success output.
- `Known Issues and Risks`: unfinished work, failing checks, edge cases, or user-visible risks not already captured in a review item or one workspace file's `## Resume`.
- `Next Steps`: session-level ordering or non-issue continuation steps, naming a4 entry points (`/a4:auto-coding`, `/a4:breakdown`, `/a4:bug`, `/a4:spec`, `/a4:validate`, etc.). Per-issue next steps stay in that issue's `## Resume`.
- `Open Questions`: unresolved product/design/implementation questions not already captured in a review item or workspace `## Resume`.
- `Useful Commands and Outputs`: only commands, output snippets, `git show` / `git diff` pointers, or expensive-to-rediscover `Glob` / `Grep` patterns that help resume quickly.

## Output

After the run, report only:

**If a handoff file was written:**

1. Handoff file path.
2. Pre-handoff commit SHA(s), or `skipped`.
3. Handoff-only commit SHA.
4. One-line validation summary, or `none recorded`.

**If the handoff file was skipped:**

1. `handoff file: skipped — no session-level meta`.
2. Pre-handoff commit SHA(s), or `skipped`.
3. Touched files whose `## Resume` and, where applicable, `## Log` were updated.

Do not restate the handoff body in the output.
