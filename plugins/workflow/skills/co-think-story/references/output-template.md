# Job Stories Output Format

```markdown
---
type: story
pipeline: co-think
topic: "<topic>"
date: <YYYY-MM-DD>
status: final
revision: 0
last_revised:                    # omit until first revision
source:                          # omit if no upstream file
  - "[[<brainstorm-file-name>]]"
tags: []
---
# Job Stories: <topic>

## Original Idea
<The original input, as-is.>

## Context
<Brief summary of the problem space, who's involved, and why this matters. Derived from the interview.>

## Job Stories

### 1. <short title>
[status:: final]
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

### 2. <short title>
[status:: final]
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

### 3. <short title> *(split from original #3)*
#### 3a. <short title>
[status:: final]
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

#### 3b. <short title>
[status:: final]
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

...

## Story Relationships

### Dependencies
- **A → B**: <reason>

### Reinforcements
- **A → B, C**: <reason>

### Story Groups
| Group | Stories | Description |
|-------|---------|-------------|
| <name> | <numbers> | <description> |

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

**`source` field rules:**
- If the idea came from a spark-brainstorm output file, add wikilinks to those files (filename only, no path).
- If the idea came from multiple diverse sessions, list all of them.
- If the user provided a raw idea with no prior diverse file, omit the `source` field entirely.

**Required sections**: Original Idea, Context, Job Stories, Story Relationships, Interview Transcript.
**Conditionally required:**
- **Open Questions** — if unresolved topics remain
