# Initial File Content Templates

Write immediately after mode and candidates are confirmed.

## Comparative mode

```markdown
---
type: research
topic: "<topic>"
status: draft       # draft | final | standalone | archived
mode: comparative
options: [name-a, name-b, name-c]
cited_by: []
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: []
---

<context>

Why this research is needed. What the caller wants to know. 1–3 sentences.

</context>

<options>

*Subsections will appear here as each option is researched.*

</options>
```

## Single mode

```markdown
---
type: research
topic: "<topic>"
status: draft       # draft | final | standalone | archived
mode: single
cited_by: []
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: []
---

<context>

The specific question to answer. 1–3 sentences.

</context>

<findings>

*Findings will appear here as research progresses.*

</findings>
```

`cited_by:` is a stored reverse-link auto-maintained by `scripts/register_research_citation.py` when a spec cites this research. Never hand-edit.
