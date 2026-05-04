---
name: research-review
description: "This skill should be used when the user has a research task at `a4/research/<id>-<slug>.md` (a `type: research` task whose body is the investigation deliverable) and wants to review its quality before relying on it for a downstream decision. Runs the `research-reviewer` agent, walks the flagged issues with the user one at a time, and applies accepted revisions. Triggers: 'review this research', 'check the research task', 'is this research sound', 'research review', or after finishing a `type: research` task body."
argument-hint: <task id or path to a4/research/<id>-<slug>.md>
allowed-tools: Read, Write, Edit, Agent, Bash, Glob
---

# Research Review & Revise

Wraps the `research-reviewer` agent into a quality pass for a `type: research` task. Use after the body of `a4/research/<id>-<slug>.md` has been authored (status `progress` or `done`) and before downstream work cites the findings.

Target: **$ARGUMENTS**

## Scope

- **In:** running the reviewer, walking findings with the user, applying accepted revisions.
- **Out:** no decision recording (that's `/a4:spec`). No wiki nudge — research investigation does not directly mutate wiki pages. No commit.

## Pre-flight

1. Resolve the project root: `git rev-parse --show-toplevel`. If not a git repo, abort with a clear message.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Resolve `$ARGUMENTS` to an existing file:
   - Bare integer (`#42`, `42`) → search `<project-root>/a4/research/` for `<n>-*.md`.
   - Path containing `research/` → use as-is (relative to project root if not absolute).
   - Bare slug → try `<project-root>/a4/research/*<slug>*.md` (single match required).
4. If the argument is empty or the path does not resolve, abort with usage hint: "Provide the research task id or path, e.g., `/a4:research-review 42` or `/a4:research-review a4/research/42-grpc-streaming.md`."
5. Read the file. Confirm `type: research` and that `mode:` is present (sanity check). If `status: done` already, ask: "This research task is already `done`. Re-run review anyway?" Proceed only on confirmation.

## Step 1: Run research-reviewer

Invoke the agent:

```
Agent(subagent_type: "a4:research-reviewer", prompt: "Review the research task at <absolute-path>")
```

The agent returns a structured review report with per-criterion verdicts across six dimensions:

1. **Source Quality** — are cited sources credible, current, and covering the breadth?
2. **Option Balance** *(comparative only)* — did each option receive equal rigor?
3. **Claim Grounding** — are factual claims backed by inline citations?
4. **Bias Detection** — confirmation / anchoring / authority / recency bias or framing language?
5. **Completeness** — does the report answer the stated question?
6. **Decision Neutrality** — does the report stay out of the decision?

Full criteria are in `${CLAUDE_PLUGIN_ROOT}/agents/research-reviewer.md`.

## Step 2: Walk findings with the user

Present the review report, then walk each flagged issue one at a time:

| Verdict | How to address |
|---------|---------------|
| `WEAK SOURCES` | Suggest specific authoritative sources or queries to add. Ask if the user wants to extend the investigation. |
| `IMBALANCED` | Name the under-researched option and the missing dimensions. Ask if the user wants to augment the weak side. |
| `UNGROUNDED CLAIMS` | List the un-cited claims. For each, propose either a citation to add or removal of the claim. |
| `BIAS DETECTED` | Quote the biased sentence; propose a neutral rewording. |
| `INCOMPLETE` | List the missing dimensions. Ask if the user wants to extend. |
| `ADVOCATES` | Quote the advocacy sentence; propose a neutral replacement. |
| `OK` / `N/A` | Skip. |

For each issue the user can **accept** (apply the proposed change), **modify** (edit the proposal), or **dismiss** (leave as-is, optionally with a rationale). Respect the user's call — review findings are advisory, not binding.

If a flagged issue requires significant new investigation (e.g., `IMBALANCED` requires augmenting a weak option's findings), offer to extend the body in this session, or to leave the task at `failing` for a follow-up cycle.

## Step 3: Apply revisions

Use the `Edit` tool to apply accepted changes to the task body. Preserve all content the user did not choose to change.

## Step 4: Wrap up

Once the user confirms the review pass is done:

1. Offer next-step status flips by editing `status:` directly (the PostToolUse cascade hook runs any cross-file cascade):
   - If the task is at `progress` and the user is satisfied: offer `progress → done`.
   - If the task is at `done` and revisions landed: no flip needed (the task is already terminal-active).
   - If the user wants to defer the open follow-ups: offer `progress → failing` so a later cycle picks it up.
3. Report:
   - Verdicts: N OK / N/A, M flagged, K accepted, L dismissed.
   - Revisions applied (file lines touched).
   - Final status (`progress` / `done` / `failing`).
   - Reminder: the file is left in the working tree.

If the review surfaces unresolved trade-offs that suggest a downstream design decision, surface them as candidates for `/a4:spec` rather than asking the reviewer to resolve them — research review is about evidence quality, not about making the decision.

## Non-goals

- Do not write a decision. If the research is meant to feed a decision, tell the user to invoke `/a4:spec` next.
- Do not extend the research unilaterally. If the reviewer finds gaps, propose extension points; the user decides whether to fill them now or defer.
- Do not commit. Leave files in the working tree.
