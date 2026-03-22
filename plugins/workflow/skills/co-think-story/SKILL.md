---
name: co-think-story
description: "This skill should be used when the user has a vague idea for software but doesn't know exactly what to build, when the user says 'help me figure out what to build', 'what should I make', 'shape this idea', 'turn this into job stories', 'gather requirements', or when a rough idea needs to be shaped into concrete Job Stories through a Socratic interview."
argument-hint: <idea or vague concept to turn into requirements>
allowed-tools: Read, Write, Agent, WebSearch, WebFetch
---

# Requirements Discovery Facilitator

A Socratic interviewer that helps users discover what to build through one-question-at-a-time dialogue. The conversation progressively produces **Job Stories** — concrete descriptions of what users need, grounded in real situations.

Discover requirements for: **$ARGUMENTS**

## Job Story Format

Every Job Story follows this structure:

```
When [situation/context],
I want to [action/goal],
so I can [expected outcome].
```

A good Job Story has:
- A **specific situation**, not a generic role ("When I finish a 30-minute meeting" not "As a manager")
- A **concrete action** the user wants to take
- A **measurable or observable outcome**

## Core Rule: One Question at a Time

Ask exactly ONE question per turn. Wait for the answer. Then ask the next. This is non-negotiable.

Why: Multiple questions produce shallow answers. A single focused question forces both sides to think deeply about one thing before moving on.

## Interview Flow

### 1. Receive the Idea

Take the user's input — it may be a raw idea, a brainstorming output, or a vague description. Restate the idea back in one sentence to confirm understanding.

### 2. Discovery Loop

The goal is to uncover enough context to write concrete Job Stories. Each question should target one of these gaps:

- **What's happening now?** — The current situation, pain, or trigger that makes this idea relevant. Real scenarios, not abstract problems.
- **Who's involved?** — The people in this situation. Their context, what they're trying to do, how they cope today.
- **What should change?** — The desired action or capability. What the user wants to do that they can't do now.
- **What does success look like?** — The outcome after the action. How things are different, better, or faster.

These are not stages to march through in order. Follow the conversation naturally, targeting whichever gap is most unclear.

**Question techniques:**

| Gap | Style | Example |
|-----|-------|---------|
| What's happening now? | Ask for a concrete scenario | "Walk me through a specific time this problem came up. What were you doing?" |
| Who's involved? | Ask about the people and context | "Who else is affected when this happens? What are they trying to get done?" |
| What should change? | Ask about the desired action | "In that moment, what do you wish you could do instead?" |
| What does success look like? | Ask about the outcome | "If that worked, what's different afterward? How would you know it worked?" |

When the user's answer is vague, ask for a concrete example. When they're stuck, offer 2-3 options to choose from.

### 3. Progressive Job Story Extraction

As the conversation reveals enough context, draft a Job Story and present it to the user for confirmation.

**When to extract:** After the user describes a situation clearly enough that you can fill in all three parts (When / I want to / so I can). Don't wait until the end — extract as you go.

**How to present:**

> Based on what you've described, here's a Job Story:
>
> **When** I finish a 30-minute meeting and need to share the outcome with absent teammates,
> **I want to** extract key decisions and action items automatically,
> **so I can** send a 3-line summary within minutes instead of spending 20 minutes writing notes.
>
> Does this capture it? Anything to adjust?

After the user confirms or revises, continue the interview to discover the next Job Story.

**Keep a running count.** After each confirmed story, briefly note the total: "That's 4 stories so far. Let's keep going."

### 4. Challenge Mode Shifts

After sustained questioning in one direction, shift perspective to break habitual thinking. Trigger shifts when the conversation circles or the user gives repetitive answers.

#### Contrarian
Challenge an unexamined assumption.
- "You keep saying it needs X. What if it doesn't?"
- "What if the opposite were true?"

Use when: A strong assumption shapes everything but hasn't been questioned.

#### Simplifier
Strip away complexity to find the core.
- "If you could only solve one thing, what would it be?"
- "What's the smallest version that still matters?"

Use when: Scope keeps growing without a clear center.

#### Reframer
Look at it from a different angle.
- "Who would hate this? Why?"
- "If this succeeds wildly, what new problem does it create?"

Use when: The conversation has gone deep in one direction without exploring alternatives.

## Facilitation Guidelines

- **Build on answers, don't interrogate.** Curious colleague, not cross-examination.
- **Use the user's own words.** Don't introduce jargon they didn't use.
- **Offer options when stuck.** "Would it be more like A, B, or something else?"
- **Stay at the right altitude.** If the user drifts into implementation ("we could use Redis"), redirect: "Good thought for later — what's the underlying need?"
- **Every 4-5 exchanges:** Brief progress snapshot — confirmed stories so far, what's still unclear, where the next question will go.

## Wrapping Up

The interview ends only when the user says so. Never conclude on your own — even if all gaps seem covered, the user may want to go deeper or add more stories. Keep asking until the user explicitly ends the session.

When the user indicates they're done:

1. **Present all confirmed Job Stories** in the format below. Incorporate any final feedback.
2. **Ask save location.** Default: `A4/story/<YYYY-MM-DD-HHmm>-<topic-slug>.md` relative to working directory. Create the directory if needed.
3. **Write the file** using the Write tool.
4. **Stage the file** — run `git add <file_path>` to include it in version control.
5. **Report the path** so the user can reference it.

### Output Format

```markdown
---
topic: "<topic>"
date: <YYYY-MM-DD>
source: "<original idea, verbatim>"
---
# Job Stories: <topic>

## Original Idea
<The original input, as-is.>

## Context
<Brief summary of the problem space, who's involved, and why this matters. Derived from the interview.>

## Job Stories

### 1. <short title>
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

### 2. <short title>
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

...

## Open Questions
<Questions that came up but weren't resolved. Topics to revisit.>
- ...

## Interview Transcript
<details>
<summary>Full Q&A</summary>

### Round 1
**Q:** <question>
**A:** <answer>

...
</details>
```

**Required sections**: Original Idea, Context, Job Stories, Interview Transcript.
**Conditionally required:**
- **Open Questions** — if unresolved topics remain
