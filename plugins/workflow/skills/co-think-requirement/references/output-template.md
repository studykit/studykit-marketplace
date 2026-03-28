# Functional Specification Output Format

```markdown
---
type: requirement
pipeline: co-think
topic: "<topic>"
date: <YYYY-MM-DD>
status: final
revision: 0
last_revised:                    # omit until first revision
covers:
  - <ui | non-ui>
tags: []
---
# Functional Specification: <topic>
> Source: [<story-file-name>](./<story-file-name>)

## Overview
<Brief summary of what this software does and who it's for. Derived from the Job Stories.>

## Job Stories Reference
<List all Job Stories from the source file for traceability. If any were decomposed, show the sub-stories with a note referencing the original.>

## Functional Requirements

### [FR-1]. <short title>
[status:: draft]
> Story: [STORY-1]

<!-- For UI -->
**Screen/View:** <where this happens>
**User action:** <what the user does>
**System behavior:**
1. <step 1>
2. <step 2>
...
**Validation:** <input rules, constraints>
**Error handling:** <what happens when things go wrong>
**Mock:** <path to mock HTML file, if created>

<!-- For Non-UI -->
**Trigger:** <what initiates this>
**Input:** <format, parameters, validation>
**Processing:** <business logic, rules, steps>
**Output:** <format, structure, response>
**Error handling:** <failure modes, error responses>

**Dependencies:** <other FRs this depends on, if any>

### [FR-2]. <short title>
[status:: draft]
> Story: [STORY-1], [STORY-2]
...

## Open Questions
<Unresolved decisions or ambiguities to revisit.>
- ...
```

**Source rules:**
- Place source references as a blockquote directly under the title heading.
- Use relative path links for references within the same repo. Use full GitHub URLs only in issue bodies.
- If multiple story files feed into one spec, list them comma-separated on one line.

**Heading ID convention:**
- FRs use `FR-N` IDs (FR-1, FR-2...) as canonical identifiers throughout the document.
- These IDs are assigned during the session and remain unchanged at finalization.

**Story reference rules:**
- Each FR links to the story(ies) it implements using a blockquote: `> Story: STORY-1`.
- If one FR comes from multiple stories, list them comma-separated: `> Story: STORY-1, STORY-2`.

**Issue reference links:** See [issue-links.md](../../references/issue-links.md).

**Required sections**: Overview, Job Stories Reference, Functional Requirements.
**Conditionally required:**
- **Open Questions** — if unresolved topics remain
