# Non-Functional Requirements Capture

Ask the user once:

> Are there non-functional requirements? Performance targets, security, scalability, accessibility, compliance. If not, we can skip this.

If yes, write `a4/nfr.md` with:

- frontmatter `type: nfr`, `updated: <today>`
- a `## Requirements` section containing a table:
  - Description
  - Affected UCs (via markdown links)
  - Measurable criteria

Skip creating the file when there are no NFRs — `nfr.md` is optional.

The full authoring contract for `a4/nfr.md` is in `../../../authoring/nfr-authoring.md`.
