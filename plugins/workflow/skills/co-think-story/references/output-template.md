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
tags: []
---
# Job Stories: <topic>
> Source: [<brainstorm-file-name>](./<brainstorm-file-name>)

## Original Idea
<The original input, as-is.>

## Context
<Brief summary of the problem space, who's involved, and why this matters. Derived from the interview.>

## Job Stories

### [STORY-1]. <short title>
[status:: final]
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

### [STORY-2]. <short title>
[status:: final]
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

### [STORY-3]. <short title> *(split from original)*
#### [STORY-3a]. <short title>
[status:: final]
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

#### [STORY-3b]. <short title>
[status:: final]
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

...

## Story Relationships

### Dependencies
- **[STORY-1] → [STORY-2]**: <reason>

### Reinforcements
- **[STORY-1] → [STORY-2], [STORY-3]**: <reason>

### Story Groups
| Group | Stories | Description |
|-------|---------|-------------|
| <name> | [STORY-1], [STORY-2], ... | <description> |

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

**Source rules:**
- Place source references as a blockquote directly under the title heading.
- Use relative path links for references within the same repo. Use full GitHub URLs only in issue bodies.
- If the idea came from a spark-brainstorm output file, add relative path links.
- If the idea came from multiple sources, list them comma-separated on one line.
- If the user provided a raw idea with no prior file, omit the source line entirely.

**Heading ID convention:**
- Stories use `STORY-N` IDs (STORY-1, STORY-2...) as canonical identifiers throughout the document.
- These IDs are assigned during the interview and remain unchanged at finalization.

**Issue reference links:** See [issue-links.md](../../references/issue-links.md).

**Required sections**: Original Idea, Context, Job Stories, Story Relationships, Interview Transcript.
**Conditionally required:**
- **Open Questions** — if unresolved topics remain
