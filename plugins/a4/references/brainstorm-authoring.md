# a4 — brainstorm authoring

A brainstorm at `a4/spark/<YYYY-MM-DD-HHmm>-<slug>.brainstorm.md` is a **pre-pipeline idea-capture session**. The body collects raw ideas surfaced during a session; the lifecycle tracks whether any of those ideas graduated into pipeline artifacts (spec / usecase / task).

Companion to [`./frontmatter-universals.md`](./frontmatter-universals.md), `./body-conventions.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: brainstorm
pipeline: spark
topic: "<short string — the session's framing question>"
status: open | promoted | discarded
promoted: []          # populated when status → promoted (e.g., [spec/8-caching, usecase/5-search])
tags: []              # free-form
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `brainstorm` |
| `pipeline` | yes | literal | `spark` |
| `topic` | yes | string | session topic |
| `status` | yes | enum | `open` \| `promoted` \| `discarded` |
| `promoted` | no | list of paths | populated when `status → promoted` (e.g., `[spec/<id>-<slug>, usecase/<id>-<slug>]`) |
| `tags` | no | list of strings | free-form |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

- `type:` is the literal `brainstorm`. The filename always carries the `.brainstorm` suffix as part of the basename (not the extension); the file extension stays `.md`.
- `pipeline:` is the literal `spark` for every brainstorm file. Reserved for future spark-family extensions.
- `topic:` is the session's framing question or theme — a short string, not a UUID or slug.
- `promoted:` lists pipeline artifacts that one or more ideas in the body graduated into. The list lives on the **brainstorm** side; the target file does not carry a back-reference. Reverse lookups are derived on demand.
- Brainstorm files do not carry `id:` — they have no issue-tracker identity.
- Path values are plain strings without `.md` and without brackets.
- Both `created` and `updated` are unquoted ISO dates. Bump `updated:` on every revision.

### Lifecycle and writer ownership

```
open      → discarded | promoted
promoted  → (terminal)
discarded → (terminal)
```

Per-status meaning:

- `open` — Session captured but no idea has graduated yet. Default initial status.
- `promoted` — At least one idea graduated into a pipeline artifact named in `promoted:`. Terminal.
- `discarded` — Session deliberately dropped (overtaken by events, no idea worth pursuing). Terminal.

Writer rules (brainstorm-specific):

- `open` is the **only** initial status.
- The brainstorm family has **no cascade** — the PostToolUse cascade hook doesn't flip related files for it (the family is absent from `FAMILY_TRANSITIONS`). `status:` is hand-flipped after the user populates `promoted:` (or decides to discard).
- Drift between `status:` and `promoted:` is surfaced as a separate consistency check: non-empty `promoted:` while `status: open` is a mismatch; empty `promoted:` while `status: promoted` is the inverse mismatch.
- There is **no reverse path** from `promoted` or `discarded` — both are terminal.

## Body shape

(Heading form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required:**

- `## Ideas` — the session's idea capture. Typically a bullet list, with one bullet per surfaced idea. Keep entries short — a brainstorm captures volume; promoting an idea is when the substance gets fleshed out elsewhere. Each promoted idea may carry a markdown link to the resulting pipeline artifact (e.g., `- caching: pre-warm on session boot → [spec/8-caching-strategy](../spec/8-caching-strategy.md)`).

**Optional, emit only when applicable:**

- `## Notes` — session context, framing prose, or evaluation notes that don't belong inline next to a single idea.
- `## Change Logs` — append-only audit trail when the body is materially edited post-create (rare).

Unknown H2 headings are tolerated.

## Common mistakes

- **Required-field omission** (`type`, `pipeline`, `topic`, `status`, `created`, `updated`).
- **`status: promoted` with empty `promoted:` list** (or non-empty `promoted:` with `status: open`) — surfaced as a consistency check.
- **Adding `id:`** — brainstorm files do not carry an id.

(Universal body conventions — stray content above the first H2, malformed headings, sections nested inside other sections, H1 in body — are documented in `./body-conventions.md`.)

## Don't

- **Don't expand a brainstorm idea inline.** When an idea grows beyond a one-liner, promote it: capture the substance in a spec, usecase, or task and link it from the brainstorm bullet.
- **Don't pre-populate `promoted:`.** The list is filled when an idea actually graduates.
- **Don't auto-flip `status:` based on `promoted:` content.** The user owns the flip; drift is reported separately but does not mutate files.

## Historical note: retired `spark-decide` slot

`a4/spark/<YYYY-MM-DD-HHmm>-<slug>.decide.md` was historically a separate "pre-pipeline decision" slot. It was retired in favor of direct `a4/spec/<id>-<slug>.md` records (with `## Decision Log` absorbing the rationale that previously lived in standalone decision records). No spark-family file carries `type: decide` anymore.
