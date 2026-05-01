---
sequence: 12
timestamp: 2026-05-01_2218
timezone: KST +0900
topic: a4-resume-context
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-05-01_2218. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## Goal

Make a4 workspace files self-sufficient for cross-session resume, so that opening a single `a4/<type>/<id>-<slug>.md` in a fresh Claude Code session is enough to continue the work — no transcript, no separate handoff, no UC/spec hop required.

The driving observation: when a user resumes work via a new session, the prior conversation is gone, but the workspace files are not. Whatever is needed to continue must live in those files. Today the workspace records the *what* (description, files, AC) but not the *where-am-I* (current approach, blockers, decisions, next step). That gap was filled in this session.

A second, related gap: when one session manipulates several sibling tasks together, no a4 file naturally hosts the cross-cutting narrative. UC and spec are wrong homes (their `## Log` is for the artifact's own evolution, not implementation progress). This session introduced a new `umbrella` type purpose-built for that aggregation home.

## Current State

- Branch: `main` at `2911cb70e feat(a4)!: make a4 files self-sufficient for cross-session resume`. Working tree clean.
- a4 plugin version bumped 17.2.0 → 18.0.0 in `.claude-plugin/marketplace.json`.
- `uv run plugins/a4/scripts/validate.py plugins/a4` clean (frontmatter / status / transitions OK).
- All design decisions committed to authoring contract docs and the validator. No in-flight work, no pending TODOs in source.

## Changes Made

Single squash commit `2911cb70e`. Inspect with:

```bash
git show 2911cb70e --stat
git show 2911cb70e -- plugins/a4/authoring/body-conventions.md
git show 2911cb70e -- plugins/a4/authoring/frontmatter-universals.md
git show 2911cb70e -- plugins/a4/authoring/umbrella-authoring.md
git show 2911cb70e -- plugins/a4/scripts/markdown_validator/frontmatter.py
git show 2911cb70e -- plugins/a4/skills/handoff/SKILL.md
```

Substantive shifts:

- **`## Log` redefined as resume-context surface.** No longer a status-transition log; now the agreed home for what a fresh reader can't reconstruct from frontmatter / required body sections / git / linked review items. Strongly recommended while the file is mid-flight. Inline cross-reference rule: a Log entry that depends on narrative recorded elsewhere (most often a parent / umbrella) must inline-cite the path inside the entry, so a reader who opens this file alone can discover the next file. Frontmatter `parent:` makes the parent *discoverable*; the inline citation makes it *necessary to read* — only when the entry actually depends on it.
- **`parent:` loosened to cross-type within the issue family.** Issue-family files (`task` / `bug` / `spike` / `research`) accept any other issue-family file as parent (e.g., `bug` with `parent: task/<id>`, `task` with `parent: spike/<id>`). `usecase` and `spec` stay same-type. Validator enforces target-type and rejects self-reference (`parent-target-type` and `parent-self-reference` violations).
- **New `umbrella` type for narrative aggregation.** Folder `a4/umbrella/<id>-<slug>.md`. Minimal frontmatter (no `cycle` / `implements` / `spec` / `depends_on` / `artifacts` / `parent` — all forbidden). Body required: `## Description`, `## Children`, `## Log`. Lifecycle: `open` ↔ `complete`, `→ discarded`. Author-judged, no automatic cascade from children. Children point at it via `parent: umbrella/<id>-<slug>`.
- **Handoff gate.** `plugins/a4/skills/handoff/SKILL.md` step 1 now updates touched files' `## Log` first (the per-artifact resume context). Step 3 applies an explicit gate: a session handoff file is created **only when session-level meta exists** (a4-anchorless work, session-level validation, important user dialog, non-obvious branch state, anchor-less cross-cutting decision). Sessions whose entire substance fits inside the touched files' Logs skip the handoff file entirely.
- **Validator additions.** `parent` registered as `path_scalar_fields` for task/bug/spike/research/usecase/spec. New `_validate_parent_target` enforces the family-target rules. New `umbrella` schema with the type's forbidden-fields set. `_PARENT_ALLOWED_FOLDERS` for issue-family children includes `umbrella`.
- **Status model.** `STATUS_BY_FOLDER["umbrella"]`, `UMBRELLA_TRANSITIONS`, `TERMINAL_STATUSES`, `IN_PROGRESS_STATUSES` registered. `ISSUE_FOLDERS` in `common.py` includes `umbrella`.
- **Path-purity cleanup.** Removed `/a4:handoff` and `/a4:validate` skill citations from `body-conventions.md` and `frontmatter-universals.md` (authoring/ must not cite skills).

## Key Files

- `plugins/a4/authoring/body-conventions.md` — `## Log` redefinition + inline cross-reference rule + example. The single source of truth for entry shape and what to write vs. not.
- `plugins/a4/authoring/frontmatter-universals.md` — `parent` row updated, family/type tables include umbrella, "`parent` and cross-cutting narrative" subsection covers the two roles (derivation vs. aggregation).
- `plugins/a4/authoring/umbrella-authoring.md` — full authoring contract for the new type. "When to create / when not to" criteria, frontmatter, lifecycle, body shape.
- `plugins/a4/authoring/{task,bug,spike,research}-authoring.md` — `parent:` field added to each per-type table; "Parent and shared narrative" subsection explains derivation vs. umbrella aggregation.
- `plugins/a4/authoring/{usecase,spec,review}-authoring.md` — `## Log` one-liner reframed to resume-context language.
- `plugins/a4/scripts/markdown_validator/frontmatter.py` — `umbrella` schema, parent validation (`path_scalar_fields` + `_validate_parent_target`), `_PARENT_ALLOWED_FOLDERS` mapping.
- `plugins/a4/scripts/status_model.py` — umbrella enums and transitions.
- `plugins/a4/scripts/common.py` — umbrella in `ISSUE_FOLDERS`.
- `plugins/a4/skills/handoff/SKILL.md` — two-part handoff (in-file Log + conditional session file), gate criteria, step renumbering, output branches.
- `.claude-plugin/marketplace.json` — a4 version 18.0.0.

## Related Links

No external links (GitHub issues, PRs) for this thread — the work was repo-internal authoring + validator changes. The thread's history is the commits leading up to `2911cb70e`.

## Decisions and Rationale

These are the load-bearing choices the next session should not relitigate without good reason:

- **`## Log` is for resume context, not status transitions.** Earlier the section was "hand-maintained status-transition narrative". That role overlaps with `updated:` and the cascade hook; reframing the section as resume-context made it valuable enough to recommend strongly while mid-flight.
- **UC and spec `## Log` is NOT the home for implementation aggregation narrative.** The user explicitly rejected the option of routing cross-cutting implementation decisions into the UC/spec Log. UC = user-facing definition narrative. Spec = design decision narrative. Implementation progress that spans tasks is a different category and goes to issue-family parents or umbrella.
- **`parent` is one field for both derivation and aggregation.** Derivation (a `task` from a `spike`) and aggregation (an `umbrella` for several siblings) share the same field. The reverse `children` lookup finds every child regardless of parent kind. Keeping a single field avoids two-field bookkeeping.
- **Cross-type within the issue family for `parent`.** Initially considered keeping same-type only. Loosened because real workflows produce cross-family relationships (task → bug, spike → task, etc.) that previously had no frontmatter representation.
- **Umbrella does not follow issue body shape.** No `## Files`, no `## Unit Test Strategy`, no `## Acceptance Criteria` required. The work belongs to children; the umbrella exists only to host narrative. User explicitly said "umbrella가 기존 issue 포맷을 따라 갈 필요는 없어 보이는데" — that reframed the type to be deliberately lightweight.
- **Author-judged umbrella lifecycle, no auto-cascade.** Considered automatically flipping umbrella `complete` when all children reach `complete`. Rejected — author may keep umbrella open intentionally for follow-up children. Drift detector can surface "all children terminal but umbrella open" as a soft signal in the future.
- **No nested umbrellas in v1.** `parent:` is forbidden on umbrella. If deeper grouping is needed, reorganize children rather than introducing umbrella-of-umbrellas.
- **Handoff file is conditional.** Sessions that touch a single mid-flight task and update its Log do not need a separate handoff file — the Log is the resume context, and an empty-shell handoff is the failure mode the gate exists to prevent.
- **Path-purity rule strict in authoring/.** No `/a4:...` skill citations in authoring/ docs. They are the contract; skills consume the contract. Existing violations from before this session were also cleaned up where surfaced.
- **`/a4:roadmap` and `/a4:run` workflows not modified.** User explicitly scoped them out: "roadmap 스킬은 현재 논의 대상이 아님" and "왜 자꾸 run과 연동을 하는지". Whatever umbrella-aware behavior those skills should grow is a separate decision for a future session.

## Important Dialog

Direct user signals that shaped the design (paraphrased; original Korean):

- "task 문서만 읽어도 되게 만들고 싶은데" — original framing of the goal.
- "재개할때 필요한 context를 담고 싶은거지. 어떤 스킬을 시작해라 이런 걸 의미하는건 아님." — Log content scope: just the context, not action prescriptions.
- "status 전이보다 더 중요한건. claude code를 새로 시작했을때 필요한 정보를 기록하는거임." — anchor for what counts as a Log entry.
- "왜 자꾸 run과 연동을 하는지?" — kept `/a4:run` out of scope.
- "umbrella task에 기록을 하는게 맞지 않을까?" — origin of the parent / umbrella thread.
- "같은 타입이 아니어도 parent가 되게 만들면 될텐데." — drove cross-type parent within the issue family.
- "parent cross-type은 issue간 cross type인데." — clarified that wiki types stay same-type.
- "spec과 uc에 들어가는 내용과 작업을 하면서 기록하는 내용으느 달라야 할걸로 보임." — locked the decision against routing implementation narrative into UC/spec.
- "umbrella가 기존 issue 포맷을 따라 갈 필요는 없어 보이는 데" — drove umbrella as a separate, minimal type.
- "B" — chose the gate-based handoff path (file created only when session-level meta exists).

## Validation

- `uv run plugins/a4/scripts/validate.py plugins/a4` → frontmatter / status / transitions all OK.
- Smoke fixture for `parent` validation (temporary `/tmp/parent_test/` workspace, since cleaned up): confirmed `task → spike` parent passes, `usecase → task` parent rejected with `parent-target-type`, `spec → spike` parent rejected, `task → self` rejected with `parent-self-reference`.
- Smoke fixture for `umbrella` validation (temporary `/tmp/umbrella_test/`): confirmed valid umbrella + child `parent: umbrella/...` passes; an umbrella with `implements:` / `parent:` / `cycle:` is caught with three `type-field-forbidden` errors.
- Smoke fixture for hook path resolution (`uv run --with pyyaml /tmp/probe.py`): confirmed `_resolve_type_from_path` returns `"umbrella"` for `a4/umbrella/<id>-<slug>.md` paths, and `${plugin_root}/authoring/umbrella-authoring.md` exists.
- No unit tests exist in the validator or scripts directories. The above smoke-test fixtures are the only behavioral verification.

## Known Issues and Risks

- **No unit-test coverage.** The validator changes (parent target type, umbrella schema) were verified by ad-hoc temp fixtures only. A regression in `_validate_parent_target` or the umbrella schema would not surface until someone authors a real umbrella file.
- **No `## Children` ↔ reverse-`parent:` consistency check.** Authors can add children via `parent:` without updating the umbrella's `## Children` body, and vice versa. Drift is silent. A validator pass that compares the two surfaces would catch this; out of scope this session.
- **No "all children terminal but umbrella open" drift detector.** Documented in `umbrella-authoring.md` as a future-detector candidate.
- **`/a4:roadmap` is not umbrella-aware.** When the roadmap skill batches multiple tasks for a UC, no umbrella is created. Result: cross-cutting narrative across roadmap-spawned tasks has no home unless authors create umbrellas after the fact. Whether `/a4:roadmap` should auto-create an umbrella per UC batch is the largest open product question.
- **`/a4:run` is not umbrella-aware.** The implementation loop does not read or update umbrella `## Log`. Cross-task decisions made during `/a4:run` (e.g., a coder agent making a choice that affects sibling tasks) are not auto-captured.
- **No `/a4:umbrella` skill.** Users currently have no command surface for creating an umbrella file. They must hand-author at `a4/umbrella/<id>-<slug>.md` and remember to allocate an id via `scripts/allocate_id.py`. A `/a4:umbrella` ad-hoc skill (cousin of `/a4:task`) is the obvious follow-up.
- **`scripts/allocate_id.py` umbrella support unverified.** Not exercised in this session. If the allocator walks `ISSUE_FOLDERS` (which now includes umbrella), it will Just Work. Worth confirming before the first real umbrella authoring attempt.

## Next Steps

In rough priority order. None are blockers; this session's core deliverable is shipped.

1. **Audit remaining `/a4:...` and `${CLAUDE_PLUGIN_ROOT}/skills/...` citations in `plugins/a4/authoring/*.md`.** Run `git grep -n '/a4:\|skills/' plugins/a4/authoring/`. This session removed two. Others may exist (e.g., references to `/a4:run`, `/a4:roadmap`).
2. **Verify `scripts/allocate_id.py` umbrella behavior.** Spot-check that allocator uses `ISSUE_FOLDERS` from `common.py` and therefore covers umbrella ids. If not, add umbrella to whatever folder list it consults.
3. **Decide on `/a4:umbrella` skill.** Either author the skill (mirror of `/a4:task` shape) or document explicitly that umbrella authoring is hand-only. Without a skill, the type is hard for users to discover.
4. **Decide on `/a4:roadmap` umbrella behavior.** Should roadmap auto-create an umbrella per UC batch? Per cycle? Never (umbrella stays user-driven)? This is a product decision, not a mechanical one. The cleanest answer is probably "user-driven only in v1; reconsider after dogfooding" but it should be explicit.
5. **Add `## Children` ↔ reverse-`parent:` consistency check.** Validator pass that compares the umbrella body's `## Children` list to the set of files whose frontmatter `parent:` resolves to that umbrella. Surface drift as a warning.
6. **Add "all children terminal but umbrella open" drift detector.** Soft signal; not an error. Useful as a heads-up.
7. **Mention umbrella exclusion in `task-family-lifecycle.md`.** One-line note that umbrella has its own lifecycle separate from the four issue families.
8. **Consider unit tests.** The validator's growing set of cross-file checks (parent target type, parent self-reference, umbrella forbidden fields) would benefit from a small `pytest` fixture. None exist today.

## Open Questions

- **Should `/a4:roadmap` auto-create umbrellas?** Currently no. Likely the right answer for v1, but the cost of leaving it manual is that LLM-driven sessions (which already split larger work into multiple tasks) will keep producing parentless task batches with cross-cutting decisions homeless.
- **What about umbrella-of-spec / umbrella-of-UC?** This session locked `parent:` on issue-family children to "issue-family or umbrella" only. UCs cannot have an umbrella parent. If a user wants to group several specs under shared narrative, there's no mechanism. Likely fine — spec aggregation rarely needs a narrative home — but worth confirming in real use.
- **Should umbrella appear in `scripts/search.py` results by default?** It's already in `FORWARD_FIELDS` for `parent`-traversal. CLI surface (`--folders`, `--type`) inherits from `ISSUE_FOLDERS` so it should work. Not verified.
- **Naming.** "umbrella" was the user's term. Acceptable, but "epic" or "group" might read better in some contexts. Not changing now; flagging in case it grates later.

## Useful Commands and Outputs

```bash
# Inspect the squash commit
git show 2911cb70e --stat
git show 2911cb70e -- plugins/a4/authoring/umbrella-authoring.md

# Run validators on the workspace
uv run plugins/a4/scripts/validate.py plugins/a4
uv run plugins/a4/scripts/validate.py plugins/a4 --only frontmatter
uv run plugins/a4/scripts/validate.py --list-checks

# Search for forward-`parent:` references in a workspace (umbrella discovery)
uv run plugins/a4/scripts/search.py --references-via parent

# Verify path-purity in authoring/
git grep -n '/a4:\|\${CLAUDE_PLUGIN_ROOT}' plugins/a4/authoring/

# List authoring contracts (ensure umbrella is present)
ls plugins/a4/authoring/*-authoring.md

# Smoke-test umbrella schema with a fixture (template)
mkdir -p /tmp/u_test/a4/{umbrella,task}
cat > /tmp/u_test/a4/umbrella/1-foo.md <<'EOF'
---
type: umbrella
id: 1
title: "Foo"
status: open
created: 2026-05-01
updated: 2026-05-01
---
## Description
Test.
## Children
- [task/2-bar](../task/2-bar.md)
## Log
- Approach: test.
EOF
uv run plugins/a4/scripts/validate.py /tmp/u_test/a4 --only frontmatter
rm -rf /tmp/u_test
```
