---
timestamp: 2026-04-24_2213
topic: decision-slot-unification
previous: 2026-04-24_2138_retire-decision-review-introduce-decision-skill.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_2213. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

Continuation of the `decision-slot-unification` thread. The preceding handoff (`2026-04-24_2138`) closed the skill-shape redesign (retired `/a4:decision-review`, introduced `/a4:decision` and `/a4:research-review`). That handoff's "Plausible follow-ups" #2, #3, and #7 flagged specific unclosed gaps around **status transitions that the schema claims are derived but no automation actually enforces** — specifically `decision.superseded` and `brainstorm.promoted`/`idea.promoted`.

This session closed those gaps via report-only enforcement. The user's directive was explicit at three junctures:

1. **"superseded는 값 수동업데이트 아닌데. 다른 파생 status가 있음."** — Pushed back when my first answer described `superseded` as a manual update. I was prompted to survey the entire schema for derived statuses, inventory who actually writes each value, and identify gaps.
2. **"상태가 맞지 않다는걸 알려주는 용도이면은 됨. hook으로 관리할 예정."** — Scope locked to report-only (not mutate) + hook-based delivery.
3. **"SessionStart 에서 처음에 판단하여 LLM에 알려주기. 그리고 파일 변경이 있는 경우, status 정합성 알려주기."** — Two hook sites: SessionStart for initial read; file-change for ongoing.
4. **"관련 issue끼리 연결해서 보면 되는건데. 전부 볼 필요 없이."** — Rejected the initial workspace-wide scan per PostToolUse. Required scoping to the edited file's "related set" (connected component via supersedes / self-contained for idea/brainstorm). Non-applicable edits (usecase/task/wiki) must be silent even if legacy mismatches exist elsewhere.

# Status enum survey (drives the scope)

Done this session as part of the cross-family audit. Recording here for future sessions; the survey does not live in the schema doc.

| Family | Enum | Who writes each value |
|---|---|---|
| usecase | `draft`/`implementing`/`done`/`blocked` | skills write draft/implementing/done; `blocked` is auto-set by `usecase-reviser` (SPLIT) and `/a4:plan` (upstream blocker) |
| task | `pending`/`implementing`/`complete`/`failing` | all four driven by `/a4:plan` (Step 2.2 around task-implementer, Step 2.3 around test-runner) |
| review | `open`/`in-progress`/`resolved`/`dismissed` | reviewer agents / drift-detector / iterate flows (`resolved`) write these |
| decision | `draft`/`final`/`superseded` | `/a4:decision` writes draft/final from natural-language signals; **`superseded` has no writer** — schema L209 declares it derived from another decision's `supersedes:` but no skill/script flips it |
| idea | `open`/`promoted`/`discarded` | `/a4:idea` writes `open`; `promoted`/`discarded` are manual per `spec/2026-04-24-idea-slot.decide.md:133-137` |
| brainstorm | `open`/`promoted`/`discarded` | `/a4:spark-brainstorm` writes `open`; `promoted`/`discarded` are manual (no auto back-reference from `/a4:decision`) |

**Scripts and hooks do not write status anywhere.** Confirmed — `index_refresh.py`/`drift_detector.py`/validators are all read-only on status. This means the "gap" for derived statuses is enforced nowhere *at write time*. This session's choice was to make the absence of enforcement **visible** via report-only validation, rather than to automate the transition.

The three mismatches the validator checks are the ones without automated writers: `decision.superseded`, `idea.promoted`, `brainstorm.promoted`. `blocked`/`failing`/`complete`/`resolved` are considered "derived" in informal usage but have skill-level writers (`/a4:plan`, `usecase-reviser`, iterate flows) — those are explicitly **out of scope**.

# Rejected alternatives (discussed, not taken)

- **Auto-mutate the old decision when a new decision declares `supersedes:`.** User rejected mutation as a category: "상태가 맞지 않다는걸 알려주는 용도이면은 됨." Report-only was locked before implementation started. Also would have complicated the reverse case (removing a supersedes entry should presumably un-`superseded` — nontrivial to get right).
- **Fold the new check into `drift_detector.py` and emit review items** (extend the existing drift-detector pattern). Considered but not chosen: drift_detector's output is review items (mutation — creates `a4/review/*.md`). User wanted inform-only, so a fresh validator in the `validate_*` family is the right home, not drift.
- **Workspace-wide scan on every PostToolUse.** This was the first implementation, rejected by the user ("전부 볼 필요 없이"). Caused every `a4/` edit — including unrelated `usecase`/`task`/wiki edits — to re-inject the full list of legacy mismatches into the LLM context. Replaced with file-scoped (`--file`) mode.
- **Tighten the PostToolUse matcher to only fire on `decision/`, `idea/`, `spark/*.brainstorm.md` paths.** Mentioned as a pre-filter optimization. Not done because `--file` mode already makes the validator return `[]` for non-applicable paths, so the matcher-narrow would have been belt-and-suspenders. Kept the broad matcher (`a4/*.md`) so the validator owns the applicability decision.
- **Add the consistency check to the Stop hook too.** Explicitly surveyed and declined. The existing Stop hook (`validate-edited-a4.sh`) is structured for blocking `exit 2`; mixing non-blocking additionalContext into it violates its shape. SessionStart + PostToolUse already cover both "remind at session begin" and "alert on each edit," so Stop would duplicate.

# What got built (8 files, commit `8d25019a2`)

**New validator**
- `plugins/a4/scripts/validate_status_consistency.py` — rules checked:
  1. `decision.status = superseded` ↔ another decision declares `supersedes: [<this>]`. Two directions flagged: `stale-superseded-status` (status=superseded without anyone targeting), `missing-superseded-status` (targeted but status≠superseded).
  2. `idea.status = promoted` ↔ own `promoted:` list non-empty. `empty-promoted-list-idea` / `missing-promoted-status-idea`.
  3. `spark/*.brainstorm.md status = promoted` ↔ own `promoted:` non-empty. Same two rule names with `-brainstorm` suffix.
  4. `superseded-target-missing` — decision's `supersedes:` points at a file that doesn't exist.
- Two modes:
  - **Workspace mode** (`<a4-dir>`): scan everything, report all.
  - **File-scoped mode** (`<a4-dir> --file <path>`): scope to connected component.
    - `idea/<id>-<slug>.md` / `spark/*.brainstorm.md` — self-contained, reads only that file.
    - `decision/<id>-<slug>.md` — reads `decision/` folder (for reverse lookup), filters output to `{X} ∪ X.supersedes ∪ {Y : X ∈ Y.supersedes}`.
    - Other paths under `a4/` (usecase/task/review/wiki) — returns `[]` immediately, hook stays silent.
- CLI shape matches `validate_frontmatter.py` / `validate_body.py`: accepts absolute or workspace-relative `--file`, supports `--json`, exit 2 on mismatch / 0 clean / 1 on usage error.

**New hooks**
- `plugins/a4/hooks/report-status-consistency-session-start.sh` — SessionStart. Workspace scan. Wraps validator stderr into a markdown block with a rule summary; emits `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}` via stdout JSON. Always exits 0; silent on clean workspace or any internal error.
- `plugins/a4/hooks/report-status-consistency-post-edit.sh` — PostToolUse (`Write|Edit|MultiEdit`). Reads `tool_input.file_path` from stdin JSON; passes it as `--file <abs-path>` to the validator. Silent on clean, on non-`a4/` files, on non-`.md` files, on missing `CLAUDE_PLUGIN_ROOT`/`CLAUDE_PROJECT_DIR`. Always exits 0. First line of the injected additionalContext names the edited file path so the LLM has concrete provenance.

**Hook registration**
- `plugins/a4/hooks/hooks.json` — new entries added to both `PostToolUse` (alongside the existing `record-edited-a4.sh`) and `SessionStart` (alongside `sweep-old-edited-a4.sh`). Existing Stop (`validate-edited-a4.sh`) and SessionEnd (`cleanup-edited-a4.sh`) untouched. `description` field at top of file extended to mention both flows (blocking single-file validation + non-blocking cross-file consistency).

**Skill integration**
- `plugins/a4/skills/validate/SKILL.md` — `/a4:validate` now runs three validators. Step 4 (new) runs `validate_status_consistency.py` in workspace mode; explicitly skipped when `$ARGUMENTS` names a single file (consistency is global by definition). Step 5 (was Step 4) rewritten for three-validator aggregate reporting. Step 6 (was Step 5) — suggest-follow-up — unchanged in spirit, renumbered.

**Docs**
- `plugins/a4/README.md` — Skills table description updated (`validate` mentions three validators); Hooks section split into two flows (single-file validation blocking vs. cross-file consistency non-blocking) with the two new hooks tabulated; scope paragraph clarifies workspace-wide vs. scoped behavior.
- `plugins/a4/references/frontmatter-schema.md` — new `### Cross-file status consistency` subsection under Validator behavior, with a table of derived values and a two-mode description; Cross-references adds the new script.

**Version**
- `.claude-plugin/marketplace.json` — a4 `1.6.0 → 1.7.0`.

# Verification performed

- **Script AST parse** — clean.
- **Workspace mode** — synthetic fixture with 5 mismatches (`missing-superseded`, `stale-superseded`, `missing-promoted-idea`, `empty-promoted-idea`, `missing-promoted-brainstorm`) + 1 dangling supersedes target → validator reports all 6, exit 2. Clean workspace → `OK`, exit 0. `--json` mode emits well-formed JSON with the same exit codes.
- **File-scoped mode**, case matrix:
  - `--file decision/<edited>` where the chain is `1-a ← supersedes ← 2-b` and `3-c` has an unrelated stale status: editing `2-b` → only `1-a missing-superseded` reported, `3-c` stale not in output.
  - `--file decision/3-c.md` → only `3-c stale-superseded` reported.
  - `--file decision/1-a.md` → `1-a missing-superseded` (reverse lookup finds `2-b`).
  - `--file idea/<stuck>.md` → that idea's mismatch only; other ideas' legacy mismatches not reported.
  - `--file idea/<ok>.md` → clean.
  - `--file spark/<...>.brainstorm.md` → that brainstorm only.
  - `--file usecase/<anything>.md` → clean (no rule applies), even though the same workspace has unrelated decision/idea mismatches.
  - `--file` with absolute path → same result as workspace-relative.
- **PostToolUse hook end-to-end** — stdin JSON payload piped to the shell script; verified the emitted JSON matches the `hookSpecificOutput.additionalContext` schema from Claude Code's hooks docs. Confirmed silent (rc 0, no output) on:
  - edits outside `a4/`,
  - edits in `a4/` but outside applicable families (e.g., `usecase/`), even when legacy mismatches exist in `decision/`/`idea/`,
  - clean workspace edits.
- **SessionStart hook** — same payload protocol; confirmed additionalContext injection on dirty workspace and silence on clean.
- **`hooks.json` / `marketplace.json`** — valid JSON per Python `json.load`.
- Manual read of the skill and README updates.

# Explicitly untouched

- **`validate-edited-a4.sh`** (Stop hook). Stays on `validate_frontmatter.py` + `validate_body.py` only; keeps its `exit 2` blocking semantics. The new consistency check is NOT added here by design (see rejected alternatives). Result: frontmatter/body issues still force the LLM to fix before Stop; status-consistency issues inform but don't block.
- **`record-edited-a4.sh` / `cleanup-edited-a4.sh` / `sweep-old-edited-a4.sh`**. Unchanged. Edit-record accumulation and cleanup is orthogonal to consistency checking.
- **`validate_frontmatter.py` / `validate_body.py`**. Unchanged. They check per-file schema; consistency check is a sibling with different scope.
- **`drift_detector.py`**. Unchanged. It produces review-item files (a different output kind — mutation, not report). The new consistency script is strictly read-only.
- **Decision frontmatter schema.** `status` enum `draft | final | superseded` unchanged; `supersedes:` list unchanged. The new script reads the same fields, does not add any.
- **Skills that write decision/idea/brainstorm files.** `/a4:decision`, `/a4:idea`, `/a4:spark-brainstorm` untouched. They continue to NOT auto-flip related files' statuses. The consistency script compensates by making the resulting drift visible.
- **Idea's manual promotion procedure at `spec/2026-04-24-idea-slot.decide.md:133-137`.** Unchanged. The script will catch it if the user opens the file, sets `promoted: [...]`, but forgets to flip `status`.
- **arch's `a4/research/<label>.md`** cache. Same carve-out as preceding handoffs. Still separate from project-root `./research/`.

# Design notes for future sessions

- **Two-mode shape is load-bearing.** Workspace mode answers "what's broken anywhere?" and drives `/a4:validate` + SessionStart. File-scoped mode answers "what's broken involving this file?" and drives PostToolUse. Mixing modes would either spam legacy mismatches (workspace on every edit) or hide global state (scoped on session start). Keep them separate.
- **`--file` silently returns `[]` for non-applicable paths** (usecase/task/review/wiki). This is intentional: lets the PostToolUse hook fire on ANY `a4/*.md` edit without a narrow matcher, and the validator owns the applicability decision. If a future rule family extends to e.g. usecase/task coherence, the same shape generalizes — add a new branch in `collect_file_mismatches`, no hook change.
- **"Connected component" is defined symmetrically via `supersedes:`.** For decision X: X + targets(X) + reverse-referrers(X). If a future schema change makes some decisions point at others via a different relationship field, extend `_decision_component`; do not add new relationship fields without also updating the component computation.
- **Rule coverage is specifically the three without skill-level writers.** Don't add `blocked` or `failing` to this validator — those have skill writers (`/a4:plan`, `usecase-reviser`). Doing so would create double enforcement and bypass the skills' lifecycle logic.
- **Hook output is `hookSpecificOutput.additionalContext` via stdout JSON, exit 0.** This is non-blocking by design. If a future redesign wants blocking enforcement, create a separate script/hook; do not change this one's exit code semantics.

# Plausible follow-ups (not done; user has not requested)

1. **Real-world smoke test in a live `a4/` workspace.** This session tested on synthetic fixtures only. A first real run will reveal whether the additionalContext payload size is reasonable for typical workspaces (1-2 mismatches is tiny; 20+ could dominate context). If it becomes noisy, consider a deduplication/summarization step in the hook.

2. **Hook noise profile during large-scale editing.** A skill that does 10+ `Edit`s on decision files in sequence will fire the PostToolUse hook 10+ times. Each fires a `decision/` folder scan. At typical workspace sizes this is fine, but if scans become slow, memoize the decision set across the session (e.g., cache file with a timestamp).

3. **Extend to `complete`/`failing` on tasks.** Currently out of scope because `/a4:plan` owns those. But if a task file is ever manually edited (bypass the skill), there's no validator to catch an inconsistent `complete` claim. Low priority unless such drift surfaces.

4. **`blocked` coherence across `depends_on` chains.** A usecase whose `depends_on` targets are all `done` should arguably not be `blocked`. Currently no automation — this session deliberately didn't go there. Keep as a future thread if dependency-graph mechanics become a focus.

5. **Mutation alternative.** If the report-only stance proves too passive in practice — users keep leaving mismatches uncorrected — the reversible escalation is to add a `/a4:fix-status-consistency` skill (user-invoked, not a hook) that applies the implied transitions with user confirmation. Don't fold this into `/a4:decision` or `/a4:idea` themselves; keep the write point separate.

6. **`supersedes` removal case.** If a user edits `decision/2-new.md` and removes `supersedes: [decision/1-old]`, the old file's `status` (if flipped to `superseded` previously) is now incorrect. The current script detects this as `stale-superseded-status` on 1-old. Report-only is sufficient — but if auto-mutation ever comes (see #5), this reverse case needs an explicit design round; removing `supersedes` shouldn't silently un-`superseded` a decision that might have been manually set `superseded` for other reasons.

7. **Stop hook report-only channel.** Was considered and declined this session. If a future session decides the SessionStart + PostToolUse coverage has a gap (e.g., manual user edits outside Claude's editing tools that don't trigger PostToolUse), revisit. Would go in a separate Stop hook, not folded into `validate-edited-a4.sh`.

8. **Integrate brainstorm `status → promoted` back-reference into `/a4:decision`.** This was already flagged as follow-up #7 in the preceding handoff. Status today: still not done. The new validator at least makes the resulting inconsistency visible if a user records a decision from a brainstorm and forgets to update the brainstorm's `status`/`promoted:`. If the pattern of forgetfulness surfaces, the right fix is a confirmation step at the end of `/a4:decision`, not a hook mutation.

# Key files to re-read on the next session

- `plugins/a4/scripts/validate_status_consistency.py` — the validator. `collect_file_mismatches` / `_decision_component` define the scoping logic; change rules only by editing `check_superseded` / `check_promoted`.
- `plugins/a4/hooks/report-status-consistency-post-edit.sh` / `report-status-consistency-session-start.sh` — the two hooks. Payload format (`hookSpecificOutput.additionalContext`) and silent-on-clean behavior are load-bearing.
- `plugins/a4/hooks/hooks.json` — current hook registration. Reference point if adding more hooks.
- `plugins/a4/skills/validate/SKILL.md` — three-validator flow; how `[file]` mode skips consistency; aggregate-report language.
- `plugins/a4/references/frontmatter-schema.md §Cross-file status consistency` — the canonical user-facing description of the rules.
- `plugins/a4/README.md` — Hooks section (two flows), Skills table row for `validate`.

# Outstanding parked threads (unrelated to this session)

- `decision-slot-unification` thread itself continues — the three preceding handoffs (`2026-04-24_2033`, `2026-04-24_2117`, `2026-04-24_2138`) remain valid context for the skill-shape side of the same data. This handoff extends the thread on the enforcement-infrastructure side.
- `a4-redesign`, `experiments-slot`, `idea-slot` — unaffected.
