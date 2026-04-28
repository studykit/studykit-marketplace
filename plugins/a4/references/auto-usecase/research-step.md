# Step 2: Research (parallel, optional)

Run Step 2a and 2b in parallel when both are needed. Wait for both to complete before composing.

## Step 2a: Similar Systems Research

If no `a4/research/similar-systems-initial.md` exists, spawn a research subagent via `Agent(subagent_type: "general-purpose")`:

> Research similar systems for the following idea:
>
> <raw idea / path to brainstorm file>
>
> Goal: discover features and UCs that users of this type of system commonly need. Try 2–3 search queries. For each similar product (up to 5), list key user-facing features as "Actor does X to achieve Y". Identify candidates common across 3+ systems (high-value) vs unique to one (niche). Look for user reviews or feature requests indicating unmet needs.
>
> Write the report to `a4/research/similar-systems-initial.md` with frontmatter `{ label: similar-systems-initial, scope: similar-systems, source-input: <idea/file>, date: <today> }`. Include sections: Similar systems, High-value UC candidates, Niche UC candidates, User-requested features.

## Step 2b: Code Analysis

Skip when no source-code path is referenced. When source is referenced and no `a4/research/code-analysis-initial.md` exists, spawn a `general-purpose` subagent:

> Analyze the codebase at `<paths>`.
>
> Goal: extract what the system currently does from the perspective of its users — features, actors, workflows. Identify main entry points, implemented user-facing features, visible actors (user roles, external systems, scheduled jobs), partial/stubbed features, data entities + CRUD operations.
>
> Write the report to `a4/research/code-analysis-initial.md` with frontmatter `{ label: code-analysis-initial, scope: code-analysis, paths: [<input paths>], date: <today> }`.
