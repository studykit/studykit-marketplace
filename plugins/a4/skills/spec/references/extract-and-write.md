# Steps 2–5: Extract, Discover Research, Decide Status, Write

## Step 2: Extract the spec

Two input modes:

- **No argument.** Read recent conversation context. Identify the converged shape — what artifact it describes, the prescriptive rules, and any decisions explaining why the shape landed this way. If no clear shape emerged, ask the user which one to record.
- **Short summary / title.** Use `$ARGUMENTS` as a seed; still draw the full content from recent conversation.

Draft a scratch summary covering the fields and sections defined in `../../../references/spec-authoring.md` (`title`, the chosen-shape one-liner that will land in `## Context` and the first `## Decision Log` entry, required `## Context` + `## Specification`, optional sections only when the conversation produced content for them, candidate `supersedes:` if the conversation referenced a predecessor). Do **not** emit placeholder sections.

Present the draft to the user before proceeding. Iterate until the substance is confirmed.

## Step 3: Discover related research tasks

Offer two sources for soft links:

1. **Auto-scan.** `Glob a4/research/*.md`. For each candidate, compare the file's `title:` frontmatter or slug to the spec's title/topic. Propose plausible matches.
2. **User-specified.** If the user named a research task during the conversation, include it verbatim.

Confirm the final list with the user. Empty is fine — specs do not require prior research. The links land in two places (Step 5):

- `related:` frontmatter list (e.g., `related: [research/42-grpc-streaming]`) for frontmatter-level discoverability.
- Inline standard markdown links inside whichever spec section the user wants the citation rendered in (typically `## Decision Log` or `## Rejected Alternatives`).

There is no stored-reverse contract — the research task is not auto-modified, and reverse lookups are derived on demand via grep / `search.py`.

## Step 4: Decide on status via dialogue

Interpret confidence/commitment from the user:

- `active` signals — "this is the spec", "lock this in", "확정", "이걸로 가자".
- `draft` signals — "tentative", "still open", "두고 보자", "아직 여지 있음".

If ambiguous, ask once: *"Activate now, or leave as `draft` for now?"*

**Record the signal — do not write it yet.** The file is always born at `status: draft` in Step 5; Step 6 flips it via the writer if `active` was signaled.

## Step 5: Allocate id, slug, and write the file

1. Allocate id:

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "<project-root>/a4"
   ```

2. Derive slug from the title (kebab-case; ASCII lowercase + CJK pass through; punctuation stripped; collapse hyphens; trim to ~50 chars; fall back to `untitled` if empty).

3. File path: `<project-root>/a4/spec/<id>-<slug>.md`.

4. Use the `Write` tool. Frontmatter shape, required body sections (`## Context`, `## Specification`), optional sections (`## Decision Log`, `## Open Questions`, `## Rejected Alternatives`, `## Consequences`, `## Examples`), and heading-form rules are defined in `../../../references/spec-authoring.md`. Initial `status:` is always `draft`. Capture the chosen-shape one-liner inside `## Context` so Step 6 can quote it as the activate `--reason`. Populate `related:` with the research-task paths confirmed in Step 3 (e.g., `related: [research/42-grpc-streaming]`), and add inline `[research/<id>-<slug>](../research/<id>-<slug>.md)` markdown links inside whichever spec section the citation is most relevant to (commonly `## Decision Log` or `## Rejected Alternatives`).

Report the full file path: "Spec recorded at `<path>` as `draft`."

## Step 6: Activate (if signal was `active`)

Invoke only when the user signaled `active` in Step 4, or the whole invocation is in activate-existing mode.

Edit the spec file's frontmatter `status:` from `draft` to `active` directly (use the `Edit` tool). The PostToolUse cascade hook (`${CLAUDE_PLUGIN_ROOT}/scripts/a4_hook.py`) detects the transition, refreshes `updated:`, and runs the supersedes-chain cascade — every same-family entry in `supersedes:` currently at `active` or `deprecated` is flipped to `superseded` automatically.

The supersedes-cascade behavior is defined in `../../../references/spec-authoring.md` §Lifecycle. After the edit, surface the hook's `additionalContext` to the user (it lists each cascaded predecessor). If the resulting jump is illegal (e.g., `draft → superseded`), the cascade hook silently skips and the Stop-hook safety net surfaces the violation — return to Step 5 and re-author. Post-draft authoring invariants (placeholder tokens etc.) are caught by the frontmatter validator at the Stop hook.
