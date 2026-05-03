# a4 — task artifacts convention

Cross-family reference for the **artifact directory** that may sit alongside a task at project-root `artifacts/<type>/<id>-<slug>/`. Per-family shape, the `artifacts:` artifact-only contract, the spike archive convention, and curation policy live here so all four issue families (`task` / `bug` / `spike` / `research`) cite a single source.

Per-family authoring files cite this document for shared rules and add only family-specific notes (e.g., the spike's "primary deliverable" status, the bug's "evidence-only" framing).

The four issue families are sibling top-level folders under `a4/`; the artifact directory mirrors this with sibling top-level folders under `artifacts/`.

## Directory layout

Each task may have a sibling artifact directory at project-root `artifacts/<type>/<id>-<slug>/`, parallel to (not inside) `a4/`:

```
<project-root>/
  a4/<type>/<id>-<slug>.md         # task markdown — type ∈ {task, bug, spike, research}
  artifacts/<type>/<id>-<slug>/    # artifact directory (opt-in)
    *.py *.json *.png *.csv ...
```

The `artifacts/` directory:

- Is part of the project repo, not a temporary scratch area.
- Is not validated by any a4 script — the markdown-only contract of `a4/` is preserved.
- Is opt-in — projects without artifact-bearing tasks have no `artifacts/` directory.

## Per-family expectations

| Family | Typical contents | Strength |
|---|---|---|
| `spike` | PoC code, benchmark raw, scratch scripts | Primary use — most active spikes have one |
| `research` | Comparison raw data, charts, evaluation scripts, downloaded sources | Recommended when the investigation produces ancillary artifacts |
| `task` | Test samples, execution outputs for behavior comparison, design mockups, migration dry-run results | Optional — only when artifacts have evidentiary or comparative value |
| `bug` | Reproduction repos, crash logs, screenshots, traces | Optional — only when reproduction or evidence is itself worth keeping |

## Frontmatter `artifacts:` is artifact-only

Frontmatter `artifacts:` lists artifact paths only — every path must point under `artifacts/<type>/<id>-<slug>/...`. Production source paths the task writes or modifies are not duplicated in frontmatter; git history is authoritative, and the optional body `## Change Plan` may name them as a forward-looking scope fence.

For `type: spike`, `artifacts:` may also point under `artifacts/spike/archive/<id>-<slug>/` once archived.

## Spike archive convention

When a spike completes (or fails), the user manually `git mv`s the directory to `artifacts/spike/archive/<id>-<slug>/` and updates the task's `artifacts:` paths to match.

- The archive convention applies to `spike` only — `task`, `bug`, and `research` artifact directories are **not** archived (closed task markdown moves to `a4/archive/` independently).
- The move is **never automated**; same-precedent reasoning as `idea/` promotion (deferred until manual cost surfaces as pain).

## Curation policy

The artifact directory is part of the project repo, not scratch. Commit intentionally — only what carries value beyond the current session.

- **Keep:** comparison results, reproducible data / scripts, evidence cited from the task body, decision-supporting raw output.
- **Drop:** regenerable build outputs, machine-specific caches, large binaries not referenced from the body, secrets / API keys.

Curation is user-driven. There is no automated cleanup. When a spike's exploration ends, manually `git mv` the directory to `artifacts/spike/archive/<id>-<slug>/`.
