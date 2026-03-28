---
name: co-think-story
description: "This skill should be used when the user has a vague idea for software but doesn't know exactly what to build, when the user says 'help me figure out what to build', 'what should I make', 'shape this idea', 'turn this into job stories', 'gather requirements', 'split this story', 'break this down', or when a rough idea needs to be shaped into concrete Job Stories through a Socratic interview. Automatically detects and splits oversized stories into smaller, independently valuable pieces."
argument-hint: <idea or vague concept to turn into requirements>
allowed-tools: Read, Write, Agent, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
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

## Progressive File Writing

The working file is a living document that grows throughout the interview. The user can open it at any time to see the current state.

### File Lifecycle

| Phase | Trigger | What happens to the file |
|-------|---------|--------------------------|
| Create | Idea received (step 1) | Create the file with frontmatter, original idea, and empty sections |
| Update | Each story confirmed or split (steps 3-4) | Append the new story to the Job Stories section |
| Update | Progress snapshot (every 4-5 exchanges) | Update the Context section with latest understanding |
| Finalize | User ends the session (wrap-up) | Fill remaining sections, append transcript, remove draft marker |

### Working File Path

At the start of the interview, determine the file path:
- Default: `A4/co-think/<YYYY-MM-DD-HHmm>-<topic-slug>.story.md` relative to working directory
- Ask the user only if they want a different location
- Create the directory if needed

### Initial File Content

Write this immediately after restating the idea. Follow the template in `references/output-template.md` — create the file with frontmatter (`status: draft`), the Original Idea section filled in, and placeholder text for Context, Job Stories, and Open Questions.

Tell the user the file path so they can follow along: "I've started a working file at `<path>`. It will update as we go."

### How to Update

- **Use the Write tool** to rewrite the entire file each time. This keeps the file consistent and avoids partial edit issues.
- **Preserve all previously confirmed stories** — never remove or reorder them during updates.
- **Update the Context section** with the latest understanding each time you write.

## Interview Flow

### 1. Receive the Idea

Take the user's input — it may be a raw idea, a brainstorming output, or a vague description. Restate the idea back in one sentence to confirm understanding.

**Then immediately create the working file** as described in Progressive File Writing above.

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

After the user confirms or revises:
1. **Update the working file** — append the confirmed story to the Job Stories section and update Context.
2. **Track progress with tasks** — create a task for the confirmed story (e.g., `STORY-1: <title>`) and mark it as completed. This gives the user a running overview of all confirmed stories via TaskList.

### 4. Story Splitting

After a Job Story is confirmed, evaluate whether it is too large. Read `references/story-splitting.md` for the full splitting guide with signs, examples, and rules.

### 5. Challenge Mode Shifts

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

### 6. Story Relationship Analysis

After 5 or more stories have been confirmed, analyze and present the relationships between stories. Read `references/story-relationships.md` for the full analysis guide covering dependency relationships, reinforcement relationships, story groups, and presentation format.

## Facilitation Guidelines

- **Build on answers, don't interrogate.** Curious colleague, not cross-examination.
- **Use the user's own words.** Don't introduce jargon they didn't use.
- **Offer options when stuck.** "Would it be more like A, B, or something else?"
- **Stay at the right altitude.** If the user drifts into implementation ("we could use Redis"), redirect: "Good thought for later — what's the underlying need?"
- **Every 4-5 exchanges:** Brief progress snapshot — confirmed stories so far, what's still unclear, where the next question will go. Update the working file with the latest Context.

## Wrapping Up

The interview ends only when the user says so. Never conclude on your own — even if all gaps seem covered, the user may want to go deeper or add more stories. Keep asking until the user explicitly ends the session.

When the user indicates they're done:

1. **Run the story-reviewer agent** — invoke the `story-reviewer` agent with the current working file path. The agent evaluates every story for size, specificity, action clarity, outcome measurability, and overlap.
2. **Present the review results** — show the user the review report. For each flagged issue, walk through it one at a time:
   - `SPLIT` — propose the split and ask for confirmation
   - `VAGUE` / `UNCLEAR` / `WEAK` — present the suggestion and ask if the user wants to revise
   - `OVERLAPS` — ask if the user wants to merge or differentiate the overlapping stories
   - The user can accept, modify, or dismiss each suggestion. Respect their decision.
3. **Update the working file** with any revisions from the review.
4. **Create GitHub Issues for each story** — for each finalized story:
   1. Create a GitHub Issue with label `story`. Title: prefixed with the STORY ID (e.g., `STORY-1: 회의 요약 생성`). Body: the full story text + a clickable markdown link to the working file (e.g., `[A4/co-think/file.story.md](https://github.com/{owner}/{repo}/blob/main/A4/co-think/file.story.md)`).
   2. Keep the STORY-N ID in the heading as-is (e.g., `### STORY-1. 회의 요약 생성` stays unchanged).
   3. Add a `<!-- references -->` section at the end of the file mapping each STORY ID to its GitHub issue URL.
   4. Present the issue mapping to the user:

      > | ID | Issue | Title |
      > |----|-------|-------|
      > | STORY-1 | #42 | 회의 요약 생성 |
      > | STORY-2 | #43 | 요약 공유 |

5. **Finalize the working file** — write the final version with all sections completed:
   - Ensure all headings use STORY-N IDs
   - Finalize the Context section with the complete understanding from the interview
   - Ensure all confirmed Job Stories are present and in order
   - Add the Open Questions section if unresolved topics remain
   - Append the full Interview Transcript
   - Remove any placeholder text (e.g., "*Stories will appear here...*")
6. **Report the path and issues** so the user can reference them.

### Output Format

Follow the Job Stories template in `references/output-template.md` for the final file structure and required sections.
