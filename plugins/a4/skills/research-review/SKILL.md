---
name: research-review
description: "This skill should be used when the user has a research artifact at `./research/<slug>.md` (produced by `/a4:research` or hand-authored in the same format) and wants to review its quality before relying on it for a decision. Runs the `research-reviewer` agent, walks the flagged issues with the user one at a time, applies accepted revisions, and bumps `updated:`. Triggers: 'review this research', 'check the research report', 'is this research sound', 'research review', or after finishing a `/a4:research` session. Runs workspace-agnostic — no `a4/` required."
argument-hint: <path to ./research/<slug>.md>
allowed-tools: Read, Write, Edit, Agent, Bash, Glob
---

# Research Review & Revise

Wraps the `research-reviewer` agent into a review pass for a research artifact. Use after `/a4:research` produces `./research/<slug>.md` (or on any file following the same format). Does not require an `a4/` workspace — research artifacts live at project root and are portable.

Target: **$ARGUMENTS**

## Scope

- **In:** running the reviewer, walking findings with the user, applying accepted revisions, bumping `updated:`.
- **Out:** no decision recording (that's `/a4:adr`). No wiki nudge — research is workspace-agnostic and does not touch `a4/`. No commit.

## Pre-flight

1. Resolve the project root: `git rev-parse --show-toplevel`. If not a git repo, resolve paths against the current working directory instead (this skill can run outside a git repo).
2. Resolve `$ARGUMENTS` to an existing file:
   - Absolute path → use as-is.
   - Relative path → resolve against project root (or cwd if no repo).
   - If the argument is a bare slug (no `./research/` prefix, no extension), try `./research/<slug>.md`.
3. If the argument is empty or the path does not resolve, abort with usage hint: "Provide the research file path, e.g., `/a4:research-review ./research/grpc-streaming.md` or `/a4:research-review grpc-streaming`."
4. Read the file. Confirm it has `topic:` and `mode:` in frontmatter (sanity check). If `status: final` already, ask: "This research is already `final`. Re-run review anyway?" Proceed only on confirmation.

## Step 1: Run research-reviewer

Invoke the agent:

```
Agent(subagent_type: "a4:research-reviewer", prompt: "Review the research report at <absolute-path>")
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
| `WEAK SOURCES` | Suggest specific authoritative sources or queries to add. Ask if the user wants to re-research that slice. |
| `IMBALANCED` | Name the under-researched option and the missing dimensions. Ask if the user wants to augment (possibly re-running `/a4:research` on the weak side). |
| `UNGROUNDED CLAIMS` | List the un-cited claims. For each, propose either a citation to add or removal of the claim. |
| `BIAS DETECTED` | Quote the biased sentence; propose a neutral rewording. |
| `INCOMPLETE` | List the missing dimensions. Ask if the user wants to extend. |
| `ADVOCATES` | Quote the advocacy sentence; propose a neutral replacement. |
| `OK` / `N/A` | Skip. |

For each issue the user can **accept** (apply the proposed change), **modify** (edit the proposal), or **dismiss** (leave as-is, optionally with a rationale). Respect the user's call — review findings are advisory, not binding.

If a flagged issue requires new research (e.g., `IMBALANCED` requires augmenting a weak option's findings), offer to delegate back to `/a4:research <slug>` on the specific option or sub-question rather than patching by hand.

## Step 3: Apply revisions

Use the `Edit` tool to apply accepted changes to the research file. Preserve all content the user did not choose to change. Bump `updated:` to today after each write.

## Step 4: Wrap up

Once the user confirms the review pass is done:

1. Bump `updated:` to today (if any revisions landed).
2. Offer to flip `status: draft → final` if the user is satisfied with the reviewed state. Do not flip unilaterally.
3. Report:
   - Verdicts: N OK / N/A, M flagged, K accepted, L dismissed.
   - Revisions applied (file lines touched).
   - Final status (`draft` or `final`).
   - Reminder: the file is left in the working tree.

If the review surfaces unresolved trade-offs or user uncertainty about the conclusion, those are ADR-trigger signals (B2 / B3 in [`references/adr-triggers.md`](${CLAUDE_PLUGIN_ROOT}/references/adr-triggers.md)). Surface them as candidates for `/a4:adr` rather than asking the reviewer to resolve them — research review is about evidence quality, not about making the decision.

## Non-goals

- Do not write a decision. If the research is meant to feed a decision, tell the user to invoke `/a4:adr` next.
- Do not extend the research unilaterally. If the reviewer finds gaps, offer to delegate to `/a4:research` rather than investigating inline.
- Do not touch `a4/`. Research and its review are workspace-agnostic.
- Do not commit. Leave in the working tree.
