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

### #N. <short title>
[status:: final]
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

### #N. <short title>
[status:: final]
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

### #N. <short title> *(split from original)*
#### #N-a. <short title>
[status:: final]
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

#### #N-b. <short title>
[status:: final]
**When** <situation/context>,
**I want to** <action/goal>,
**so I can** <expected outcome>.

...

## Story Relationships

### Dependencies
- **#N → #M**: <reason>

### Reinforcements
- **#N → #M, #O**: <reason>

### Story Groups
| Group | Stories | Description |
|-------|---------|-------------|
| <name> | #N, #M, ... | <description> |

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

**Heading number convention:**
- During the interview, stories use temporary sequential numbers (1, 2, 3...).
- At finalization, sequential numbers are replaced with GitHub issue numbers (#N) after issues are created.
- `#N` is the GitHub-assigned issue number, which becomes the story's canonical ID.

**Issue reference links:**
- Use markdown reference links so issue numbers are clickable in GitHub file preview.
- In the body, write `[#N][N]`. At the end of the file, add a references section:
  ```
  <!-- references -->
  [7]: https://github.com/{owner}/{repo}/issues/7
  ```
- This keeps the body clean while making all issue references clickable.

**Required sections**: Original Idea, Context, Job Stories, Story Relationships, Interview Transcript.
**Conditionally required:**
- **Open Questions** — if unresolved topics remain
