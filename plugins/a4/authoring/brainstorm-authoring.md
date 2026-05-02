# a4 — brainstorm authoring

A brainstorm at `a4/brainstorm/<id>-<slug>.md` is an **idea-capture session**. The body collects raw ideas surfaced during a session; the lifecycle tracks whether any of those ideas graduated into concrete artifacts (spec / usecase / task).

Companion to `./frontmatter-issue.md`, `./issue-body.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: brainstorm
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
topic: "<short string — the session's framing question>"
status: open | promoted | discarded
promoted: []          # populated when status → promoted (e.g., [spec/8-caching, usecase/5-search])
tags: []              # free-form
---
```

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `brainstorm` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | short human-readable phrase (distinct from `topic`) |
| `topic` | yes | string | the session's framing question or theme |
| `status` | yes | enum | `open` \| `promoted` \| `discarded` |
| `promoted` | no | list of paths | populated when `status → promoted` (e.g., `[spec/<id>-<slug>, usecase/<id>-<slug>]`) |
| `tags` | no | list of strings | free-form |


- `id:` see `./frontmatter-issue.md` § `id` for the allocator command and contract.
- `title` is required and must not be a placeholder; `<title>`-shaped strings are invalid.
- `topic:` is the session's framing question or theme — a short string complementing `title:`. Where `title:` is a one-line headline ("Caching strategy options"), `topic:` is the question the session set out to explore ("How to keep the dashboard responsive when the data set grows past 100K rows?").
- `promoted:` lists artifacts that one or more ideas in the body graduated into. The list lives on the **brainstorm** side; the target file does not carry a back-reference. Reverse lookups are derived on demand.

### Lifecycle and writer ownership

```
open      → discarded | promoted
promoted  → (terminal)
discarded → (terminal)
```

Per-status meaning:

- `open` — Session captured but no idea has graduated yet. Default initial status.
- `promoted` — At least one idea graduated into an artifact named in `promoted:`. Terminal.
- `discarded` — Session deliberately dropped (overtaken by events, no idea worth pursuing). Terminal.

Writer rules (brainstorm-specific):

- `open` is the **only** initial status. New brainstorms are always born at `open`.
- The brainstorm family has **no cascade** — status changes do not trigger automatic flips of related files. `status:` is hand-flipped after the user populates `promoted:` (or decides to discard).
- Drift between `status:` and `promoted:` is invalid: non-empty `promoted:` while `status: open` is a mismatch; empty `promoted:` while `status: promoted` is the inverse mismatch.
- There is **no reverse path** from `promoted` or `discarded` — both are terminal.

## Body shape

**Required:**

- `## Ideas` — the session's idea capture. Typically a bullet list, with one bullet per surfaced idea. Keep entries short — a brainstorm captures volume; promoting an idea is when the substance gets fleshed out elsewhere. Each promoted idea may carry a markdown link to the resulting artifact (e.g., `- caching: pre-warm on session boot → [spec/8-caching-strategy](../spec/8-caching-strategy.md)`).

**Optional, emit only when applicable:**

- `## Notes` — session context, framing prose, or evaluation notes that don't belong inline next to a single idea.

Unknown H2 headings are tolerated.

## Common mistakes

- **Required-field omission** (`type`, `id`, `title`, `topic`, `status`, `created`, `updated`).
- **`status: promoted` with empty `promoted:` list** (or non-empty `promoted:` with `status: open`) — invalid; flagged at validation time.

## Don't

- **Don't expand a brainstorm idea inline.** When an idea grows beyond a one-liner, promote it: capture the substance in a spec, usecase, or task and link it from the brainstorm bullet.
- **Don't pre-populate `promoted:`.** The list is filled when an idea actually graduates.
- **Don't auto-flip `status:` based on `promoted:` content.** The user owns the flip; drift is reported separately but does not mutate files.
