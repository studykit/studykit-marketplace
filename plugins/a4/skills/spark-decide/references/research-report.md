# Research Report Format

spark-decide uses the B1 single-file model: the finalized decide file at `a4/decision/<id>-<slug>.md` contains the decision plus the research and session trace that produced it. No sidecar files.

The Research agent (`a4:api-researcher`) is spawned per option and returns its findings as a markdown block in its response. spark-decide inserts that block into the main decide file's `## Research Findings` section at the next checkpoint.

## Agent output format

Each research pass produces one subsection keyed by option name:

```markdown
### Option N: <name>

**Sources consulted**
- <URL | doc path | search query>
- <URL | doc path | search query>
- ...

**Key findings**
<Objective summary — what it is, how it works, strengths, limitations, cost, adoption, differentiators. Cite sources inline using `([ref](<url>))` footnote style.>

<details><summary>Raw excerpts</summary>

<Verbatim quotes, code samples, API signatures, benchmark numbers, pricing pages, and anything else that grounds the key findings. Do not summarize or truncate; paste directly so the file is self-contained and re-verifiable.>

</details>
```

## Why inline, not sidecar

- Keeps the decision and its justifying research in one file — a reader can audit "why did we pick this?" without chasing sidecars.
- `<details>` collapse means raw excerpts stay out of the way during normal reading but remain in the same commit / same diff / same search surface.
- Avoids introducing a sidecar convention under `a4/decision/`, which the issue-tracker schema would have to special-case.

## How spark-decide incorporates agent output

1. The Research agent returns the subsection markdown as its response.
2. spark-decide tracks each researched option via a task.
3. At the next checkpoint (every 2 options, or phase transition), spark-decide rewrites the decide file with all received subsections appended under `## Research Findings`.
4. In the Evaluation section, the skill references options by name, not by sidecar path.
