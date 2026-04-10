# Phase Review Guide

Detailed procedures for triggering and conducting phase reviews via the `spec-reviewer` subagent.

## Review Scopes

Each phase has a focused review scope that maps to specific reviewer criteria:

| Scope | Sections Reviewed | Reviewer Criteria | When |
|-------|-------------------|-------------------|------|
| **Requirements** | FRs, UI Screen Groups, Authorization | #1 Behavior Coverage (FR completeness only), #2 Precision (FR language), #3 Error & Edge (FR error handling), #5 UI Screen Grouping, #6 Technical Claims (in FRs) | After FRs are substantially defined |
| **Domain Model** | Glossary, Relationships, State Transitions | #2 Precision (naming conflicts, glossary coverage), #7 Consistency (FR ↔ Domain only) | After concepts and relationships are mapped |
| **Architecture** | Components, DB Schemas, Information Flows, Interface Contracts | #1 Behavior Coverage (sequence diagrams, component mapping), #4 Ownership, #6 Technical Claims (in architecture), #7 Consistency (full cross-section, cross-diagram) | After components and flows are defined |
| **Full** | All sections | All criteria (#0–#7) | End Iteration, Finalize |

## When to Trigger

1. **Auto-suggest:** When the Navigation status table shows a phase as `Ready for review`, suggest it to the user: "Requirements look substantial enough for a phase review. Want me to send them to the reviewer?" Never auto-trigger — always ask.
2. **User request:** The user can request a phase review at any time (e.g., "review the domain model"). Trigger immediately.
3. **End Iteration / Finalize:** Always uses **Full** scope. See Wrapping Up section in SKILL.md.

## How to Request a Review

Spawn a fresh `Agent(subagent_type: "spec-reviewer")`. Include the scope, file paths, and report output path per `review-report.md` (in this references directory) in the prompt.

**Scoped review:**

> **Scoped review request.**
> Scope: **Requirements**
> Review criteria: #1 Behavior Coverage (FR completeness only), #2 Precision (FR language), #3 Error & Edge (FR error handling), #5 UI Screen Grouping, #6 Technical Claims (in FRs).
> Spec file: `<path>`
> Source files: `<paths>`
> Report path: `A4/<topic-slug>.spec.review-requirements-<revision>.md`
> Only review the sections and criteria listed above. Skip all other criteria.

**Full review:**

> **Full review request.**
> Scope: **Full**
> Review all sections against all criteria (#0–#7).
> Spec file: `<path>`
> Source files: `<paths>`
> Report path: `A4/<topic-slug>.spec.review-full-<revision>.md`

If previous review reports exist, include their paths so the reviewer can see prior findings:

> Previous review reports: `<paths>` — focus on whether previously flagged issues have been addressed.

## Before Review

Before launching the reviewer subagent, write a checkpoint and **increment `revision`**. This stamps the exact document state the reviewer will evaluate. The review report uses this post-bump revision in its filename and frontmatter.

## After Review

1. Present findings to the user, walking through flagged issues one at a time.
2. Update the spec file with accepted revisions. Add the review report file name to the frontmatter `reflected_files` list. **Increment `revision`** and update `revised` timestamp.
3. Update the Navigation status table: mark the phase as `Reviewed (rev N)`.
4. If subsequent changes are made to a reviewed phase, change its review status to `Changes since last review`.
