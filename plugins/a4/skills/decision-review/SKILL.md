---
name: decision-review
description: "This skill should be used when the user has authored (or revised) an `a4/decision/<id>-<slug>.md` file and wants to review and finalize it. Runs the decision-reviewer agent against the file, walks the flagged issues with the user one at a time, applies accepted revisions, nudges affected wiki pages, and transitions `status` from `draft` to `final`. Triggers: 'review my decision', 'finalize decision', 'decision review', 'check my ADR', 'is this decision sound', or after hand-authoring a decision file. Requires an `a4/` workspace."
argument-hint: <path to a4/decision/<id>-<slug>.md>
allowed-tools: Read, Write, Edit, Agent, Bash, Glob
---

# Decision Review & Finalize

Wraps the `decision-reviewer` agent + wiki-nudge protocol into a single wrap-up pass for a hand-authored decision file. Use after drafting or revising an `a4/decision/<id>-<slug>.md` file — this skill does not author decisions, it reviews, revises, and finalizes them.

Target: **$ARGUMENTS**

## Scope

Expects a **drafted decision file** at `<workspace>/a4/decision/<id>-<slug>.md`. Requires an `a4/` workspace resolvable via `git rev-parse --show-toplevel`. Unlike `/a4:research` (which is workspace-agnostic), this skill is scoped to the `a4/` workspace because it edits wiki pages and writes review items there.

## Pre-flight

1. Resolve the project root: `git rev-parse --show-toplevel`. If not a git repo, abort with a clear message.
2. Verify `<project-root>/a4/` exists. If not, abort — decision review requires the workspace.
3. Resolve `$ARGUMENTS` to an existing file under `<project-root>/a4/decision/`. If the argument is empty, or the path does not resolve, abort with usage hint: "Provide the decision file path, e.g., `/a4:decision-review a4/decision/12-caching-strategy.md`."
4. Read the file. If `status: final` already, ask: "This decision is already `final`. Re-run review anyway?" Proceed only on confirmation.

## Step 1: Run decision-reviewer

Invoke the agent:

```
Agent(subagent_type: "a4:decision-reviewer", prompt: "Review the decision record at <absolute-path>")
```

The agent returns a structured review report with per-criterion verdicts across seven dimensions:

1. **Criteria Completeness** — are success criteria comprehensive and specific?
2. **Research Balance** — was each option investigated with equal rigor?
3. **Bias Detection** — anchoring / confirmation / sunk cost / status quo / authority bias?
4. **Rationale Strength** — does the decision logically follow from the evaluation?
5. **Rejection Clarity** — is each rejected alternative given a specific reason?
6. **Reversibility Assessment** — is reversibility acknowledged, with rigor proportional?
7. **Actionability** — are Next Steps concrete and ticket-ready?

Full criteria are in `plugins/a4/agents/decision-reviewer.md`.

## Step 2: Walk findings with the user

Present the review report, then walk each flagged issue one at a time:

| Verdict | How to address |
|---------|---------------|
| `INCOMPLETE` / `IMBALANCED` | Suggest what to add. Ask if the user wants to address it. |
| `BIAS DETECTED` | Explain the bias with quoted evidence. Ask if the user wants to re-evaluate. |
| `WEAK RATIONALE` / `VAGUE REJECTION` | Propose a stronger formulation. Ask for confirmation. |
| `NOT ASSESSED` | Ask the user to supply the missing dimension (e.g., reversibility class + switching cost). |
| `VAGUE ACTIONS` | Propose concrete next-step bullets; ask for confirmation. |
| `OK` | Skip. |

For each issue the user can **accept** (apply the proposed change), **modify** (edit the proposal), or **dismiss** (leave as-is, optionally with a rationale). Respect the user's call — review findings are advisory, not binding.

## Step 3: Apply revisions

Use the `Edit` tool to apply accepted changes to the decision file. Preserve all content the user did not choose to change. Bump `updated:` to today after each write.

## Step 4: Finalize

Once the user confirms the review pass is done:

1. In the decision file's frontmatter:
   - Set `status: final`.
   - If `decision:` is empty, prompt the user for a one-line summary and populate it.
   - Bump `updated:` to today.
2. Rewrite the file.

## Step 5: In-situ wiki nudge

Check whether the finalized decision affects existing wiki pages at the `a4/` workspace root (the parent of the `decision/` folder holding this file). Discover candidates via `Glob a4/*.md`. Skip silently when no wiki pages exist.

| Change type | Likely wiki target |
|-------------|--------------------|
| Technology / framework / library choice | `architecture.md` (Technology Stack, External Dependencies) |
| Process, scope, or constraint shift | `context.md` (Problem Framing, Success Criteria) |
| New actor or role | `actors.md` |
| New domain concept | `domain.md` |
| Non-functional requirement change | `nfr.md` |

For each applicable candidate, present the proposed updates and ask the user to confirm. For every confirmed update:

1. Edit the wiki page — update the affected section, append a footnote marker `[^N]` inline, and append a `## Changes` line `[^N]: <YYYY-MM-DD> — [[decision/<id>-<slug>]]` pointing to this decision file.
2. Bump the wiki page's `updated:` frontmatter to today.

If the user defers any update, open a review item instead so the gap does not disappear:

1. Allocate an id: `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "<project-root>/a4"`.
2. Write `a4/review/<id>-<slug>.md` with:
   - `kind: gap`
   - `status: open`
   - `source: self`
   - `target: decision/<decision-id>-<slug>`
   - `wiki_impact: [<affected wiki basenames>]`

The wiki close guard (at session close) and drift detector (between sessions) re-surface unresolved impact later.

Use judgment — minor decisions (naming conventions, purely internal choices with no wiki-visible effect) skip the nudge.

## Step 6: Report

Summarize to the user:

- Review verdicts: N OK, M flagged, K accepted, L dismissed.
- Final decision path.
- Wiki pages updated / deferred review items opened (with ids).
- Reminder: the file is left in the working tree — commit at the user's convenience.

## Non-goals

- Do not author the decision. Finalize only what is already written.
- Do not commit the file. Leave in the working tree.
- Do not auto-supersede prior decisions. If `supersedes:` needs to be populated, the user sets it during Step 2 revision.
- Do not invoke `/a4:research`. Research, if needed, is a separate prior step authored outside this skill.
