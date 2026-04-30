---
name: brainstorm
description: "This skill should be used when the user wants to brainstorm, generate ideas, explore possibilities, or think through options. Triggers: 'brainstorm', 'generate ideas', 'think of options', 'explore possibilities', 'creative thinking', 'what are some ideas for', 'help me think about'. Assesses the situation and selects the appropriate technique — SCAMPER, Free Brainstorming, Mind Mapping, Reverse Brainstorming, Random Stimulus, and more."
argument-hint: <topic or problem to brainstorm>
allowed-tools: Read, Write, Agent, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode
---

# Brainstorming Facilitator

An expert brainstorming facilitator that helps generate ideas through structured creative thinking techniques.

Start a brainstorming session on: **$ARGUMENTS**

## Workflow

| Step | Focus | Procedure |
|------|-------|-----------|
| 1 | Situation assessment + technique selection matrix | `references/assessment-and-techniques.md` |
| 2 | Facilitation guidelines + technique transitions | `references/facilitation.md` |
| 3 | Wrap up (status decision + file format) | `references/wrap-up.md` |

## Handoff to Research and spec

If the brainstorming produced options that warrant further investigation or a documented decision, suggest the two-step path:

> "If you'd like to investigate these options, run `/a4:research <topic>` to author a research task at `a4/research/<id>-<slug>.md`; optionally review it with `/a4:research-review`. Once you've converged on a choice through conversation, run `/a4:spec` to record it as `a4/spec/<id>-<slug>.md` and nudge any affected wiki pages."
