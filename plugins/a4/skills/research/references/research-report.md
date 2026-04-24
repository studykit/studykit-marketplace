# Research Report Format

`/a4:research` produces a single portable file at `./research/<slug>.md`. The file body is either a `## Options` section with per-option subsections (`comparative` mode) or a flat `## Findings` section (`single` mode). No sidecar files.

## Comparative mode — per-option subsection

When `api-researcher` is invoked on an option, it returns a subsection in this shape. The skill inserts the returned markdown under `## Options` at the next checkpoint.

```markdown
### <option-name>

**Sources consulted**
- <URL | doc path | search query>
- <URL | doc path | search query>
- ...

**Key findings**
<Objective summary — what it is, how it works, strengths, limitations, cost, adoption, differentiators. Cite sources inline using `([ref](<url>))` style.>

<details><summary>Raw excerpts</summary>

<Verbatim quotes, code samples, API signatures, benchmark numbers, pricing pages, and anything else that grounds the key findings. Do not summarize or truncate.>

</details>
```

Option order in the output file follows the input order.

When options are not API-centric (architectural patterns, qualitative trade-offs), `/a4:research` writes the subsection directly in the same shape — no subagent — by using `WebSearch` / `WebFetch` and, where applicable, `get-api-docs` / `find-docs`.

## Single mode — flat findings

No subagent. `/a4:research` investigates directly and writes under `## Findings` in this flat shape:

```markdown
## Findings

**Sources consulted**
- <URL | doc path | search query>
- ...

**Key findings**
<Objective summary answering the stated question. Cite sources inline using `([ref](<url>))` style.>

<details><summary>Raw excerpts</summary>

<Verbatim quotes, code samples, API signatures, benchmark numbers.>

</details>
```

## Why inline, not sidecar

- Keeps the research record self-contained in a single file — a reader can follow every claim back to its source without chasing sidecars.
- `<details>` collapse keeps raw excerpts out of the way during normal reading but preserved in the same commit / diff / search surface for re-verification.
- Matches the B1 single-file principle established by the decision-slot-unification change (one artifact, one file).

## Checkpoint write flow (comparative mode)

1. `api-researcher` returns the subsection markdown as its response (one agent per option, parallelized).
2. `/a4:research` tracks each researched option via a task.
3. At the next checkpoint (every 2 options, phase transition, or user request), `/a4:research` rewrites the output file with all received subsections under `## Options`.
4. On finalize, `status` flips to `final` and `updated:` bumps to today.
