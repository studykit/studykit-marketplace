# Gap Diagnosis (Step 3.3)

Trace from foundation to execution against the workspace state collected in Step 3.2. Stop at the first layer that has actionable work. For a targeted Step 1.1 argument, focus the trace on layers upstream of the target (e.g., a blocked task points back to its `depends_on` predecessor).

## 3.3.0 Detect shape

Layer 0 and Layer 1 below are **Full / Reverse-then-forward only** — they assume a UC-driven pipeline with the canonical wiki chain. Minimal-shape and Reverse-only workspaces have legitimately empty UC sets or upstream wikis and would be mis-diagnosed by those layers. Detect shape from current state per [`pipeline-shapes.md`](${CLAUDE_PLUGIN_ROOT}/docs/pipeline-shapes.md) §"Shape detection" before tracing:

| State | Shape | Layer 0/1 behavior |
|---|---|---|
| `bootstrap.md` absent, `usecase/*.md` absent | No shape | Skip Layer 0/1; route via Step 2 catalog instead — gap diagnosis does not apply |
| `bootstrap.md` present, `usecase/*.md` absent | Minimal | **Skip Layer 0 and Layer 1.** No-UC is by design; jump to Layer 2 |
| `usecase/*.md` present, all with `source: auto-usecase`, `bootstrap.md` absent | Reverse-only | Skip Layer 0; run Layer 1 only for `domain.md` (the natural Reverse-then-forward continuation step). If user signals "documentation only," skip Layer 1 too |
| `bootstrap.md` present + `usecase/*.md` present (Full / Reverse-then-forward) | Full | Run Layer 0 and Layer 1 normally |
| `bootstrap.md` absent + `usecase/*.md` present (mixed `source:`) | Full in progress | Run Layer 0 and Layer 1 normally |

Carry the detected shape into the diagnosis report (Step 3.4) so the user sees the assumption.

## Layer trace

**Layer 0 — Workspace foundation** *(Full / Reverse-then-forward only)*. Does the workspace have any use cases yet?
- No UCs → recommend `/a4:usecase` (interactive) or `/a4:auto-usecase` (autonomous).

**Layer 1 — Wiki foundation** *(Full / Reverse-then-forward only; Reverse-only runs `domain.md` check only)*. Is each wiki page that has dependent issues present? Check in pipeline order (`usecase → domain → architecture → bootstrap → roadmap`); stop at the first missing layer.
- UCs exist, `domain.md` missing → recommend `/a4:domain` (cross-cutting concept extraction is its own skill, not part of `/a4:usecase`).
- `domain.md` exists, `architecture.md` missing → recommend `/a4:arch`.
- `architecture.md` exists, `bootstrap.md` missing → recommend `/a4:auto-bootstrap`.
- `bootstrap.md` exists, `roadmap.md` missing, tasks expected → recommend `/a4:roadmap`.
- Any issue's `wiki_impact:` references a non-existent wiki page — the drift detector emits this as a high-priority `missing-wiki-page` finding; pick it up in Layer 2.

**Layer 2 — Drift alerts.** Any open `review/*.md` with `source: drift-detector`?
- High priority first (`close-guard`, `missing-wiki-page`). Each item's `target:` or `wiki_impact:` tells you which iteration skill owns the fix: `architecture`/`domain`/etc. → `/a4:arch iterate`; `usecase/*` → `/a4:usecase iterate`; `task/*` → `/a4:roadmap iterate` or `/a4:run iterate`.

**Layer 3 — Open review items (non-drift).** Any other open review items?
- Sort by `priority` (high → medium → low) then by `created:`. Recommend the iteration skill that owns each item's `target:`. Route by target: `architecture` / `architecture` `wiki_impact` → `/a4:arch iterate`; `domain` / `domain` `wiki_impact` → `/a4:domain iterate`; `usecase/*` / `actors` / `context` / `nfr` → `/a4:usecase iterate`; `task/*` / `roadmap` → `/a4:roadmap iterate` or `/a4:run iterate`.

**Layer 4 — Active tasks.** Any `task/*/*.md` (recursing through `feature/`, `bug/`, `spike/`) with `status: pending | progress | failing`?
- Yes → recommend `/a4:run iterate` (resume implementation).

**Layer 5 — Blocked items.** Any item with `status: blocked`?
- Read its `depends_on` chain to find the nearest unblocked predecessor; recommend the skill that owns that predecessor.

**Layer 6 — Completion.** Everything `done` / `complete` / `resolved` / `final`?
- Suggest either a new iteration (fresh UCs for the next milestone) or per-item archive of any targeted closed item (see SKILL.md Step 3.5).
