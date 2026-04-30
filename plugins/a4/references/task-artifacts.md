# a4 — task artifacts convention

Cross-kind reference for the **artifact directory** that may sit alongside a task at project-root `artifacts/task/<kind>/<id>-<slug>/`. Per-kind shape, the `task.artifacts:` artifact-only contract, the spike archive convention, and curation policy live here so all four kinds (`feature` / `bug` / `spike` / `research`) cite a single source.

Per-kind authoring files (`task-{feature,bug,spike,research}-authoring.md`) cite this document for shared rules and add only kind-specific notes (e.g., the spike's "primary deliverable" status, the bug's "evidence-only" framing).

## Directory layout

Each task may have a sibling artifact directory at project-root `artifacts/task/<kind>/<id>-<slug>/`, parallel to (not inside) `a4/`:

```
<project-root>/
  a4/task/<kind>/<id>-<slug>.md         # task markdown
  artifacts/task/<kind>/<id>-<slug>/    # artifact directory (opt-in)
    *.py *.json *.png *.csv ...
```

The `artifacts/` directory:

- Is part of the project repo, not a temporary scratch area.
- Is not validated by any a4 script — the markdown-only contract of `a4/` is preserved.
- Is opt-in — projects without artifact-bearing tasks have no `artifacts/` directory.

## Per-kind expectations

| kind | Typical contents | Strength |
|---|---|---|
| `spike` | PoC code, benchmark raw, scratch scripts | Primary use — most active spikes have one |
| `research` | Comparison raw data, charts, evaluation scripts, downloaded sources | Recommended when the investigation produces ancillary artifacts |
| `feature` | Test samples, execution outputs for feature comparison, design mockups, migration dry-run results | Optional — only when artifacts have evidentiary or comparative value |
| `bug` | Reproduction repos, crash logs, screenshots, traces | Optional — only when reproduction or evidence is itself worth keeping |

## Frontmatter `task.artifacts:` is artifact-only

Frontmatter `task.artifacts:` lists artifact paths only — every path must point under `artifacts/task/<kind>/<id>-<slug>/...`. Production source paths the task writes or modifies belong in the body `## Files` section, not in frontmatter. (The field was named `files` before a4 v10.0.0; rename in any pre-v10 workspace.)

For `kind: spike`, `artifacts:` may also point under `artifacts/task/spike/archive/<id>-<slug>/` once the directory has been archived.

## Spike archive convention

When a spike completes (or fails), the user manually `git mv`s the directory to `artifacts/task/spike/archive/<id>-<slug>/` and updates the task's `artifacts:` paths to match.

- The archive convention applies to `spike` only — `feature`, `bug`, and `research` artifact directories are **not** archived (closed task markdown moves to `a4/archive/` independently).
- The move is **never automated**; same-precedent reasoning as `idea/` promotion (deferred until manual cost surfaces as pain).

## Curation policy

The artifact directory is part of the project repo, not scratch. Commit intentionally — only what carries value beyond the current session.

- **Keep:** comparison results, reproducible data / scripts, evidence cited from the task body, decision-supporting raw output.
- **Drop:** regenerable build outputs, machine-specific caches, large binaries not referenced from the body, secrets / API keys.

Curation is user-driven. There is no automated cleanup. When a spike's exploration ends, manually `git mv` the directory to `artifacts/task/spike/archive/<id>-<slug>/`.
