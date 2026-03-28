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
source:
  - "[[<story-file-name>]]"
covers:
  - <ui | non-ui>
tags: []
---
# Functional Specification: <topic>

## Overview
<Brief summary of what this software does and who it's for. Derived from the Job Stories.>

## Job Stories Reference
<List all Job Stories from the source file for traceability. If any were decomposed, show the sub-stories with a note referencing the original.>

## Functional Requirements

### FR-1: <short title>
[status:: draft]
[story:: [[<story-file-name>]]#<story heading>]

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

### FR-2: <short title>
[status:: draft]
[story:: [[<story-file-name>]]#<story heading>]
[story:: [[<another-story-file>]]#<story heading>]
...

## Open Questions
<Unresolved decisions or ambiguities to revisit.>
- ...
```

**`source` field rules:**
- Use wikilinks (filename only, no path) to the Job Story file(s) this spec is based on.
- If multiple story files feed into one spec, list all of them.

**`story` inline field rules:**
- Each FR links to the specific story item(s) it implements, using `[[filename]]#heading` format.
- If one FR comes from multiple stories (across one or more files), add multiple `[story::]` lines — Dataview treats repeated keys as arrays.
- The heading must match the exact heading text in the story file (e.g., `#1. 로그인 인증`).

**Required sections**: Overview, Job Stories Reference, Functional Requirements.
**Conditionally required:**
- **Open Questions** — if unresolved topics remain
