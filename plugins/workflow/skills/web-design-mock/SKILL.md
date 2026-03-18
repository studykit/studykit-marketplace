---
name: web-design-mock
description: "This skill should be used when the user wants to create a web page mockup, prototype a UI, design a landing page, build a dashboard layout, or do HTML/CSS design work. Also applies when the user mentions wireframes, page layouts, responsive design prototypes, or wants to visualize what a web page would look like. It generates self-contained HTML/CSS files and supports iterative refinement through versioned outputs."
argument-hint: <design request or description>
allowed-tools: Read, Agent
---

# Web Design Mock Generator

Orchestrate HTML mockup creation and iterate on designs based on user feedback. Manage the conversation flow and delegate HTML/CSS generation to the `mock-html-generator` agent.

Design request: **$ARGUMENTS**

## Conversation Flow

Adapt your conversation depth based on the specificity of the user's input. The core principle: **generate as soon as there is enough information. Only ask about what's missing.**

### Assessing Input Specificity

- **Vague request** ("make me a landing page") — Ask about purpose, audience, and mood one question at a time. Keep it to 2-3 questions max before generating a first draft.
- **Moderate detail** ("SaaS landing page, clean look") — Confirm the overall structure briefly, then generate immediately.
- **Highly specific** ("dark dashboard with sidebar and card grid layout") — Generate immediately without asking questions.
- **Reference provided** (image attached or URL mentioned) — Analyze the reference, confirm the direction, then generate.

When in doubt, lean toward generating early. A concrete mockup drives better feedback than abstract discussion.

## File Management

All output goes into a versioned directory structure. Each modification creates a new version — never overwrite previous versions.

### Directory Structure

```
workflow/web-mock/<session-name>/
  v1/
    index.html
    style.css
  v2/
    index.html
    style.css
  ...
```

- `<session-name>`: A short slug derived from the design request (e.g., `saas-landing`, `admin-dashboard`).
- Path is relative to the project root (current working directory).

### Version Rules

- Every modification produces a new version directory (`v1/`, `v2/`, `v3/`, ...).
- Previous versions are read-only — never edit files in an earlier version.
- When the user asks to combine elements across versions ("v2's header with v3's color scheme"), read the referenced versions and pass both sets of files to the agent as context.

## Generating Mockups

When it's time to generate, delegate to the `mock-html-generator` agent. Provide a clear, complete prompt that includes:

1. **Design brief**: What to build (page type, layout, sections, mood, colors).
2. **Output path**: The exact directory to write files to (e.g., `workflow/web-mock/saas-landing/v1/`).
3. **Styling preference**: Pure CSS (default) or Tailwind CDN.
4. **Previous version context**: If iterating, include the relevant previous version files or describe what to keep/change. For cross-version combinations, read the referenced versions and include the relevant portions.

### Prompt Template

```
Design brief: <description of what to build>
Output path: workflow/web-mock/<session-name>/v<N>/
Styling: <pure CSS | Tailwind CDN>
<If iterating:>
Previous version: <include file contents or describe changes needed>
Feedback: <user's feedback>
```

## After Generating

After the agent completes:

1. Report the file path: "I've created `workflow/web-mock/<session-name>/v<N>/index.html`."
2. Hand the ball back: **"Open it in your browser and let me know what you'd like to change."**
3. Wait for feedback before making the next version.

## Iterating on Feedback

When the user provides feedback:

- **Specific feedback** ("make the header bigger", "change the primary color to blue") — Pass directly to the agent and generate the next version.
- **Vague feedback** ("it doesn't feel right", "too busy") — Ask one clarifying question, then generate. Don't over-discuss.
- **Comparative feedback** ("I liked v1's layout but v3's colors") — Read the referenced versions, then pass both to the agent with instructions on what to combine.
- **Structural changes** ("add a pricing section", "remove the testimonials") — Pass the feedback and generate the next version.

Keep the iteration loop tight: feedback → new version → "Open it and let me know." Avoid lengthy explanations of what you changed — the browser is the best explanation.

## Session Closure

When the user indicates they're satisfied or done iterating:

1. Mention the final version path and total number of versions created.
2. Offer: "Would you like me to clean up the intermediate versions, or keep them all for reference?"
3. If the user wants cleanup, delete intermediate version directories but keep the final one.
