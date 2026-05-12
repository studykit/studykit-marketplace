# a4 Issue Body Conventions

Body-level rules for issue files (`usecase`, `task`, `bug`, `spike`, `research`, `epic`, `review`, `spec`, `idea`, `brainstorm`). Defines two optional sections that keep a mid-flight issue file self-sufficient for the next session: `## Resume` (current-state snapshot) and `## Log` (narrative-worthy events).

Common body rules (heading form, backlink form): `./body-conventions.md`.

## Why two sections

A future Claude Code session (or any reader picking up cold) needs two distinct things:

- **What to do next** — current approach, current blocker, next concrete step. A *snapshot*; previous values become irrelevant the moment a new value replaces them.
- **What got us here** — decision pivots, blocker resolutions, approach changes that have shaped the work. A *narrative*; older entries retain value as audit trail.

Mixing the two makes it impossible for a fresh reader to tell which fact is still live. The split keeps each surface readable on its own:

| Section | Role | Write rule |
|---|---|---|
| `## Resume` | Current-state snapshot. What a fresh session needs to pick the work up. | Freely rewrite or replace any slot; do not preserve history. |
| `## Log` | Narrative of meaningful events: decision pivots, blocker resolutions, approach changes worth remembering. | Append-only. Dated bullets. Older entries are not edited. |

When `## Resume` is present, do **not** duplicate its content in `## Log`. Use `## Log` only for events whose narrative value persists past the current state — what changed, why, what was superseded. Routine status updates ("started X today", "moved to progress") do not belong in `## Log`.

Both sections are optional. A file may carry one, the other, both, or neither.

## `## Resume`

Purpose: **current-state snapshot for the next session**. Contains only what is true *now*; freely overwritten as work progresses.

Suggested slots (all optional, omit when empty):

- **Approach.** Strategy currently being attempted, when not yet visible in `## Description` / `## Acceptance Criteria` / `## Specification`.
- **Blocked on.** Where the work is currently stuck and the suspected cause.
- **Open questions.** Questions awaiting user input or constraints the user gave only in conversation.
- **Next.** The next concrete step a fresh session should pick up.

**Compact `## Resume` whenever you update it.** Adding a new in-flight item, modifying an existing one, or marking something settled — in the same edit, walk every slot and remove items no longer in flight or next to do (Done sub-steps, settled Open questions, resolved Blocked-on, shipped phases). If a removed item carries narrative worth preserving past the current state, append a dated `## Log` entry in the same edit; never leave it behind as a `_Done._` marker, `settled at …` annotation, or strikethrough line. The slot lists what is live, not what has been done.

Format is the author's choice — bullets with bold lead-ins, prose paragraphs, or any combination. Opening this section should give a fresh reader, in under 30 seconds, the information needed to continue.

```markdown
## Resume

**Approach.** caching at the Service layer (not Repository) because the cache key needs `user-id` and the Repository has no user context.

**Blocked on.** cache-key shape disagreement between `usecase/3-search-history.md` Flow and `spec/12-cache-key.md`. Awaiting user input.

**Next.** SearchServiceTest cache-invalidation case is unwritten; eviction-timing assertion strategy undecided.
```

### What `## Resume` is not

Do not restate things a fresh reader can already see:

- Frontmatter values — `status:`, `cycle:`.
- Which files were modified — `git log` / `git diff` cover this.
- Review-item bodies — link the review item and stop there.
- Command history (test runs, builds, etc.) — that belongs in the session handoff.

Do not record narrative ("we used to try X, then switched to Y"). That belongs in `## Log`. `## Resume` carries only what is currently in effect.

### Update discipline

`## Resume` is **strongly recommended whenever the file is mid-flight**. Each per-type contract (`./<type>-authoring.md`) names the family's mid-flight statuses; non-terminal is a useful rough proxy but some non-terminal states (e.g., `usecase: ready / implementing`, `spec: active`) are stable and not mid-flight. Status changes may run cross-file cascades automatically, but never modify `## Resume` — its content is hand-maintained. Update as you work, especially before any session boundary risks losing in-memory context.

When a slot's value changes, **rewrite the slot in place** — do not keep the old value as strikethrough or supplementary line. If the change is narrative-worthy, record that pivot as a `## Log` entry separately. Adding a new line over an old line is not a rewrite; see *Compact whenever you update it* above.

## `## Log`

Purpose: **append-only narrative of meaningful events** that have shaped the work — decision pivots, blocker resolutions, approach changes worth remembering. Routine progress is not narrative; do not log "started today" or "moved to progress". The section earns its place when the *why* of a past change adds context the current state alone cannot supply.

For an `epic/<id>-<slug>` file, `## Log` carries the epic's **shared coordination narrative** — decisions, pivots, blockers, integration constraints, and cross-child trade-offs spanning its children. Per `./epic-authoring.md`, children inline-cite the epic path in their own entries when they depend on a decision recorded there.

Write entries when:

- A decision changed the original framing — what changed, why, and which upstream artifact (UC, spec, architecture section) still needs reconciling.
- A blocker recorded earlier in `## Resume` was resolved, and the resolution shapes future work.
- The approach was replaced by a materially different one and the prior attempt's lesson is worth preserving.

Do **not** restate things a fresh reader can already see (same exclusions as `## Resume`).

Format is the author's choice — short bullets, one fact per line, append-only. Use a `YYYY-MM-DD HH:mm` (KST) prefix when several entries accrete on the same topic; standalone entries may omit the timestamp.

```markdown
## Log

- 2026-04-28 14:32 — Tried caching at the Repository layer; abandoned because the cache key needs `user-id` and the Repository has no user context. Moved to Service-layer caching.
- 2026-05-01 09:15 Decided to follow `spec/12-cache-key.md` for the cache-key shape. UC 3 Flow still needs to point at spec/12.
```

### Update discipline

`## Log` entries are append-only — do not reorder, edit, or remove old entries. Corrections accrete as new entries (`2026-05-02 11:08 — The 2026-05-01 09:15 decision was wrong: ...`).

Like `## Resume`, hand-maintained. Status changes never modify `## Log`.

## Inline cross-references for cross-cutting narrative

Both `## Resume` and `## Log` may contain claims that depend on a decision recorded *elsewhere* — most often in a parent issue's `## Log` (when several siblings share a cross-cutting decision the parent owns). When this happens, write the entry so a reader who opens this file alone can discover the next file to read: **inline-cite the path of the file that carries the source narrative inside the entry itself.**

Use the body backlink form (`` `<relpath>/<file>.md` `` or `` `<file>.md` `` per `./body-conventions.md` § Backlink form) for inline citations.

```markdown
## Resume

**Approach.** follow the caching strategy decided in `../epic/5-search.md` `## Log`. This child only diverges on test-fixture shape.

**Blocked on.** cache eviction timing — local to this task, not covered by the epic decision.
```

Without this inline citation, the parent's `## Log` is invisible to a session that started from the child file. Frontmatter `parent:` makes the parent *discoverable* (reverse children lookup); the inline citation makes it *necessary to read* — only when the entry actually depends on it. Self-contained entries need no cross-reference.

The same rule applies whenever an entry leans on narrative recorded in any other a4 file (sibling, related issue, spec, UC). Inline-cite the path; do not rely on the reader inferring it from frontmatter alone.

## `## Why Discarded`

Purpose: **the reason this file was abandoned**, recorded once on the `→ discarded` transition. Single dated bullet, append-only:

```markdown
## Why Discarded

- 2026-05-08 14:32 superseded by `spec/14-cache-tiers.md`; this exploration is no longer load-bearing.
```

Rules:

- Format `- <YYYY-MM-DD HH:mm> <reason text>`. Timestamp is KST. When the reason cites another file, use the backtick-wrapped backlink form per `./body-conventions.md`.
- Append-only — never edit or remove the bullet. If the discard rationale is later understood differently, append a second bullet rather than rewriting the first.
- Emit only when the file is at `status: discarded`. Files in any other lifecycle state must not carry this section.
- Applies uniformly to every issue type that has a `discarded` terminal status (`task`, `bug`, `spike`, `research`, `epic`, `usecase`, `spec`, `idea`, `brainstorm`). Per-type contracts do not redefine the format.

## Cross-references

- `./body-conventions.md` — common body rules (heading form, backlink form).
- `./<type>-authoring.md` — per-type contracts (which list `## Resume`, `## Log`, and `## Why Discarded` in their optional-sections menu).
