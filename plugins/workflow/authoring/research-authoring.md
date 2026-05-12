# Workflow Research Authoring

A workflow research item is a **time-boxed investigation** of a question, technical topic, product question, or comparison of alternatives.

Research is a dual artifact:

1. An issue-backed workflow artifact for scope, questions, discussion, status, and review.
2. A knowledge-backed curated report for final findings, evidence, options, and recommendation-neutral conclusions.

The issue artifact is always created first. The curated report is created or updated when there is stable research output worth publishing.

Companion contracts:

- `./metadata-contract.md`
- `./issue-body.md`
- `./knowledge-body.md`
- Issue provider binding: `./providers/github-issue-authoring.md` or `./providers/jira-issue-authoring.md`
- Knowledge provider binding: `./providers/confluence-page-authoring.md` or `./providers/github-knowledge-authoring.md`

## When research is warranted

Use research when the next step is evidence-gathering, not implementation.

Good research inputs:

- Compare alternatives.
- Understand a provider, API, SDK, or integration.
- Gather evidence before committing to a spec.
- Investigate feasibility, cost, risk, or constraints.
- Produce citable findings for later specs, tasks, or decisions.

Use `spike` instead when the output is exploratory code or a runnable proof of concept.

Use `spec` instead when the decision is already known and the task is to write the prescriptive contract.

## Storage role

`research` has two roles.

| Role | Provider | Purpose |
| --- | --- | --- |
| Workflow issue | GitHub Issues or Jira | Scope, questions, discussion, status, review, and follow-up tracking. |
| Curated knowledge report | Confluence or GitHub repository `wiki/` | Final findings, sources, comparisons, and reusable evidence. |

The workflow issue may exist without a curated report while the investigation is in progress. The curated report should link back to the workflow issue when published.

## Workflow issue metadata

Represent this metadata using provider-native fields when available.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | `research`, or provider issue type/label/field equivalent. |
| `title` | yes | Short investigation title. |
| `status` | yes | Provider-backed lifecycle status. |
| `mode` | yes | `comparative` or `single`. |
| `options` | required for comparative | Alternatives being compared. |
| `knowledge_page` | optional until published | Link to curated report after publication. |
| `depends_on` | optional | Work items that must finish first. |
| `parent` | optional | Epic or parent issue coordinating this research. |
| `related` | optional | Specs, tasks, use cases, reviews, or pages this research informs. |
| `labels` | optional | Provider labels/tags. |

Provider identity replaces local integer ids. Use GitHub issue numbers or Jira keys for the workflow issue.

Do not use implementation-only fields such as `implements` or `cycle` for research.

## Curated report metadata

Represent this metadata using provider-native page properties, labels, metadata block, or index metadata when available.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | `research`. |
| `title` | yes | Same or clearer title than the workflow issue. |
| `source_issue` | yes | Link back to the workflow issue that owns discussion and status. |
| `mode` | yes | `comparative` or `single`. |
| `options` | required for comparative | Alternatives covered by the report. |
| `related` | optional | Specs, tasks, use cases, reviews, architecture, or domain pages. |
| `labels` | optional | Provider labels/tags. |

## Lifecycle

Recommended workflow issue lifecycle:

```text
open → queued → progress → done
open → discarded
queued → progress | holding | discarded
progress → holding | failing | done | discarded
holding → queued | progress | discarded
failing → queued | discarded
done → terminal
discarded → terminal
```

Status meaning:

- `open` — Captured but not yet ready to run.
- `queued` — Scoped and ready for investigation.
- `progress` — Investigation is active.
- `holding` — Paused for input, access, or sequencing.
- `failing` — Investigation is blocked by inaccessible sources, bad framing, or contradictory evidence.
- `done` — Curated report is published or the issue clearly records why no report is needed.
- `discarded` — No longer needed.

Provider mappings may vary:

- GitHub: Issue Field status when available.
- Jira: configured Jira workflow statuses.

## Workflow issue body

The workflow issue body should define the investigation scope and current state.

Recommended sections:

```markdown
## Description

<why this research is needed and how the result will be used>

## Research Question

<single question or comparison objective>

## Mode

comparative | single

## Options

- <option A>
- <option B>

## Related

- <provider-native ref or URL>
```

Optional sections:

- `## Scope` — in-scope and out-of-scope boundaries.
- `## Sources To Check` — initial source list or search plan.
- `## Resume` — current-state snapshot while in progress. See `./issue-body.md`.
- `## Log` — use sparingly; prefer provider comments for discussion. See `./issue-body.md`.

Use provider comments for ongoing notes, links discovered midstream, and review discussion. Promote stable findings into the curated report.

## Curated report body

The curated report is the citable research deliverable.

Required:

```markdown
## Context

<why the research was needed and what question it answers>
```

Required by mode:

### Comparative mode

```markdown
## Options

### <Option A>

**Sources Consulted**

- <source>

**Key Findings**

<findings with citations>

### <Option B>

...
```

### Single mode

```markdown
## Findings

**Sources Consulted**

- <source>

**Key Findings**

<findings with citations>
```

Optional sections:

- `## Summary` — concise result overview.
- `## Criteria` — comparison criteria and why they matter.
- `## Raw Evidence` — compact excerpts, benchmark numbers, API signatures, or tables.
- `## Limitations` — known uncertainty, missing access, or confidence boundaries.
- `## Related Work` — specs, tasks, use cases, or reviews that cite or depend on the research.
- `## Change Log` — required for material updates. See `./knowledge-body.md`.
- `## Sources` — bibliography-style source list when not already covered in each option/finding.

## Decision neutrality

Research describes evidence. Specs make decisions.

Avoid prescriptive language such as:

- "Therefore we should choose X."
- "The implementation must use Y."
- "X is the correct architecture."

Prefer evidence-oriented language:

- "X has lower operational overhead under these constraints."
- "Y lacks feature Z in the documented API."
- "The evidence supports X if revocation latency is the primary criterion."

If a decision is reached, record it in a spec `## Decision Log` or another appropriate knowledge artifact, and cite the research.

## Publishing rule

Publish or update the curated report when:

- The research question is clear.
- Sources consulted are listed.
- Findings are grounded in sources.
- Comparative reports cover each option with similar depth or explain why not.
- Limitations or confidence boundaries are visible.
- The report can be cited by a spec, task, or review without relying on hidden discussion.

The first publication should add a `## Change Log` entry linking to the workflow issue.

## Review before done

Before marking research `done`, perform or request a quality review for:

- Source quality.
- Claim grounding.
- Option balance in comparative mode.
- Missing criteria.
- Bias or premature decision-making.
- Clear limitations.

Review findings should become `review` items if they need workflow tracking.

## Citing research

Specs and tasks should cite the curated report, not a long issue comment thread.

Use provider-native refs or links:

```markdown
## Related Work

- [OAuth Provider Evaluation](https://example.atlassian.net/wiki/spaces/ENG/pages/123456789/OAuth+Provider+Evaluation)
```

The workflow issue remains useful for audit and discussion, but the curated report is the stable citation target.

## Common mistakes

- Publishing raw notes as the curated report.
- Making a decision in research instead of in a spec.
- Comparing options with uneven evidence without explaining why.
- Marking research `done` before a citable report exists or before the issue explains why no report is needed.
- Hiding source links in comments instead of the curated report.
- Using local projection paths or local integer ids as provider-backed identity.

## Do not

- Do not use `implements` or implementation cycle fields on research.
- Do not store the final research deliverable only in an issue body when a knowledge backend is configured.
- Do not create the curated report before the workflow issue unless importing existing documents.
- Do not auto-trigger a skill just because research is being written; follow the authoring resolver policy.
