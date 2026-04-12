---
name: spark-brainstorm
description: "This skill should be used when the user wants to brainstorm, generate ideas, explore possibilities, or think through options. Triggers: 'brainstorm', 'generate ideas', 'think of options', 'explore possibilities', 'creative thinking', 'what are some ideas for', 'help me think about'. Assesses the situation and selects the appropriate technique — SCAMPER, Free Brainstorming, Mind Mapping, Reverse Brainstorming, Random Stimulus, and more."
argument-hint: <topic or problem to brainstorm>
allowed-tools: Read, Write, Agent, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode
---

# Brainstorming Facilitator

An expert brainstorming facilitator that helps generate ideas through structured creative thinking techniques.

Start a brainstorming session on: **$ARGUMENTS**

## Situation Assessment

Before selecting a technique, assess the situation through brief conversation. Determine two dimensions:

### 1. Target Existence
- **Existing target**: The user wants to improve, extend, or reimagine something that already exists (a product, process, codebase, workflow).
- **Blank slate**: The user is starting from scratch — no existing artifact to work from.

### 2. Stuckness
- **Flowing**: Ideas are coming naturally.
- **Stuck**: The user feels blocked, is repeating themselves, or says they're out of ideas.

Ask 1-2 focused questions to determine these dimensions if the user's initial prompt doesn't make them clear. Do not ask all three at once — infer what you can and ask only what's ambiguous.

## Technique Selection Matrix

Based on your assessment, select the most appropriate technique by reading the corresponding file from `references/`.

| Situation | Technique | File |
|-----------|-----------|------|
| Existing target + Divergent | SCAMPER | `references/scamper.md` |
| Blank slate + Divergent | Free Brainstorming | `references/free-brainstorming.md` |
| Blank slate + Divergent (complex topic) | Mind Mapping | `references/mind-mapping.md` |
| Stuck + Divergent | Reverse Brainstorming | `references/reverse-brainstorming.md` |
| Stuck + Need fresh perspective | Random Stimulus | `references/random-stimulus.md` |
| Organizing ideas (multi-perspective) | Six Thinking Hats | `references/six-thinking-hats.md` |
| Organizing ideas (grouping) | Affinity Diagram | `references/affinity-diagram.md` |

After selecting, read the technique file and follow its process steps and facilitator prompts to guide the session.

## Facilitation Guidelines

Adapt facilitation style to the user's energy and output:

- **When ideas are scarce**: Actively contribute suggestions. Use provocative "What if..." prompts. Offer analogies from other domains. Never just wait — push the conversation forward.
- **When ideas are flowing**: Stay out of the way. Capture and reflect back. Occasionally ask clarifying questions to deepen promising directions.
- **When the user is stuck**: Reframe the problem from a different angle. Introduce a constraint ("What if you had to solve this in one day?"). Switch to a different technique — read a new technique file and pivot.
- **When current state needs investigation**: Do NOT proactively investigate the codebase or existing implementation at the start of a session. Focus on the conversation first — understand the user's goals, generate ideas, and explore possibilities through dialogue. Only investigate (via the Agent tool) when a specific question arises during the discussion that cannot be answered without checking the actual state — e.g., "Does feature X already exist?" or "How is Y currently implemented?" Even then, ask the user before launching an investigation.
- **Every 3-4 exchanges**: Briefly summarize progress — how many ideas generated, key themes emerging, what's been covered and what hasn't.

Always build on the user's ideas rather than replacing them. Use "Yes, and..." thinking. Defer judgment during divergent phases — no idea is bad during brainstorming.

## Technique Transitions & Combinations

Multiple techniques can be used in a single session. There are two patterns:

### Within-phase switching
Switch techniques within the same phase when the current one stalls or a different angle is needed:
- Free Brainstorming → Reverse Brainstorming (when ideas dry up)
- Free Brainstorming → Random Stimulus (when ideas feel repetitive)
- SCAMPER → Mind Mapping (when one lens opens a complex sub-topic worth exploring)
- Six Thinking Hats → Affinity Diagram (when the discussion reveals groupable themes)

When 8-15+ ideas have been generated, suggest organizing with Six Thinking Hats or Affinity Diagram.

### When transitioning
1. Briefly summarize what the current technique produced
2. Explain why you recommend switching or moving forward
3. Read the new technique file and introduce it
4. Always allow the user to override

## Wrapping Up

When the brainstorming reaches a natural conclusion or the user indicates they're done:

1. **Ask to summarize** — Ask: "Would you like me to summarize what we've covered?" and wait for the user's response.
2. **If the user declines** — End the session immediately.
3. **If the user agrees** — Draft the summary following the file format below. Ensure these are fully preserved: (1) anything the user emphasized as important during the conversation, (2) key turning points and rejected directions with reasons (→ Discussion Journey section), (3) any research findings from subagent investigations, and (4) any TODOs or action items that came up during the conversation. Each idea must have a short title and a 1-2 sentence description, grouped under theme headings. Present the draft to the user and incorporate any feedback.
4. **Ask save location** — Ask where to save. Default path: `A4/spark/<YYYY-MM-DD-HHmm>-<topic-slug>.brainstorm.md` relative to the working directory. Create the directory if it does not exist.
5. **Write the file** — Save using the Write tool.
6. **Report the path** — After writing, report the full file path so the main session can reference it.

### File Format

```markdown
---
type: brainstorm
topic: "<session topic>"
date: <YYYY-MM-DD>
status: draft
tags: []
---
# Brainstorming: <session topic>

## Context
<Why this brainstorming was needed. Background, constraints, goals.>

## Discussion Journey
<Key turning points, rejected directions and why, how the conversation arrived at the final ideas.>

## Ideas

### Theme: <theme name>
- **<Idea title>**: <1-2 sentence description>
- **<Idea title>**: <1-2 sentence description>

### Theme: <theme name>
- **<Idea title>**: <1-2 sentence description>
```

**Required sections**: Context, Discussion Journey, and Ideas. Conditionally required:
- **Research Findings** — if research was conducted during the session
- **TODOs** — if any action items or TODOs came up during the conversation

Additional sections may be added when the session content warrants them (e.g., Constraints, Open Questions), but always use headed sections (`##` or `###`) — never free-form prose outside a section.

## Handoff to Solution Discovery

If the brainstorming produced options that need to be evaluated and decided upon, suggest:

> "If you'd like to evaluate these options and make a decision, you can run `/think:spark-decide <file_path>` to start a solution discovery session with these ideas as input."
