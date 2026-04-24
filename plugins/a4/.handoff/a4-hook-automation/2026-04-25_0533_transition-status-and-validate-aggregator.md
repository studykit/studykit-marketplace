---
timestamp: 2026-04-25_0533
topic: a4-hook-automation
previous: 2026-04-25_0449_drift-index-migrate-and-render-fix.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_0533. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

Continued the scripts-modularization thread from the prior handoff. Three moves:

1. **Migrate `transition_status.py` to shared modules** — the last remaining script in the unshared regime. 16 call sites of `split_frontmatter` consolidated through a `_parse` shim over `markdown.parse`; local `normalize_ref` dropped in favor of `common.normalize_ref`.
2. **Analysis: "should the status transition state machine be extracted?"** — evaluated, deferred. No second consumer; only `transition_status.py` uses the tables.
3. **Analysis + execution: "should the three `validate_*` scripts be unified?"** — evaluated (full-merge pros/cons), user chose the **thin aggregator** middle path. Implemented: each validator now exposes a pure `run()` library API, and a new `scripts/validate.py` composes them into one entrypoint. `/a4:validate` SKILL.md simplified from three sequential `uv run` steps to one.

Three commits land on top of `a73270152` (last commit before this session):

- `ef54b5567` — refactor(a4): migrate transition_status to shared modules.
- `691843694` — feat(a4): add validate.py aggregator; simplify /a4:validate skill.
- (this handoff — separate commit per step 5).

a4 1.14.3 → **1.14.4** (transition refactor, patch, byte-identical) → **1.15.0** (aggregator + skill simplification, minor because a new public CLI lands).

Thread topic `a4-hook-automation` retained.

# What shipped this session

## `transition_status.py` — migrated (commit `ef54b5567`)

The biggest remaining target from the prior handoff. Removed:

- Local `split_frontmatter` (30-line function body).
- Local `normalize_ref` (identical to `common.normalize_ref`).
- `import yaml` (no direct `yaml.*` calls after dropping `split_frontmatter`).

Added a single 3-tuple adapter to preserve the CLI contract with minimal diff churn:

```python
from common import normalize_ref
from markdown import parse


def _parse(path: Path) -> tuple[dict | None, str, str]:
    """Preserves the pre-shared-module `split_frontmatter(path)` 3-tuple
    contract: (fm | None, raw_fm, body_content). `body_content` retains
    the leading newline from the closing-fence line; `write_file`
    applies `body.lstrip()` before emitting so output stays byte-
    identical. Substring-probing call sites (validation) are insensitive
    to the leading newline."""
    parsed = parse(path)
    return parsed.preamble.fm, parsed.preamble.raw, parsed.body.content
```

All 16 call sites swapped in one `replace_all` pass: `split_frontmatter(` → `_parse(`.

**Kept local** (transition-specific writers, no shared-module counterpart):

- `rewrite_frontmatter_scalar` (surgical `status:` / `updated:` rewrites preserving indent and surrounding lines).
- `append_log_entry` (`## Log` section appending).
- `write_file` (matches `refresh_implemented_by._write_file`, i.e. `body.lstrip()` on emit).

**PEP-723 dep** `pyyaml>=6.0` retained for transitive use (`markdown.parse` needs it).

### Verification (byte-identical)

Fixture: `/tmp/a4-transition-smoke/a4/` with usecase + task + review + decision + a supersedes pair on both UC and decision families. Two identical fixture copies, one run against HEAD's script, one against the migrated script.

Dry-run JSON diff — **7 scenarios byte-identical**:

- `--sweep --dry-run --json`
- `--file usecase/1-alpha.md --to implementing --dry-run --json`
- `--file usecase/2-beta.md --to shipped --dry-run --json` (supersedes cascade)
- `--file decision/5-pick.md --to final --dry-run --json` (supersedes cascade)
- `--file usecase/1-alpha.md --to discarded --dry-run --json` (task + review cascade)
- `--file usecase/2-beta.md --to revising --dry-run --json` (task reset cascade)
- `--file usecase/1-alpha.md --validate --to implementing --json`

Real-write sequence — `diff -r` of fixture trees after identical op chain (ready→implementing, task→complete, implementing→shipped with supersedes, draft→final with supersedes, sweep idempotency) showed **BYTE-IDENTICAL**.

### Scripts now in shared-module regime

Down from 1 to 0:

| Script | Shared-module migration | Notes |
|---|---|---|
| `drift_detector.py` | ✅ prior session | `_fm` shim over `extract_preamble` |
| `index_refresh.py` | ✅ prior session | `_fm` shim + local `WIKI_KINDS` ordered tuple |
| `refresh_implemented_by.py` | ✅ earlier | `_parse` adapter + `_write_file` template |
| `validate_frontmatter.py` | ✅ earlier (always used) | native shared-module consumer |
| `validate_body.py` | ✅ earlier | native shared-module consumer |
| `validate_status_consistency.py` | ✅ earlier | `_fm` shim present |
| `allocate_id.py` | ✅ earlier | uses `markdown.parse` |
| `transition_status.py` | ✅ **this session** | `_parse` adapter (3-tuple contract) |
| `inject_includes.py` | ❌ deliberately excluded | see prior handoff §`inject_includes.py` — explicitly NOT migrated |
| `a4_hook.py` | (dispatcher) | uses shared modules transitively |

**No scripts remain in the unshared regime** apart from the deliberate `inject_includes.py` exclusion.

## Analysis: separating the status-transition state machine (no action taken)

User asked whether the inline state-machine tables and validators in `transition_status.py` should be extracted into their own module (e.g. `state_machine.py`).

Reviewed structure:

- Pure tables: `UC_TRANSITIONS`, `TASK_TRANSITIONS`, `REVIEW_TRANSITIONS`, `DECISION_TRANSITIONS`, `FAMILY_TRANSITIONS`, `FAMILY_STATES` + `detect_family`.
- Mechanical validation: `validate_transition` + `_validate_{ready_to_implementing, revising_to_ready, implementing_to_shipped, draft_to_final}` — some read task files (I/O).
- Cascades: `_cascade_uc_{revising, discarded, shipped}`, `_cascade_decision_final` — all I/O by nature.

**Decision: defer.** Recorded rationale:

- No second Python consumer exists. Skills/agents all shell-out to `--validate --to X --json`; the CLI is the state-machine-as-a-service contract.
- Our shared-module playbook is "pull out once there is duplication" (precedent: `split_frontmatter` pulled after 4 local copies). Preemptive extraction for a single-consumer module contradicts it.
- Validation-I/O coupling means the extractable surface is ~50 lines (tables + `detect_family` + `validate_transition` dispatch). Small payoff vs. the file-boundary cost.
- Module-level tables already serve as self-documenting canonical source; moving them does not improve readability.

**Triggers that would re-open this**:

- A second Python-level consumer (read-only "would-be" reporter, batch validator, CI rule).
- Need to auto-generate a state diagram from the tables (e.g. mermaid in `references/`).
- If validation rules grow from 4 to 10+ per-transition and per-transition dispatch becomes the dominant code shape.

## `validate.py` — thin aggregator (commit `691843694`)

User explored "should the three `validate_*` scripts be unified into one?". Full review of options produced three candidates:

1. **Full monolith** — merge 1,276 lines into one file with `--kind frontmatter|body|status-consistency`. Rejected: unwieldy size, breaks direct per-script CLI, scope-creep risk.
2. **Keep three, add orchestrator** — status quo (skill runs three `uv run`s). Adequate but loses single-process wins.
3. **Thin aggregator + per-validator library API** — compact new `validate.py` composes three pure `run()` functions. Selected.

### Per-validator `run()` extraction

Each validator's `main()` now delegates to a pure library function with no I/O or exit:

```python
# validate_frontmatter.py
def run(
    a4_dir: Path, file: Path | None = None
) -> tuple[list[Violation], list[Path]]:
    """Library API: scan the workspace (or a single file) and return
    violations plus the files scanned. Pure — no stdout/stderr/exit."""
    files = [file] if file else discover_files(a4_dir)
    violations: list[Violation] = []
    for path in files:
        preamble = extract_preamble(path)
        if preamble.fm is None:
            missing = check_missing_frontmatter(path, a4_dir)
            if missing:
                violations.append(missing)
            continue
        violations.extend(validate_file(path, a4_dir, preamble.fm))
    if file is None:
        violations.extend(validate_id_uniqueness(a4_dir))
    return violations, files
```

Same shape for `validate_body.py`. `validate_status_consistency.py` uses a slightly different signature because it has no per-file violation lists, only global mismatches:

```python
# validate_status_consistency.py
def run(a4_dir: Path, file: str | None = None) -> list[Mismatch]:
    """Library API: workspace or file-scoped consistency check.
    When `file` is given, restrict to the connected component of that
    workspace-relative path (same semantics as the `--file` CLI flag).
    Pure — no stdout/stderr/exit."""
    if file:
        return collect_file_mismatches(a4_dir, file)
    return collect_workspace_mismatches(a4_dir)
```

Each `main()` remains as a thin shell: argparse → resolve paths → `run()` → render output → `sys.exit`.

### Aggregator design

`scripts/validate.py` is ~180 lines, PEP-723-headered, `uv run` friendly. CLI surface:

```
uv run validate.py <a4-dir>
uv run validate.py <a4-dir> <file>
uv run validate.py <a4-dir> --json
uv run validate.py <a4-dir> <file> --json
```

JSON shape:

```json
{
  "a4_dir": "...",
  "file": "idea/20-bad.md" | null,
  "frontmatter": {"scanned": [...], "violations": [...]},
  "body": {"scanned": [...], "violations": [...]},
  "status_consistency": {"skipped": bool, "mismatches": [...]}
}
```

Exit code: 2 if any category has violations, 0 clean, 1 usage error.

Human output: three stdout section headers (`=== frontmatter ===`, `=== body ===`, `=== status consistency ===`) with either `OK — N file(s) scanned, no ...` on stdout or `N violation(s)...` on stderr. Each per-category block is delegated to a local helper `_print_{frontmatter,body,status}` so the per-class violation formatting (field, line, rule, message) stays identical to what each script's own `main()` prints.

### Single-file mode: status consistency **skipped**

The aggregator mirrors the **prior SKILL.md convention**: when a file is passed, status-consistency is skipped (reports `{"skipped": true, "mismatches": []}` and "skipped (single-file mode; re-run without [file] for the workspace-wide check)"). Rationale:

- Preserves previous skill behavior verbatim — users running `/a4:validate <file>` before and after see the same verdict.
- The connected-component mode is still available via `uv run validate_status_consistency.py --file X` (inline comment in `validate.py` points at it). Surfacing it through the aggregator would be a behavior change; left as a potential follow-up.

### Individual scripts: CLI unchanged (byte-identical)

Verified against `git show HEAD:...` versions, 12 scenarios covering all flag combinations:

| Case | Result |
|---|---|
| `validate_frontmatter.py <a4>` | OK |
| `validate_frontmatter.py <a4> --json` | OK |
| `validate_frontmatter.py <a4> <file>` (abs) | OK |
| `validate_frontmatter.py <a4> <file> --json` (abs) | OK |
| `validate_body.py <a4>` | OK |
| `validate_body.py <a4> --json` | OK |
| `validate_body.py <a4> <file>` (abs) | OK |
| `validate_body.py <a4> <file> --json` (abs) | OK |
| `validate_status_consistency.py <a4>` | OK |
| `validate_status_consistency.py <a4> --json` | OK |
| `validate_status_consistency.py <a4> --file idea/20-bad.md` | OK |
| `validate_status_consistency.py <a4> --file idea/20-bad.md --json` | OK |

(`<file>` required absolute path because the two cwd-relative tests reported the cd'd-pwd root in the error — not a behavior difference, a fixture-path artifact.)

### Aggregator smoke

Fixture `/tmp/a4-vfx/a4/` with deliberate violations — frontmatter missing-required + enum-violation on task kind, and a `promoted`-with-empty-list idea for status-consistency. All four aggregator modes verified:

- workspace human: 5 frontmatter violations + 1 status mismatch, body OK, exit 2.
- workspace JSON: combined structure, `skipped: false`, exit 2.
- single-file human: 1 frontmatter violation, body OK, status `skipped`, exit 2.
- single-file JSON: same structure with `skipped: true`, `mismatches: []`, exit 2.

### SKILL.md simplification

`plugins/a4/skills/validate/SKILL.md` previously had **Step 2 / Step 3 / Step 4** (one per validator) plus Step 5 (surface combined) and Step 6 (suggest follow-up). Collapsed to:

- Step 1 — Verify the workspace exists (unchanged).
- Step 2 — Run the aggregator: `uv run validate.py <a4> $ARGUMENTS` (single call).
- Step 3 — Surface the result (was Step 5; the aggregator already labels sections so the skill can relay verbatim).
- Step 4 — Suggest a follow-up (was Step 6; unchanged).

The "status consistency skipped in single-file mode" nuance is **now owned by `validate.py`** (it prints the skip line). The skill just relays that.

### Per-class CLI continuity

SKILL.md explicitly calls out: *"Per-category CLI entrypoints (`validate_frontmatter.py`, `validate_body.py`, `validate_status_consistency.py`) remain available and unchanged — use them directly when you want a single class of check."* Reference docs (`frontmatter-schema.md`, `obsidian-conventions.md`) that mention per-class scripts are still accurate and were not touched.

## Output format note — stdout/stderr interleaving

Both pre-refactor and post-refactor, per-category violation bodies go to **stderr** and OK / section-header lines go to **stdout**. The aggregator preserves this. In a terminal, stderr lines may appear interleaved with stdout section headers; this matches the pre-refactor per-script behavior. Users piping to `jq` or filtering with `2>/dev/null` see the same semantics they always did. Not flagged as a bug; mentioned here for forward awareness.

# What's left

## New this session

- **Status-consistency connected-component mode through the aggregator.** Currently skipped in single-file mode (matches previous behavior). Could be promoted to "run with `--file X`" in `validate.py` — natural improvement, but a behavior change for `/a4:validate`. Defer until demand.
- **`run()` library API as a formal convention.** Three validators now have it. Consider documenting in `references/hook-conventions.md` under "Shared modules" (or a new "Validator composition" subsection) if the pattern gets reused — e.g. if `drift_detector.py` and `index_refresh.py` later need `run()` entrypoints for a drift+index aggregator.

## Carried from prior handoffs (unchanged)

- **Dispatcher end-to-end exercise in a real workspace.** Highest-value carried test; still unexercised.
- **`validate_body` off-by-one** (body line numbers via `Body.extract_headings`). Standalone loud commit when done.
- **Widen drift_detector's `ISSUE_FOLDERS`** to include `"idea"` — semantic decision, not a refactor. Affects wikilink resolution + next-id.
- **Unify `WIKI_KINDS` ordering** between `common.py` (frozenset) and `index_refresh.py` (ordered tuple). Not blocking; promote when a second ordered consumer appears.
- **Pre-existing dead import** `field` from `dataclasses` at `index_refresh.py:38`. Trivial standalone cleanup.
- **Symmetric trailing blank** in `index_refresh.render_section` (before `<!-- static-fallback-end -->`). Cosmetic.
- `transition_status.py --sweep` SessionStart hook.
- `compass` wrapper.
- SessionStart `systemMessage` for status-consistency-only output.
- Hard-fail surfacing design.
- Test harness for the dispatcher.
- Stop budget elasticity.

## Explicitly off the table (do not re-open without new signal)

- **State-machine extraction from `transition_status.py`.** See §Analysis above — rejected pending a second Python consumer. Re-open triggers documented.
- **Full-monolith validator unification.** Rejected this session; thin aggregator is the chosen shape.
- **`inject_includes.py` migration to shared modules.** Explicitly excluded per prior handoff (three behavior changes would hide behind a "refactor" label).

# Design decisions worth remembering

1. **`_parse` adapter is the idiomatic migration pattern for old `split_frontmatter(path)`-returning-3-tuple call sites.** `transition_status.py` now joins `refresh_implemented_by.py` in using it:

   ```python
   def _parse(path: Path) -> tuple[dict | None, str, str]:
       parsed = parse(path)
       return parsed.preamble.fm, parsed.preamble.raw, parsed.body.content
   ```

   The `body.lstrip()` on write compensates for the retained leading newline. `_fm` shim (prior handoff) is for sites that only read `fm`.

2. **Validators now expose a `run(a4_dir, file=None)` pure library API.** Signatures:
   - `validate_frontmatter.run(a4_dir, file: Path | None) -> (list[Violation], list[Path])`
   - `validate_body.run(a4_dir, file: Path | None) -> (list[Violation], list[Path])`
   - `validate_status_consistency.run(a4_dir, file: str | None) -> list[Mismatch]`

   `main()` delegates; aggregator composes via `import`. Future validators in this package should follow the same pattern so they compose into `validate.py` without further refactor.

3. **Thin aggregator > monolithic unification, until proven otherwise.** The thin aggregator keeps file-boundary cognitive separation, preserves per-class CLI, gains single-process execution + unified JSON + aggregate exit code. The monolithic approach would pay a 1,276-line file, break direct CLI paths, and invite scope creep.

4. **Aggregator behavior mirrors prior skill semantics by default.** `status_consistency` skipped in single-file mode. The connected-component mode exists on the individual script but is not plumbed through the aggregator — deliberate, keeps the behavior-change budget at zero for this commit.

5. **State machine stays inline in `transition_status.py`.** Extraction is a single-consumer cost. Documented triggers for re-opening above.

6. **Version bump policy (continuing prior convention)**:
   - Byte-identical refactor → patch (1.14.3 → 1.14.4).
   - New public CLI + user-visible skill simplification → minor (1.14.4 → 1.15.0).

# Explicitly untouched

- **`plugins/a4/hooks/hooks.json`** — unchanged.
- **`hooks/*.sh`** — unchanged.
- **`plugins/a4/references/*.md`** — unchanged. The per-class validator mentions in `frontmatter-schema.md` and `obsidian-conventions.md` are still accurate (individual scripts preserved). `hook-conventions.md §Shared modules` was considered for a `run()` convention note; deferred until a second reuse.
- **Other `/a4:*` skills** — unchanged. Only `skills/validate/SKILL.md` touched this session.
- **`drift_detector.py`, `index_refresh.py`, `allocate_id.py`, `refresh_implemented_by.py`, `a4_hook.py`** — unchanged this session (all prior-session migrations stand).
- **`common.py`, `markdown.py`** — unchanged.
- **`inject_includes.py`** — unchanged; still deliberately outside shared-module scope.

# Key files to re-read on the next session

- **`plugins/a4/scripts/validate.py`** — the new aggregator. Single file ~180 lines. Main + three `_print_*` renderers + sibling imports.
- **`plugins/a4/scripts/validate_frontmatter.py`** — `run()` at ~L366, `main()` at ~L395 delegates.
- **`plugins/a4/scripts/validate_body.py`** — `run()` at ~L297, `main()` at ~L316 delegates.
- **`plugins/a4/scripts/validate_status_consistency.py`** — `run()` at ~L417, `main()` at ~L429 delegates.
- **`plugins/a4/scripts/transition_status.py`** — `_parse` shim at ~L129, all 16 call sites use it. `normalize_ref` imported from `common`.
- **`plugins/a4/skills/validate/SKILL.md`** — collapsed to 4 Task steps.
- **`plugins/a4/.handoff/a4-hook-automation/2026-04-25_0449_drift-index-migrate-and-render-fix.md`** — prior handoff; design rationale for the `_fm` shim and the prior migration commits. Useful for the migration conventions still in force.

# Outstanding parked threads

- **`a4-hook-automation`** (this thread) — open. Next: dispatcher end-to-end exercise, or any of the follow-ups enumerated above. Every script migration target on this thread is now complete.
- **`uc-status-transition-system`** — formally concluded.
- **`idea.promoted` / `brainstorm.promoted` materialization** — still open, unrelated.
- **`a4-redesign`, `experiments-slot`, `idea-slot`, `decision-slot-unification`** — unaffected.
