---
name: co-think-discover
description: "This skill should be used when the user needs to make a decision between options, evaluate trade-offs, or research alternatives before choosing a solution. Triggers: 'help me decide', 'compare alternatives', 'evaluate options', 'trade-off analysis', 'research options', 'ADR', 'architecture decision', 'solution discovery', 'pick between', 'which approach', 'weigh pros and cons', 'decision record', 'choose between', 'which option is better'. Can accept output from co-think-diverse as input."
argument-hint: <topic, problem, or path to brainstorming output file>
allowed-tools: Read, Write, Agent, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode
---

# Solution Discovery Facilitator

A solution discovery facilitator that helps move from multiple options to a well-reasoned decision through structured research and evaluation. The output is an Architecture Decision Record (ADR) — a documented decision with rationale, rejected alternatives, and next steps.

Facilitate a solution discovery session on: **$ARGUMENTS**

## Input Handling

Determine how to start based on the input:

1. **File path provided** (e.g., `A4/think-diverse/...`): Read the file, extract ideas/options, present them to the user, and ask which ones to evaluate. Skip to Phase 2 (Option Generation) with these as candidates.
2. **Topic/problem provided**: Start from Phase 1 (Problem Framing).

If the input is ambiguous, ask the user to clarify.

## Progressive File Writing

The working file is a living document that grows throughout the session. The user can open it at any time to see the current state.

### File Lifecycle

| Phase | Trigger | What happens to the file |
|-------|---------|--------------------------|
| Create | Problem framed (Phase 1 complete) | Create file with frontmatter, context, and empty sections |
| Update | Each option researched (Phase 3) | Append research findings |
| Update | Evaluation completed (Phase 4) | Add evaluation matrix and analysis |
| Finalize | Decision made (Phase 5) | Fill all sections, append discussion log, change status to final |

### Working File Path

At the start of the session, determine the file path:
- Default: `A4/think-discover/<YYYY-MM-DD-HHmm>-<topic-slug>.md` relative to working directory
- Ask the user only if they want a different location
- Create the directory if needed

### Initial File Content

Write this after Problem Framing is complete:

```markdown
---
type: discover
topic: "<topic>"
date: <YYYY-MM-DD>
source: "<original input, verbatim>"
status: draft
framework: ""
decision: ""
---
# Decision Record: <topic>

## Context
<Why this decision is needed. Background, constraints, triggers. Derived from Problem Framing.>

## Success Criteria
<The dimensions being optimized for. Derived from Problem Framing.>

## Options Considered
*Options will appear here as they are confirmed.*

## Research Findings
*Findings will appear here as research is conducted.*

## Evaluation
*Evaluation will appear here after research is complete.*

## Decision
*Will be filled when the decision is made.*

## Rejected Alternatives
*Will be filled when the decision is made.*

## Next Steps
*Will be filled at the end of the session.*
```

Tell the user the file path so they can follow along: "I've started a working file at `<path>`. It will update as we go."

### How to Update

- **Use the Write tool** to rewrite the entire file each time. This keeps the file consistent and avoids partial edit issues.
- **Preserve all previously confirmed content** — never remove or reorder confirmed options, findings, or evaluation results.
- **Update the Context and Success Criteria** if new information emerges during the session.
- **Keep the `status: draft` marker** in frontmatter until wrap-up.

## Navigation Rules

Phases follow a natural order (Problem Framing → Option Generation → Research → Evaluation → Decision). The user controls all transitions, revisiting and interleaving are welcome.

## Phase 1: Problem Framing

The goal is to understand what the user is deciding, why, and what "good" looks like.

### What to uncover

- **What's the decision?** — State it back in one sentence to confirm.
- **Why now?** — What triggered this? What happens if no decision is made?
- **Constraints** — Time, budget, team size, technical stack, existing commitments.
- **Success criteria** — What dimensions matter? Ask: "If you could only optimize for one thing, what would it be?" Then: "What's the second most important?"

### Question techniques

| Gap | Style | Example |
|-----|-------|---------|
| What's the decision? | Restate and confirm | "So the core question is: which tool should manage your story/spec files. Is that right?" |
| Why now? | Ask for the trigger | "What changed that makes this decision necessary now?" |
| Constraints | Ask for boundaries | "Are there any hard constraints — budget limits, team size, must-use technologies?" |
| Success criteria | Force-rank | "If you could only optimize for one thing, what would it be?" |

When the user's criteria are vague, ask for a concrete example. When they list too many criteria, ask them to rank the top 3-5.

## Situation Assessment & Framework Selection

After Problem Framing, assess the decision to select an evaluation framework. Read the corresponding file from `references/`.

| Decision type | Framework | File |
|---------------|-----------|------|
| Multiple options (3+), quantifiable criteria | Weighted Scoring | `references/weighted-scoring.md` |
| Comparing against status quo / baseline | Pugh Matrix | `references/pugh-matrix.md` |
| Quick decision, 2-3 options, informal | Pros-Cons-Risks | `references/pros-cons-risks.md` |
| Strategic, external factors matter | SWOT per Option | `references/swot-analysis.md` |
| Resource-constrained, ROI matters | Cost-Benefit | `references/cost-benefit.md` |

If the decision type is ambiguous, default to Pros-Cons-Risks (simplest) and escalate to Weighted Scoring if more rigor is needed.

After selecting, read the framework reference file and follow its process steps to guide the evaluation phase.

Update the `framework` field in the working file frontmatter.

## Phase 2: Option Generation

### If input is from co-think-diverse
Present the extracted ideas and ask: "Which of these do you want to evaluate? Any to add or remove?"

### If starting fresh
Help brainstorm 3-7 candidate options. Techniques:
- Ask the user what options they already have in mind
- Suggest options from domain knowledge
- Ask: "What would someone with a completely different perspective suggest?"

For each option, capture a one-sentence description. Confirm the final list before proceeding.

Update the working file with the confirmed options.

## Phase 3: Research

For each promising option, investigate using WebSearch/WebFetch and codebase exploration (via Agent).

### Research protocol

1. **Ask before researching** — "I'd like to research [option] now. Any specific questions you want me to answer about it?" This prevents wasted research.
2. **Research one option at a time** — Present findings, then ask: "Anything else you want to know about this before we move on?"
3. **Be objective** — Present both strengths and limitations. Do not advocate for any option during research.
4. **Cite sources** — Include links or references for factual claims.
5. **Update the file** — After each option is researched, append findings to the Research Findings section.

### Research depth

- For each option, aim to answer: What is it? How does it work? What are its strengths? What are its limitations? What's the cost? Who uses it successfully?
- Match research depth across options — if you spend 3 searches on Option A, spend 3 on Option B.

### Research checkpoint

After all options are researched, ask: "We've researched all options. Is there enough information to evaluate, or do you want to dig deeper into any option?"

## Phase 4: Evaluation

Walk through the evaluation systematically using the selected framework's process steps.

### Facilitation during evaluation

- **Present, don't prescribe** — Show the comparison, let the user interpret it.
- **Surface disagreements** — If your research suggests one thing but the user scores differently, flag it: "Interesting — the research showed X, but you scored it lower. What's your reasoning?"
- **Use challenge modes** when the conversation circles or the user defaults to a familiar option:

#### Devil's Advocate
Challenge the leading option.
- "What's the strongest argument against [leading option]?"
- "If [leading option] fails in 6 months, what would the reason be?"

Use when: One option is being favored without critical examination.

#### Reframer
Shift the evaluation perspective.
- "What would a new team member think about this choice?"
- "If you had to maintain this for 5 years, does the ranking change?"

Use when: Evaluation is stuck in one frame of reference.

### Sensitivity check

After scoring, test the robustness of the result:
- "If we changed the weight of [top criterion] by 10%, would the winner change?"
- "Is the gap between the top two options meaningful or noise?"

## Phase 5: Decision & Documentation

When the evaluation points to a clear winner (or the user has decided):

1. **State the decision** — "Based on the evaluation, [option] emerges as the best fit because [reason]. Does this match your thinking?"
2. **Document trade-offs** — "By choosing [option], you're accepting [trade-off]. Is that okay?"
3. **Document rejected alternatives** — For each rejected option, write a specific reason tied to the evaluation.
4. **Assess reversibility** — "Is this decision easily reversible, or are we committing? What would switching cost later?"
5. **Identify risks** — "What could go wrong with this choice? How would we mitigate it?"
6. **Define next steps** — "What are the concrete actions to move forward?"

## Facilitation Guidelines

- **Build on the user's reasoning.** Don't override their judgment — sharpen it.
- **Research before opinions.** Never advocate for an option before investigating it.
- **Every 3-4 exchanges:** Brief progress snapshot — which phase we're in, what's been decided, what's next.
- **When the user is stuck between two options:** Ask "What would tip the balance?" and "Which set of trade-offs can you live with?"
- **Flag reversibility:** Irreversible decisions warrant more rigor than reversible ones. If the decision is easily undone, say so — don't over-analyze.
- **Match depth to stakes:** A tool choice for a side project doesn't need SWOT analysis. A core architecture decision does.

## Wrapping Up

The session ends only when the user confirms the decision. Never conclude unilaterally.

When the user indicates they're done:

1. **Run the decision-reviewer agent** — invoke the `decision-reviewer` agent with the current working file path. The agent evaluates the record for criteria completeness, research balance, bias, rationale strength, rejection clarity, reversibility, and actionability.
2. **Present the review results** — show the user the review report. For each flagged issue, walk through it one at a time:
   - `INCOMPLETE` / `IMBALANCED` — suggest what to add and ask if the user wants to address it
   - `BIAS DETECTED` — explain the bias and ask if the user wants to re-evaluate
   - `WEAK RATIONALE` / `VAGUE REJECTION` — propose a stronger formulation and ask for confirmation
   - The user can accept, modify, or dismiss each suggestion. Respect their decision.
3. **Update the working file** with any revisions from the review.
4. **Finalize the working file** — write the final version:
   - Change `status: draft` to `status: final` in frontmatter
   - Fill the `decision` field in frontmatter with a one-line summary
   - Ensure all sections are complete
   - Append the Discussion Log
   - Remove any placeholder text
5. **Report the path** so the user can reference it.
7. **Suggest next steps** — If the decision leads to building something: "You can now use `/workflow:co-think-story <file_path>` to turn this decision into Job Stories."

### Output Format

Follow the ADR template in `references/adr-template.md` for the final file structure and required sections.
