# a4 Wiki Frontmatter

Wiki-side frontmatter rules — applies to every wiki page (`actors.md`, `architecture.md`, `ci.md`, `context.md`, `domain.md`, `nfr.md`) at the `a4/` root. Cross-cutting rules shared with issues (`type:`, path-reference format, empty collections, unknown fields) live in `./frontmatter-common.md`. The `updated:` timestamp contract lives in `./frontmatter-common.md`.

## Shared frontmatter contract

Every wiki page (`actors`, `architecture`, `ci`, `context`, `domain`, `nfr`) shares the same minimal contract:

```yaml
---
type: <wiki-basename>
updated: YYYY-MM-DD HH:mm
---
```

- `type:` must equal the file basename (enforced — see `./frontmatter-common.md` § `type:` field).
- `updated:` is tooling-managed — see `./frontmatter-common.md`.
- Wiki pages have **no** `id`, **no** `status`, **no** lifecycle, and do **not** carry the issue-only body sections (`## Resume`, `## Log`). They change continuously; the optional `## Change Logs` body section records why (see `./wiki-body.md`).

Per-wiki authoring files (`<wiki>-authoring.md`) describe only the body sections required for that page; they do not redeclare this contract.
