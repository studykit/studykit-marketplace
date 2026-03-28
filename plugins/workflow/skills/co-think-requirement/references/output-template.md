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

### [#N][N]. <short title>
[status:: draft]
> Story: [#N][N]

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

### [#N][N]. <short title>
[status:: draft]
> Story: [#N][N], #M
...

## Open Questions
<Unresolved decisions or ambiguities to revisit.>
- ...
```

**Source rules:**
- Place source references as a blockquote directly under the title heading.
- Use relative path links for references within the same repo. Use full GitHub URLs only in issue bodies.
- If multiple story files feed into one spec, list them comma-separated on one line.

**Heading number convention:**
- During the session, FRs use temporary sequential IDs (FR-1, FR-2...).
- At finalization, sequential IDs are replaced with GitHub issue numbers (#N) after issues are created.
- `[#N][N]` is the GitHub-assigned issue number (as a reference link), which becomes the FR's canonical ID.

**Story reference rules:**
- Each FR links to the story issue(s) it implements using a blockquote with reference links: `> Story: [#N][N]`.
- If one FR comes from multiple stories, list them comma-separated: `> Story: [#N][N], [#M][M]`.

**Issue reference links:**
- Use markdown reference links so issue numbers are clickable in GitHub file preview.
- In the body, write `[#N][N]`. At the end of the file, add a references section:
  ```
  <!-- references -->
  [7]: https://github.com/{owner}/{repo}/issues/7
  ```
- This keeps the body clean while making all issue references clickable.

**Required sections**: Overview, Job Stories Reference, Functional Requirements.
**Conditionally required:**
- **Open Questions** — if unresolved topics remain
