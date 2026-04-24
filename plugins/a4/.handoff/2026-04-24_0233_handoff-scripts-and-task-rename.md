---
timestamp: 2026-04-24_0233
topic: a4-redesign
previous: 2026-04-24_0143_a4-wiki-issue-model-locked.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_0233. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: task/plan rename + handoff-system script foundations

This session produced two inter-locked rounds of work on the `a4-redesign` thread. **Primary read for the next session is the ADR** (see "Where to start" at the end); this handoff is the narrative wrapper.

The frontmatter above demonstrates the new handoff schema (`topic`, `previous`, `timestamp`) designed this session, though the `think-handoff` skill that would enforce it is not yet built — this file was still written by the global `/handoff` skill.

---

## Session narrative — what happened and why

### Round A: `plan/` → `task/` rename, `plan.md` wiki added

**Entry point.** The prior handoff (`2026-04-24_0143_a4-wiki-issue-model-locked.md`) had identified "Id allocator utility" as the first concrete task. Implementation started there.

**The surface.** A `uv`-powered inline-deps Python script at `plugins/think/scripts/allocate_id.py`. Scans `a4/{usecase,plan,review,decision}/*.md`, extracts `id` frontmatter, returns `max(id) + 1`. Supports `--list` and `--check` for debug / duplicate detection.

**The pivot.** While defining `ISSUE_FOLDERS = ("usecase", "plan", "review", "decision")`, the user noticed a semantic conflation: the files being allocated lived in `plan/`, but each file was Jira-task-shaped (title, `implements: [usecase/...]`, `files: [...]`, `cycle: N`, acceptance criteria). The ADR's label was "Implementation Unit"; in Jira vocabulary that is a **task** — a unit of executable work. The actual **plan** document (the narrative that says "build X first, then Y, organized in these phases") had no home.

**Reference case.** `visual-claude/a4/terminal-markdown-renderer.plan.md` — a 1214-line file that aggregates an Overview + Technology Stack + Implementation Strategy + 16 Implementation Units. After splitting IUs to per-file tasks, the remaining narrative is ~150–250 lines: genuinely plan-shaped, clearly distinct from per-task content.

**Decision.**
- Folder rename: `a4/plan/` → `a4/task/`. Each file is a Jira task.
- New wiki page: `a4/plan.md` at root (flat wiki, same tier as `context.md` / `architecture.md`). Single file, milestone structure via `## Milestones` / `### v1.0 — Foundation` sections.
- No `design.md`. `architecture.md` already covers stack, components, interfaces, test strategy; a parallel `design.md` would force an unmaintainable boundary.
- No per-milestone plan files. Post-task-extraction narrative is thin; cross-milestone sequencing is the plan's core value and wants to stay in one file. Revisit only if a project grows past ~10 milestones.
- No separate `phase:` frontmatter field. `milestone:` already carries phase semantics.

**ADR impact.** `plugins/think/a4/2026-04-23-spec-as-wiki-and-issues.decide.md` was edited in-place across ~10 spots (duality table, directory layout, conventions bullets, wiki-kind enum, task frontmatter example, UC relationship example, rejected alternatives). A new "round 3 continuation" block was added to the Discussion Log documenting the full rationale.

**Allocator impact.** `ISSUE_FOLDERS` updated to `("usecase", "task", "review", "decision")`. One-line change, re-verified.

### Round B: handoff management system — design + script foundations

**User trigger.** On opening the prior handoff in the IDE, the user said "handoff 문서도 체계적으로 관리해야 한다" and gave concrete requirements:

1. Location: `<project-root>/.handoff/` (not plugin-scoped, not under `a4/`).
2. Pain point 1: cannot tell which handoffs belong to the same topic thread.
3. Pain point 2: not drift — **duplication** between handoff bodies and `a4/` content is the burden. Use script/hook to **inject** needed `a4/` sections, at heading granularity.

**Design iteration — what was decided.**

| Axis | Decision | Rejected alternatives |
|------|----------|----------------------|
| Location | `<project-root>/.handoff/`, detected via `git rev-parse --show-toplevel` | `a4/handoff/` (session artifact, not project artifact — different semantics), `plugins/<plugin>/.handoff/` (plugin-scoped is too narrow) |
| Filename | `<TIMESTAMP>_<slug>.md` (existing convention retained) | — |
| Frontmatter | `timestamp`, `topic`, `previous` only | `references:` field (forces duplication; body is already authoritative) |
| Topic format | slug `[a-z0-9-]+` (B2) | free-form string (B1) — group-key normalization wins over authorial freedom |
| Reference extraction | **Body only**: Obsidian wikilinks `[[...]]` / `![[...]]` + `<!-- injected: ... -->` markers | Frontmatter `references:` field (duplicates body intent) |
| Injection timing | **Write-time** (snapshot frozen; safe from a4/ drift) | Read-time (violates handoff immutability; handoff would change view as a4/ evolves) |
| Injection syntax | `![[path#heading]]` (Obsidian-native embed) | Custom `{{include: ...}}`, HTML-comment-only directives |
| Section granularity | Heading + content until the next same-or-higher heading | Whole-file only, line-range based |
| Skill name | `think-handoff` (plugin-scoped, coexists with global `/handoff`) | Overriding `/handoff` in plugin — coexistence is safer |

**Four scripts built** (all in `plugins/think/scripts/`, all PEP 723 inline-deps, all verified with mktemp test corpora):

1. **`allocate_id.py`** (91 lines, pyyaml) — next-id allocator for `a4/`. Now tracks `task/` folder (post-rename).
2. **`extract_section.py`** (83 lines, stdlib) — extract one markdown heading section by text match. First occurrence, exact match, includes heading line + contents until next same-or-higher heading.
3. **`inject_includes.py`** (133 lines, stdlib) — expand `![[path#heading]]` / `![[path]]` directives in-place. Output wraps each injection as `<!-- injected: path#heading @ date -->` / content / `<!-- /injected -->`. Non-embed `[[...]]` wikilinks are left untouched. Fails fast on missing file / missing heading.
4. **`topic_references.py`** (138 lines, pyyaml) — scan `.handoff/*.md` bodies, extract references via wikilink + injection-marker regexes, group by frontmatter `topic:`. Modes: default list, `--filter <prefix>`, `--with-handoffs` (inverse), `--list-topics`. Paths emitted **verbatim** (Obsidian convention: `.md` elided from wikilinks), no normalization — previous draft's `PurePosixPath.suffix`-based normalization mis-handled the `*.decide.md` compound-extension pattern used by this plugin's own ADR files.

---

## Current state — what exists, what doesn't

### Exists (committed as part of this handoff)

- **ADR:** `plugins/think/a4/2026-04-23-spec-as-wiki-and-issues.decide.md` — round 3 continuation block added; directory layout, frontmatter schemas, and rejected alternatives updated for task/plan split.
- **Allocator:** `plugins/think/scripts/allocate_id.py` — `ISSUE_FOLDERS = ("usecase", "task", "review", "decision")`, PEP 723 with `pyyaml>=6.0`.
- **Handoff infrastructure scripts:** `extract_section.py`, `inject_includes.py`, `topic_references.py`.
- **Version bump:** `think` plugin `0.15.0` → `0.16.0` in `.claude-plugin/marketplace.json` (per CLAUDE.md's versioning rule — new features in an existing plugin).

### Does not exist yet (next session's work)

- **`think-handoff` skill** — orchestrates the four scripts into a /handoff-invokable flow. This was designed but not implemented. Until it exists, handoffs are still written by the global `/handoff` skill (as this very file was), which does not enforce the new schema or perform write-time injection.
- **`.handoff/INDEX.md`** — topic-grouped dashboard, was explicitly deferred ("다음 라운드").
- **Drift detector** — ADR's #2 priority; still pending.
- **Skill rewrites** — `think-usecase` / `think-arch` / `think-plan` / reviewer agents all pending the new per-item-file + wiki-page format.

### Schema demonstration vs enforcement — mind the gap

This handoff's frontmatter uses the new schema (`topic`, `previous`, `timestamp`). However, the file lives at `plugins/think/.handoff/` (the legacy plugin-scoped location), **not** at `<project-root>/.handoff/` (the designed location). Reason: existing handoffs are there, `topic_references.py` takes any directory as input, and the `think-handoff` skill that would enforce project-root placement is not built yet. Treat this as a transitional state — the split between old and new locations resolves when `think-handoff` lands and either migrates or starts fresh at project root.

---

## Where to start next session

### Primary reads

1. **`plugins/think/a4/2026-04-23-spec-as-wiki-and-issues.decide.md`** — the authoritative ADR. Read at minimum the two `<details>` continuation blocks in the Discussion Log (2026-04-24 and 2026-04-24 second round). These cover every decision from the last two sessions.
2. **This handoff** — narrative context for what happened between ADR snapshots.

### Optional reads (for specific concerns)

- `plugins/think/scripts/*.py` — each file's docstring is the usage spec; read the top of the file.
- `plugins/think/.handoff/2026-04-24_0143_a4-wiki-issue-model-locked.md` — the prior handoff. Superseded in part (id allocator "next task" is done; folder names updated), but the overall model framing is still accurate.

### Recommended next concrete task: build `think-handoff` skill

The four underlying scripts are ready and verified. The skill wraps them:

1. Detect project root: `git rev-parse --show-toplevel`. Fail clearly if not in a git repo.
2. Ensure `<root>/.handoff/` exists (create if missing).
3. Prompt the author (or auto-populate from session context) for: `topic` slug, `slug` for filename, and a body draft that may include `![[path#heading]]` directives.
4. Determine `previous:` — the latest `.handoff/*.md` with the same `topic:` (or null if this is the first on that thread). `topic_references.py --list-topics` + sorted-by-timestamp listing of that topic's handoffs does this.
5. Run `inject_includes.py <draft> --base-dir <project-root> --date <today>` and capture stdout.
6. Write `<root>/.handoff/<TIMESTAMP>_<slug>.md` with the new frontmatter schema.
7. Stage the handoff and any pending working-tree changes, commit.

The skill should live at `plugins/think/skills/think-handoff/SKILL.md`. Follow the conventions of existing think-plugin skills.

### Subsequent sequence (per ADR Next Steps, adjusted)

1. `think-handoff` skill (above)
2. Handoff INDEX (`.handoff/INDEX.md`, dataview + static fallback, driven by `topic_references.py`)
3. Drift detector (ADR's second-priority item — unchanged)
4. In-situ nudge integration in single-edit skills
5. Wiki update close guard
6. Skill rewrites for new layout
7. Compass + INDEX redesign
8. Spark skill alignment
9. Obsidian dataview reference snippets

---

## Explicitly rejected — do not re-open

From this session specifically:
- **`design.md`** as a separate wiki page alongside `architecture.md`.
- **Per-milestone plan files** (`milestone/v1.md`, etc.).
- **`plan/` folder** for per-task files (the name misled — it is now `task/`).
- **Separate `phase:` frontmatter field** on tasks (`milestone:` covers it).
- **`references:` frontmatter field** on handoffs (body is the source of truth).
- **Frontmatter-based reference extraction** for `topic_references.py`.
- **Normalizing wikilink paths** with `.md` append/strip in `topic_references.py` — verbatim emission is correct (respects Obsidian convention and this plugin's `*.decide.md` compound-extension pattern).
- **Read-time injection** of handoff content (violates immutability).
- **Building `think-handoff` before the scripts existed** — scripts-first was the right order; skill now has solid primitives.

Carried from prior rejections (still in force):
- Active wiki updates (skill silently edits wiki) — use nudge + review-item conduit.
- Reverse-direction relationship fields in frontmatter — compute via dataview.
- `archived: true` frontmatter — folder is the flag.
- Type prefix in filenames (`uc-`, `task-`, `rev-`, `d-`).
- Folder-scoped ids — global monotonic only.
- Legacy migration tooling — new model applies to new content only.

---

## Working-tree state at handoff time

Changes bundled into this handoff's commit:

```
modified:   .claude-plugin/marketplace.json                          # think 0.15.0 → 0.16.0
modified:   plugins/think/a4/2026-04-23-spec-as-wiki-and-issues.decide.md
new file:   plugins/think/scripts/allocate_id.py
new file:   plugins/think/scripts/extract_section.py
new file:   plugins/think/scripts/inject_includes.py
new file:   plugins/think/scripts/topic_references.py
new file:   plugins/think/.handoff/2026-04-24_0233_handoff-scripts-and-task-rename.md
```

No prior commits were made during the session; everything lands in this one handoff commit.

---

## Non-goals for the next session

- Do not retrofit existing handoffs into the new schema. Let `think-handoff` start fresh; migration is not worth it (handoffs are point-in-time snapshots).
- Do not move prior handoffs from `plugins/think/.handoff/` to `<project-root>/.handoff/`. New handoffs go to project root once the skill lands; old ones stay.
- Do not build drift detector before `think-handoff` — resumption infrastructure comes first.
- Do not introduce `design.md`, per-milestone plan files, `phase:` field, or `references:` frontmatter (all rejected this session).
- Do not normalize wikilink paths in `topic_references.py` — verbatim emission is the current (correct) behavior.
