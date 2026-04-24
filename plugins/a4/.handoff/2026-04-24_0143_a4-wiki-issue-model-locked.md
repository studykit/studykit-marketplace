> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_0143. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: `a4/` as wiki + issues — design locked, implementation pending

This session converted the partially-drafted document-model redesign into a fully-specified ADR. The authoritative artifact is **`plugins/think/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — the next session should start by reading that file; it is intentionally self-contained.

No implementation landed this session. The design round covered everything that was open from the prior handoff (`.handoff/2026-04-23_2119_a4-rename-and-compass-index-dashboard.md`) **plus** several items that surfaced as the design was pressed: wiki update protocol, global id scheme, Obsidian-markdown adoption, relationship fields.

---

## What is now locked (vs. the prior handoff's "deferred" list)

All of these were open questions at the start of this session and are now decided in the ADR. The next session should treat them as closed unless it encounters a contradiction with real-code reality.

### Document model

- **Wiki + issue duality.** `a4/` is a git-native wiki (`context.md`, `domain.md`, `architecture.md`, `actors.md`, `nfr.md`, `bootstrap.md` — flat at root) **plus** an issue tracker (`usecase/`, `plan/`, `review/`, `decision/` — per-item files in folders).
- **File naming: `<id>-<slug>.md`.** Folder indicates type; no `uc-`/`iu-`/`rev-`/`d-` prefix.
- **Global monotonic ids.** Integer ids are unique across the entire `a4/` workspace (GitHub-issue semantics). Next id is `max(existing ids in a4/) + 1`. Implication: filename basename is globally unique; `[[3-search-history]]` resolves unambiguously.
- **All reviews consolidated under `review/`.** Stage association is carried by the `target:` frontmatter field, not by folder placement. The prior plan to put stage-scoped reviews under `usecase/review-*.md` and `plan/review-*.md` was reversed.
- **Open items / questions / findings unified into review items** with `kind: finding | gap | question`.
- **Derived views are never files.** UC diagram, authorization matrix, relationship graphs are rendered on demand via Obsidian dataview; compass regenerates a static markdown approximation into `INDEX.md`.

### Relationships (hybrid)

- **Structural relationships in frontmatter**, typed per semantic meaning: `depends_on`, `implements`, `target`, `wiki_impact`, `justified_by`, `supersedes`, `parent`, `related`.
- **Forward direction only is stored.** Reverse directions (`blocks`, `implemented_by`, `justifies`, `superseded_by`, `children`) are derived by dataview queries — do not add them as stored fields.
- **Soft references (mentions, see-also) go in body prose as Obsidian wikilinks**; Obsidian's built-in backlinks carry them. Do not force everything into frontmatter.

### Wiki update protocol (this was the biggest new piece)

- **Wiki pages carry no lifecycle but are continuously updated.** Trigger is related-issue state change, **not** calendar time. Date-based staleness was explicitly rejected.
- **Change tracking via footnotes.** Modified sections carry local sequential markers `[^1]`, `[^2]`; a `## Changes` section at file bottom resolves each to `YYYY-MM-DD — [[causing-issue]]`. The wikilink payload is the substantive cause.
- **All wiki edits flow through review items.** Three entry paths:
  1. **Single edit (active skill session)** — skill emits an in-situ nudge using already-loaded context; review item opens and resolves in the same flow.
  2. **Reviewer agent output** — review items carry `wiki_impact` in frontmatter; no mid-run nudge.
  3. **Bulk generation (auto-bootstrap etc.)** — skill calls drift detector as its final step; detector emits review items.
- **Nudge trigger.** Significant changes only (create / status transition / resolve). Minor edits do not nudge.
- **Close guard.** A review item with non-empty `wiki_impact` cannot transition to `resolved` until each referenced wiki page contains a footnote back to the causing issue. Enforcement is **warning with override**.
- **Footnote label at resolve time** points to the **causing issue** (e.g., `[[usecase/3-search-history]]`), not the review item id.
- **Drift detector** is shared logic invoked from three sites: bulk-generation skills (embedded), compass Step 3 (session audit), optional `/a4-drift` (manual).

### Authoring format

- **Obsidian markdown throughout.** Body uses wikilinks (`[[usecase/3-search-history]]`) and embeds (`![[usecase/3-search-history]]`). Frontmatter paths are plain strings (no brackets, no extension) for dataview compatibility. Review item body typically embeds its `target:` for visual context.

### Explicitly rejected (do not re-open)

- Active wiki updates (skill auto-edits wiki) — too invasive, clobbers human edits.
- Drift-detection-only without in-situ nudge — wastes already-loaded context.
- Type prefix in filenames, folder-scoped ids.
- Generic `related: [{kind, ref}]` as the only relationship mechanism.
- Explicit bidirectional relationship fields — doubles maintenance, risks drift.
- `archived: true` frontmatter (reaffirmed from prior handoff — folder is the flag).
- **Legacy migration tooling** — existing `visual-claude/A4/` and this plugin's prior `a4/` stay as-is; new model applies only to new workspaces and new items.

---

## Where to start next session

**Primary read:** `plugins/think/a4/2026-04-23-spec-as-wiki-and-issues.decide.md` — the complete design. Discussion Log at the end has two `<details>` blocks: the original session summary and the 2026-04-24 continuation added this session.

**Optional background:** `.handoff/2026-04-23_2119_a4-rename-and-compass-index-dashboard.md` — only if the next session needs to understand *how we got here*. The ADR supersedes it for decisions.

---

## Recommended first concrete task: Id allocator

Every other implementation step depends on this. The Next Steps list in the ADR has ~10 items; the correct starting order is:

1. **Id allocator utility** — a small shared helper that, given an `a4/` path, scans all issue files (`usecase/*.md`, `plan/*.md`, `review/*.md`, `decision/*.md`) and returns `max(id) + 1`. No state file, no counter persistence — always computed fresh. Must be used by every skill that creates an item to preserve monotonicity. Scope: ~30-50 lines.
2. **Drift detector** — shared scanner of wiki footnotes cross-checked against issue state; emits review items with `wiki_impact` set and `source: drift-detector`.
3. **In-situ nudge integration** in single-edit skills (`think-usecase`, `think-arch`, `think-plan`, `spark-decide`).
4. **Wiki update close guard** on the review-item-resolve path.
5. **Skill rewrites** for the new output format (per-item files, Obsidian markdown, id allocator usage, nudge emission).
6. **Compass redesign** — Step 0 INDEX refresh adapted to new layout; Step 3 now includes drift detection.
7. **INDEX redesign** for single-workspace (topic × stage grid no longer meaningful).
8. **Spark skill alignment** — resolves the original status-field conflict that triggered this whole redesign.
9. **Obsidian dataview reference snippets** + **Obsidian markdown conventions doc**.

Full list (including the schema-finalization remainder) is in the ADR's Next Steps section.

---

## Open ambiguities (fine to resolve as encountered)

These were deferred rather than decided; address each when you hit it.

- **YAML grammar for path references** — the ADR proposes plain string (no brackets, no `.md` extension). Verify this works cleanly with dataview before propagating to all schema docs.
- **Issue comment/log section format** — the ADR mentions `## Log` for issue comments but does not lock the format. Defer until the first skill actually needs it.
- **Exact per-type lifecycle vocabularies** — sketched in the ADR (UC: `draft | implementing | done | blocked`; IU: `pending | implementing | complete | failing`; review: `open | in-progress | resolved | dismissed`; decision: `final`). Tune when skills are being rewritten.

---

## Non-goals for the next session

- **Do not design a legacy migration.** Explicitly rejected this session. New model applies only going forward.
- **Do not reintroduce type prefixes** (`uc-`, `iu-`, `rev-`, `d-`) in filenames.
- **Do not switch to folder-scoped ids.** Global monotonic is the decision.
- **Do not add `archived: true`** (reaffirmation from prior handoff).
- **Do not build active wiki updates** where skills silently edit wiki pages. Use the nudge + review-item conduit.
- **Do not add reverse-direction relationship fields** (`blocks`, `implemented_by`, etc.) as stored frontmatter — compute via dataview.

---

## Session changes committed

Working tree change as of this handoff: addition of the decision record file (previously untracked) plus this handoff. No code changes; this was a design round only.

- **Modified/added:**
  - `plugins/think/a4/2026-04-23-spec-as-wiki-and-issues.decide.md` — extended from initial draft to fully-specified ADR. Added: wiki update protocol section, updated frontmatter schemas (global ids, relationship fields, `wiki_impact`), 8 new rejected alternatives, expanded Next Steps, continuation Discussion Log.
  - `plugins/think/.handoff/2026-04-24_0143_a4-wiki-issue-model-locked.md` — this file.
- **No code or skill files modified.**
