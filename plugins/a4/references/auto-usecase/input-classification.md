# Step 1: Classify the Input

From `$ARGUMENTS`:

- **File path reference** — if the argument looks like a path, check whether it exists. `.md` → brainstorm / idea doc; source-code directories → code analysis target.
- **Inline content** — treat as raw idea.
- **Mixed** — inline idea + code path is common (e.g., "generate UCs for our current message-queue module at `src/mq/`").

## Resume detection

Before starting, check the workspace for prior progress:

```bash
# Existing wiki pages
ls a4/context.md a4/actors.md a4/domain.md a4/nfr.md 2>/dev/null

# Existing UCs
ls a4/usecase/*.md 2>/dev/null | wc -l

# Existing research / code analysis / exploration reports
ls a4/research/*.md 2>/dev/null

# Open review items
grep -l 'status: open' a4/review/*.md 2>/dev/null
```

If UCs already exist, enter **expansion mode**: treat the existing set as the target system and extend it rather than rewrite. Preserve UC ids and content; allocate new ids for new UCs only. Open review items carry over and feed the inner quality loop.

## File-reading discipline

Do **not** read input files in the main session. Pass their paths to subagents.
