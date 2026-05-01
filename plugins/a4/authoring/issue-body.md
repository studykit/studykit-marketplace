# a4 Issue Body Conventions

Body-level rules for issue files (`usecase`, `task`, `bug`, `spike`, `research`, `umbrella`, `review`, `spec`, `idea`, `brainstorm`). Defines two optional sections that keep a mid-flight issue file self-sufficient for the next session: `## Resume` (current-state snapshot) and `## Log` (narrative-worthy events).

Common body rules (heading form, link form, `updated:` bumping) live in `./body-conventions.md`.

## Why two sections

A future Claude Code session (or any reader picking the file up cold) needs two distinct things:

- **What to do next** — the current approach, current blocker, the next concrete step. This is a *snapshot*; previous values become irrelevant the moment a new value replaces them.
- **What got us here** — the decision pivots, blocker resolutions, and approach changes that have shaped the work to date. This is a *narrative*; older entries retain value as audit trail.

Mixing the two in one section makes it impossible for a fresh reader to tell which fact is still live. The split keeps each surface readable on its own:

| Section | Role | Write rule |
|---|---|---|
| `## Resume` | Current-state snapshot. What a fresh session needs to pick the work up. | Freely rewrite or replace any slot; do not preserve history. |
| `## Log` | Narrative of meaningful events: decision pivots, blocker resolutions, approach changes worth remembering. | Append-only. Dated bullets. Older entries are not edited. |

When `## Resume` is present, do **not** duplicate its content in `## Log`. Use `## Log` only for events whose narrative value persists past the current state — what changed, why, and what was superseded. Routine status updates ("started X today", "moved to progress") do not belong in `## Log`.

Both sections are optional. A file may carry one, the other, both, or neither.

## `## Resume`

Purpose: **current-state snapshot for the next session**. Contains only what is true *now* — the previous state is no longer of interest, so the section is freely overwritten as work progresses.

Suggested slots (all optional, omit when empty):

- **Approach.** The strategy currently being attempted, when not yet visible in `## Description` / `## Acceptance Criteria` / `## Specification`.
- **Blocked on.** Where the work is currently stuck and the suspected cause.
- **Open questions.** Questions awaiting user input or constraints the user gave only in conversation.
- **Next.** The next concrete step a fresh session should pick up.

**Compact `## Resume` on every edit.** Walk every slot and remove items that are no longer in flight or next to do — Done sub-steps, settled Open questions, resolved Blocked-on, shipped phases. If a removed item carries narrative worth preserving past the current state, append a dated `## Log` entry in the same edit; never leave it behind as a `_Done._` marker, `settled at …` annotation, or strikethrough line. The slot lists what is live, not what has been done.

Format is the author's choice — bullets with bold lead-ins, prose paragraphs, or any combination. The expectation is that opening this section gives a fresh reader, in under 30 seconds, the information needed to continue.

```markdown
## Resume

**Approach.** caching at the Service layer (not Repository) because the cache key needs `user-id` and the Repository has no user context.

**Blocked on.** cache-key shape disagreement between [usecase/3-search-history](usecase/3-search-history.md) Flow and [spec/12-cache-key](spec/12-cache-key.md). Awaiting user input.

**Next.** SearchServiceTest cache-invalidation case is unwritten; eviction-timing assertion strategy undecided.
```

### What `## Resume` is not

Do not restate things a fresh reader can already see:

- Frontmatter values — `status:`, `cycle:`, `updated:`.
- Which files were modified — `git log` / `git diff` cover this.
- Review-item bodies — link the review item and stop there.
- Command history (test runs, builds, etc.) — that belongs in the session handoff, not in the file.

Do not record narrative ("we used to try X, then switched to Y"). That belongs in `## Log`. `## Resume` carries only what is currently in effect.

### Update discipline

`## Resume` is **strongly recommended whenever the file is mid-flight** (any `status:` other than `open` / `complete` / `discarded` / `superseded`). Status changes refresh `updated:` and run cross-file cascades automatically, but never modify `## Resume` — its content is hand-maintained. Update it as you work, and especially before any session boundary risks losing the in-memory context.

When a slot's value changes, **rewrite the slot in place** — do not keep the old value as a strikethrough or supplementary line. If the change is narrative-worthy (a decision pivot worth remembering past the moment), record that pivot as a `## Log` entry separately. Adding a new line over an old line is not a rewrite; see the *Compact every edit* rule above.

## `## Log`

Purpose: **append-only narrative of meaningful events** that have shaped the work — decision pivots, blocker resolutions, approach changes worth remembering. Routine progress is not narrative; do not log "started today" or "moved to progress". The section earns its place when the *why* of a past change adds context that the current state of the file alone cannot supply.

For an `umbrella/<id>-<slug>` file specifically, `## Log` is the umbrella's **reason for existing** — the cross-cutting narrative that spans its children. Per `./umbrella-authoring.md`, children inline-cite the umbrella path in their own entries when they depend on a decision recorded there.

Write entries when:

- A decision changed the original framing — what changed, why, and which upstream artifact (UC, spec, architecture section) still needs to be reconciled.
- A blocker recorded earlier in `## Resume` was resolved, and the resolution shapes future work.
- The approach was replaced by a materially different one and the prior attempt's lesson is worth preserving.

Do **not** restate things a fresh reader can already see (same exclusions as `## Resume` above).

Format is the author's choice — short bullets, one fact per line, append-only. Use a date prefix when several entries accrete on the same topic; standalone entries may omit the date.

```markdown
## Log

- 2026-04-28 — Tried caching at the Repository layer; abandoned because the cache key needs `user-id` and the Repository has no user context. Moved to Service-layer caching.
- 2026-05-01 — Decided to follow [spec/12-cache-key](spec/12-cache-key.md) for the cache-key shape. UC 3 Flow still needs to point at spec/12.
```

### Update discipline

`## Log` entries are append-only — do not reorder, edit, or remove old entries. Corrections accrete as new entries (`2026-05-02 — The 2026-05-01 decision was wrong: ...`).

Like `## Resume`, the section is hand-maintained. Status changes never modify `## Log`.

## Inline cross-references for cross-cutting narrative

Both `## Resume` and `## Log` may contain claims that depend on a decision recorded *elsewhere* — most often in a parent issue's `## Log` (when several siblings share a cross-cutting decision the parent owns). When this happens, write the entry so a reader who opens this file alone can discover the next file to read: **inline-cite the path of the file that carries the source narrative inside the entry itself.**

Use the body-link form (`[text](relative/path.md)`) for inline citations.

```markdown
## Resume

**Approach.** follow the caching strategy decided in [umbrella/5-search](../umbrella/5-search.md) `## Log`. This child only diverges on test-fixture shape.

**Blocked on.** cache eviction timing — local to this task, not covered by the umbrella decision.
```

Without this inline citation, the parent's `## Log` is invisible to a session that started from the child file. Frontmatter `parent:` makes the parent *discoverable* (reverse children lookup); the inline citation makes the parent *necessary to read* — only when the entry actually depends on it. Entries that are self-contained (work local to this file) need no cross-reference.

The same rule applies whenever an entry leans on narrative recorded in any other a4 file (sibling, related issue, spec, UC). Inline-cite the path; do not rely on the reader inferring it from frontmatter alone.

## Cross-references

- `./body-conventions.md` — common body rules (heading form, link form, `updated:` bumping).
- `./frontmatter-universals.md` — universal frontmatter rules.
- `./<type>-authoring.md` — per-type authoring contracts (which list `## Resume` and `## Log` in their optional-sections menu).
