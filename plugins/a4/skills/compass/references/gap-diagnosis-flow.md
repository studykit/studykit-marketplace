# Step 3: Gap Diagnosis Flow

The workspace has existing wiki pages or issues. Detect drift, locate the gap, and identify the next phase of work.

## 3.1 Detect drift

Before reading state, surface accumulated wiki↔issue drift since the last session:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/drift_detector.py" "$ROOT/a4"
```

The detector writes one review item per new finding into `a4/review/`, deduplicated against existing open / in-progress / discarded `source: drift-detector` items. Any new items are surfaced in 3.3 alongside pre-existing open drift.

## 3.2 Read workspace state

`scripts/workspace_state.py` renders workspace state as markdown to stdout, with an optional section filter. Compass requests only the sections its layered diagnosis (3.3) and presentation (3.4) need — `recent-activity`, `open-ideas`, `open-sparks` are snapshot-only and skipped:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/workspace_state.py" "$ROOT/a4" \
    wiki-pages issue-counts usecases-by-source \
    drift-alerts open-reviews active-tasks blocked-items milestones
```

Section identifiers and the full schema live in `${CLAUDE_PLUGIN_ROOT}/scripts/workspace_state.py`'s module docstring (run `--list-sections` to enumerate).

### Section → layer mapping for 3.3

- shape detection: `wiki-pages` + `usecases-by-source`
- Layer 0 / 1: `wiki-pages` + usecase counts in `issue-counts`
- Layer 2: `drift-alerts`
- Layer 3: `open-reviews`
- Layer 4: `active-tasks`
- Layer 5: `blocked-items`
- 3.4 presentation table: `wiki-pages` + `issue-counts` + `drift-alerts` + `milestones`

If Step 1.1 resolved a **specific target**, additionally read that file's full body and frontmatter — it drives the 3.3 diagnosis more than aggregate state does.

## 3.3 Diagnose the gap layer

Apply the layered trace defined in `../../skills/compass/references/gap-diagnosis.md`: detect the workspace shape (3.3.0), then walk Layer 0 → 6 against the state collected in 3.2 and stop at the first layer with actionable work. For a targeted Step 1.1 argument, focus the trace on layers upstream of the target (e.g., a blocked task points back to its `depends_on` predecessor). Carry the detected shape into 3.4 so the user sees the assumption.

## 3.4 Present diagnosis

Report in this format:

```
## Workspace Status

Shape: <Full | Reverse-then-forward | Reverse-only | Minimal | No shape>

| Layer | State |
|-------|-------|
| Wiki pages | <N of 7 present, list missing> |
| Open issues | <usecase: N draft / M implementing / …; task: …; review: …> |
| Drift alerts | <N open (H high, M medium, L low)> |
| Milestones | <milestone-name: X/Y complete> (only for active milestones) |

## Diagnosis

<1-3 sentences on where the gap is and why>

## Next phase

→ **<phase identifier>** [target=<target ref>] [mode=iterate|fresh]: <what to do and why>
```

The `<phase identifier>` names the kind of work needed — e.g., `architecture`, `domain`, `usecase`, `roadmap`, `task`, `run`, `bootstrap`. `<target ref>` is the specific issue or wiki page the work should open (e.g., `review/6-missing-validation`, `usecase/3-search-history`, `architecture`). For generic resumes, omit `target=` and use `mode=iterate` alone.

If the user disagrees with the diagnosis, discuss alternatives and let them choose.

## 3.5 Archive suggestion (targeted items only)

If Step 1.1 resolved a specific target **and** that item's `status` is a terminal state (`done` / `complete` / `resolved` / `final`), after presenting the diagnosis offer to archive it:

> "Item `<folder>/<id>-<slug>` is closed. Move to `a4/archive/`?"

Do **not** move automatically. On user confirmation:

```bash
git mv a4/<folder>/<id>-<slug>.md a4/archive/
git commit -m "docs(a4): archive <folder>/<id>-<slug>"
```

Workspace-wide completion is rare and user-driven — compass does not auto-suggest batch archive. Folder location is the archived flag; no frontmatter change is needed.
