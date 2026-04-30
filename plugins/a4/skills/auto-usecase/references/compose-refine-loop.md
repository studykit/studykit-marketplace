# Step 3: Compose + Refine Loop

All work in this step happens via subagents. The main session orchestrates.

## Agents

- **Composer** — `Agent(subagent_type: "a4:usecase-composer")`. Writes / extends the workspace wiki pages and per-UC files.
- **Reviewer** — `Agent(subagent_type: "a4:usecase-reviewer")`. Emits per-finding review items.
- **Reviser** — `Agent(subagent_type: "a4:usecase-reviser")`. Walks open review items and applies fixes.
- **Explorer** — `Agent(subagent_type: "a4:usecase-explorer")`. Surfaces new-perspective UC candidates.

Pass each subagent the **absolute `a4/` path**, the shared reference paths (see SKILL.md "Shared References for Subagents"), and any iteration-specific inputs.

## Step 3a: Compose

Spawn the composer:

```
Agent(subagent_type: "a4:usecase-composer", prompt: """
Workspace: <absolute path to a4/>
Mode: new | expansion                          # based on resume detection
User idea: <raw input from Step 1, or file path>
Research reports: <paths to a4/research/*.md (optional)>
Code analysis: <path to a4/research/code-analysis-initial.md, if it exists>
Shared refs: <list of reference file paths>
Growth iteration: <N>

For new mode: create context.md + actors.md + per-UC files from scratch.
For expansion mode: read existing UCs, preserve them, and write additional UC
files / wiki entries for new candidates.

Return a summary listing UC ids written, excluded candidates, and any open
questions emitted as kind: question review items.
""")
```

The composer:

- Writes `a4/context.md` with `type: context`, `updated`, an `## Original Idea` section quoting the input and a `## Problem Framing` section.
- Writes `a4/actors.md` with `type: actors`, `updated`, a `## Roster` section containing the Actors table.
- Allocates ids via `allocate_id.py` and writes one `a4/usecase/<id>-<slug>.md` per UC.
- Writes NFRs to `a4/nfr.md` if any are surfaced.
- Does **not** write `a4/domain.md`. Domain Model authorship belongs to `/a4:domain` (per `../../../workflows/wiki-authorship.md`). The final summary recommends running `/a4:domain` after auto-usecase finishes.
- Emits `kind: question` review items for unresolvable ambiguities.
- Never rewrites previously confirmed UC files without cause.

## Step 3b: Verify Write

The composer writes directly. Do **not** read the files back in the main session — section completeness is the composer's responsibility. Use the returned summary to confirm UC count.

## Step 3c: Quality Loop (inner)

Repeat up to 3 rounds. Each round:

1. Spawn the reviewer per `usecase/authoring/review-report.md`. It writes per-finding review items into `a4/review/<id>-<slug>.md` (via `allocate_id.py`) and returns:

   ```
   verdict: ALL_PASS | NEEDS_REVISION
   passed: M / N
   items_written: [ids]
   domain_model: OK | NEEDS_REVISION | NOT_YET_CREATED
   completeness: SUFFICIENT | INCOMPLETE
   ```

2. If `verdict == ALL_PASS`, exit the quality loop.

3. Otherwise, spawn the reviser:

   ```
   Agent(subagent_type: "a4:usecase-reviser", prompt: """
   Workspace: <a4/ path>
   Review item ids to address: <list from reviewer summary>
   Shared refs: <paths>

   For each review item (status: open, source: usecase-reviewer): read it, apply
   the Suggestion to the target UC / wiki page, edit the review item's `status:`
   to `resolved` directly (the PostToolUse cascade hook refreshes `updated:`),
   and append a ## Change Logs bullet on each modified wiki page whose basename
   appears in the review's target: list.
   If a finding cannot be applied (e.g., ambiguous), leave status: open and
   capture the reason in conversation notes for the main session to surface.

   Return: revised UC ids, resolved review item ids, deferred review item ids.
   """)
   ```

4. Continue to the next round.

**Maximum:** 3 quality rounds per growth iteration. Remaining findings stay as `status: open` review items for human follow-up.

## Step 3d: Growth Check (outer)

After the quality loop settles:

- `completeness: INCOMPLETE` → the reviewer's findings already include `kind: gap` review items with UC candidates. Feed them back into the composer for another growth iteration.
- `completeness: SUFFICIENT` → spawn the explorer to surface fresh perspectives:

  ```
  Agent(subagent_type: "a4:usecase-explorer", prompt: """
  Workspace: <a4/ path>
  Report path: a4/research/exploration-g<N>.md
  Prior explorations: <paths to a4/research/exploration-*.md if any>
  Shared refs: <paths>
  """)
  ```

  - If the explorer returns UC candidates, feed them back into the composer.
  - If it returns none, exit the outer loop.

**Maximum:** 3 growth iterations. Remaining unexplored perspectives stay as `kind: gap` review items.
