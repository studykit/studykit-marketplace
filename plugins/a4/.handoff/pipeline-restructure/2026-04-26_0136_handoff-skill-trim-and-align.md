---
timestamp: 2026-04-26_0136
topic: pipeline-restructure
previous: 2026-04-26_0103_adr-trigger-detection-shipped.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-26_0136. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Pipeline restructure — handoff skill trim & pipeline-align

## Session context

Continuation of the pipeline-restructure thread from `2026-04-26_0103_adr-trigger-detection-shipped.md`. That handoff's "How to resume" listed three follow-on candidates (#14′, CLAUDE.md companion-list extension, `refresh_research_citations.py`); the user did not pick from that list. Instead the session opened a **topic-organization sweep** (`topic 정리`) — verifying that the skills referenced in the prior handoff actually reflect what was shipped, and pulling any cleanup forward.

The sweep produced two outcomes on disk:

1. **`decision/SKILL.md` cross-check** — confirmed every claim in the 0103 handoff (C4·C5 changes) is present, and committed the one pre-existing pre-session edit that was already in the working tree (Plugin meta-ADR fallback removal).
2. **`handoff/SKILL.md` pipeline alignment + structural trim** — added the pipeline-context bumps the prior topic had implied but not propagated, deleted the unused transclusion infrastructure (`inject_includes.py`), and trimmed mentions of the global `/handoff` skill plus the now-unnecessary callout how-to.

Three commits shipped (all on `main`); the handoff commit will make four for this session.

## Topic backlog at session end

| ID | Title | Status |
|---|---|---|
| #1–#7 | (see prior handoffs) | completed |
| #15′ | ADR-trigger detection | completed (prior session) |
| **handoff-skill alignment** | propagate Topic #15′ consequences into `handoff/SKILL.md`; drop dead transclusion infra | **completed this session** |
| #14′ | drift_detector staleness propagation, wiki-wide (covers original #14 + downstream-direction A1 + A4 temporal-staleness + `## Changes` advance → propagate-to-dependents) | pending |
| (consideration) | `plugins/a4/CLAUDE.md` always-read-first list extension — now a 5-file question (`wiki-authorship.md`, `skill-modes.md`, `iterate-mechanics.md`, `pipeline-shapes.md`, `adr-triggers.md`) | pending |
| (deferred) | `refresh_research_citations.py` SessionStart safety net for the C4 atomic registrar | pending — add only if real-world drift surfaces |

## What shipped this session

Three commits on `main`:

| SHA | Subject |
|---|---|
| `54b4488ca` | refactor(a4): drop plugin meta-ADR fallback from decision skill |
| `7b038d6b9` | refactor(a4): align handoff skill with pipeline; drop unused inject_includes |
| (handoff) | docs(handoff): snapshot pipeline-restructure session state |

`marketplace.json` `a4` version: unchanged (1.31.0). These are skill prose / dead-code cleanups, not new behavior — no version bump.

### `54b4488ca` — decision/SKILL.md: drop Plugin meta-ADR fallback

The bullet under Step 5 body-structure rules (about how to write `## Next Steps` for ADRs in `plugins/a4/spec/` when there is no `<project-root>/a4/task/` workspace) was the lone exception to the skill's workspace-only design. Pre-flight already aborts when `<project-root>/a4/` is missing, and `plugins/a4/CLAUDE.md` states `plugins/a4/spec/` is **not** a skill output. The bullet documented a case the skill never handles. This edit existed in the working tree at session start as a pre-session diff; verified its direction matches the workspace-only invariant and committed it.

No other inconsistencies between `decision/SKILL.md` and the 0103 handoff's claims about C4·C5 — every Step-3 / Step-5 / Step-5b / Step-2 bullet from the prior topic is present and accounted for.

### `7b038d6b9` — handoff/SKILL.md: pipeline-align + transclusion infra removal

Two independent threads bundled because they touch the same file:

**A. Pipeline-context bumps (consequences of Topic #15′).**

- **Section 3** now requires the footnote protocol from `references/obsidian-conventions.md §Wiki Update Protocol` for any wiki edit, and explicitly states that any `## Changes` entry on `architecture.md` must include a `[[decision/<id>-<slug>]]` wikilink — `drift_detector` raises a `missing-adr-cite` gap otherwise (the C1 detector shipped in 0968fa53e). It also forbids hand-editing decision/research citation state and embeds the exact registrar invocation:

  ```bash
  uv run "${CLAUDE_PLUGIN_ROOT}/scripts/register_research_citation.py" \
      "<project-root>/a4" \
      "research/<slug>" \
      "decision/<id>-<slug>"
  ```

  Form matches `decision/SKILL.md` Step 5b verbatim.

- **Section 4 carry-forward enum** gains `[[research/<slug>]]` for in-flight investigations (`status: draft` only — `final` / `standalone` / `archived` artifacts are not carry-forward). Adds an explicit pre-write sweep against `references/adr-triggers.md` (B1–B6 + content-aware upward propagation) so missed ADR moments are caught before they freeze into free-text carry-forward; mandates `/a4:decision` to create a draft first if one is warranted. The free-text-prohibition paragraph also picks up `/a4:research` as another tracker-creation path.

**B. Transclusion infrastructure removal.**

- `plugins/a4/scripts/inject_includes.py` deleted. Codebase audit showed:
  - **Zero usage history.** No past handoff contains the `<!-- injected: -->` marker. The four prior handoffs in `pipeline-restructure/` mention `![[…]]` only inside backticks as prose explaining the convention.
  - **Trade-off was wrong direction.** The script's whole point was write-time snapshot for handoff immutability, but the cost was: transclusion directives lost (no Obsidian click-through), embedded headings collide with host outline, HTML-comment audit markers invisible in Obsidian preview. For a feature no one used, the renderer-correctness cost was paid every conceptual write.
- **Section 4** now explicitly **prohibits** `![[…]]` inside handoffs (live transclusion would let a past handoff silently mutate as the source drifts) and tells the writer to paste verbatim text with a plain path+date attribution when a frozen excerpt is genuinely needed. Format is the writer's call — Obsidian callout syntax is **not** taught (the reader is already in Obsidian).
- **Section 5** ("Expand embed directives") removed entirely. Remaining sections renumbered (old #5→removed, old #6→#5, old #7→#6). Section 5's body plate `<expanded body from step 5>` rewritten to `<draft body from step 4>`.

**C. Trim global-skill mentions.**

The intro line *"Complements the global `/handoff` skill"* and the invocation footnote about disambiguating from `/handoff` were removed — the a4 variant stands on its own. `frontmatter.description` slug aligned to `/a4:handoff` (the actual invocation name) for cleaner skill-trigger matching.

## Things deliberately not done

- **No `refresh_research_citations.py`.** Status unchanged from 0103 — atomic registrar remains the only write path; SessionStart back-scan remains deferred.
- **No `plugins/a4/CLAUDE.md` always-read-first list extension.** Same status — pending consideration. The candidate set is now 5 files (the original 4 + `adr-triggers.md`).
- **No Topic #14′ (drift_detector wiki-wide propagation).** Untouched — requires git/mtime infrastructure not yet planned.
- **No automated migration of past handoffs.** None contained real `![[…]]` directives, so there is nothing to rewrite. The four prior pipeline-restructure handoffs render correctly in Obsidian today.
- **No update to `marketplace.json`.** This session is prose + dead-code cleanup, not feature behavior. Version stays at 1.31.0.
- **No push.** 47 commits ahead of `origin/main` (44 prior + 2 refactor commits this session + the handoff commit will be 47).

## Key reference documents the next session should know about

- **`plugins/a4/skills/handoff/SKILL.md`** — now Obsidian-native: live `[[…]]` for pointers, prohibition on `![[…]]` transclusion, hand-attributed verbatim excerpts. Section 3 enforces wiki footnote protocol + register_research_citation.py for any pipeline-touching session. Section 4 carry-forward enum includes `[[research/<slug>]]` and an `adr-triggers.md` pre-sweep mandate.
- **`plugins/a4/skills/decision/SKILL.md`** — workspace-only invariant restored (no plugin-meta-ADR fallback bullet). All C4·C5 changes from 0103 verified present.
- **`plugins/a4/scripts/inject_includes.py`** — **deleted**. Do not re-create. If a future need arises for frozen embed snapshots, prefer hand-written attributions over write-time transformation; transclusion vs. snapshot is fundamentally a UI/intent choice and the writer should make it consciously per excerpt.
- **`plugins/a4/references/adr-triggers.md`** *(from prior session)* — now load-bearing for `handoff/SKILL.md` Section 4's pre-write sweep. Any change to its trigger taxonomy (B1–B6, content-aware upward propagation) propagates into how handoff carry-forwards are built.
- **`plugins/a4/references/obsidian-conventions.md §Wiki Update Protocol`** — newly cited from `handoff/SKILL.md` Section 3. The cross-skill citation pattern (handoff → conventions → wiki edit footnote shape) is now consistent with `/a4:decision`'s wiki-nudge step.

## Citation convention (preserved)

Same as last session — for any `plugins/a4/` doc:

- Plugin-internal markdown link citations: `${CLAUDE_PLUGIN_ROOT}/<plugin-internal-path>`. No relative `../`.
- Shell commands: `${CLAUDE_PLUGIN_ROOT}/scripts/...`.
- Inline prose to current skill's own files: `${CLAUDE_SKILL_DIR}/references/...`.
- `<project-root>/a4/` workspace docs (user output): Obsidian `[[wikilinks]]` and `![[embeds]]`.

Note that the last bullet — workspace docs allowing `![[embeds]]` — is **not** contradicted by this session's `![[…]]` prohibition: that prohibition applies *only* to handoff documents under `<project-root>/.handoff/`, where snapshot-immutability is the requirement. User-output workspace docs (`a4/architecture.md`, `a4/roadmap.md` etc.) continue to use Obsidian transclusion freely.

## How to resume

1. **Pick the next topic.** The carry-forward set has not changed since 0103, except this session is now closed:
   - **#14′** (drift_detector staleness propagation, wiki-wide) — concrete code change. See 0103 handoff for the full scope description; nothing was done on it this session.
   - **CLAUDE.md companion-list extension** — small one-shot. Now a 5-file question (the original 4 + `adr-triggers.md`).
   - **`refresh_research_citations.py`** — defer-this-session item still deferred.
   User has not signaled preference; ask.

2. **Discussion-first remains the default.** Per session-specific guidance, present options + recommendation, accept user's pick, then execute. Auto mode tends to be on; the pick is the action trigger.

3. **Conflict audit before implementing.** This session's pre-implementation audit caught both the inject_includes-zero-usage finding and the workspace-only-vs-plugin-meta-ADR inconsistency in decision/SKILL.md. Future implementation work should run a similar audit — read the SKILL.md / scripts / schema before writing code, surface conflicts, decide before editing.

## Working tree state

Clean. Three commits this session, one more for the handoff. Commits ahead of `origin/main`: 47 (44 prior + 2 refactor commits + the handoff commit).

## Session insight worth keeping

Two patterns reinforced from prior sessions, both about *removing* rather than building:

1. **Audit before propagating.** The 0103 handoff claimed certain changes shipped; the cross-check found every claim accurate, but also surfaced one pre-session edit (`decision/SKILL.md`) that was on theme and unfinished. Topic-organization sweeps are cheap and frequently turn up loose ends that "feel" done but aren't on `main`.

2. **Dead infrastructure is liability, not optionality.** `inject_includes.py` was a working, tested, documented script — and its existence forced ongoing trade-offs (Obsidian convention compliance vs. immutability) for a feature no one used. Removing it simplified the skill's mental model and made the Obsidian-native rendering choice unambiguous. Generalizes the 0103 lesson (*"don't add detection when the work belongs at the moment of authoring"*) to: **also remove infrastructure when the work belonged at the moment of authoring all along**.
