---
name: web-design-mock
description: "This skill should be used when the user wants to create a web page mockup, prototype a UI, design a landing page, build a dashboard layout, or do HTML/CSS design work. Also applies when the user mentions wireframes, page layouts, responsive design prototypes, or wants to visualize what a web page would look like."
argument-hint: <design request or description>
allowed-tools: Read, Agent
---

# Web Design Mock Generator

Orchestrate HTML mockup creation and iterate on designs based on user feedback. Manage the conversation flow and delegate HTML/CSS generation to the `mock-html-generator` agent.

Design request: **$ARGUMENTS**

## Conversation Flow

Adapt conversation depth to input specificity — generate as soon as possible. Read `references/conversation-flow.md` for the assessment matrix.

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

## After Generating

After the agent completes:

1. Report the file path: "I've created `workflow/web-mock/<session-name>/v<N>/index.html`."
2. Hand the ball back: **"Open it in your browser and let me know what you'd like to change."**
3. Wait for feedback before making the next version.

## Iterating on Feedback

When the user provides feedback, read `references/iteration-guide.md` and generate the next version.

## Session Closure

When the user indicates they're satisfied or done iterating:

1. Mention the final version path and total number of versions created.
2. All versions are kept for reference by default. Only clean up intermediate versions if the user explicitly requests it.
