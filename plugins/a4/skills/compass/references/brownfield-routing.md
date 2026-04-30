# Brownfield Detection and Pipeline-Shape Routing

Applied at compass Step 2.0, before showing the Step 2.1 catalog. Detects whether the project already has implementation code and, if so, asks the user to choose one of three pipeline shapes.

## Detection

Run both signature checks at project root:

```bash
# Build/manifest signature at project root
ls "$ROOT"/{package.json,pyproject.toml,Cargo.toml,go.mod,pom.xml,build.gradle,build.gradle.kts} 2>/dev/null

# Tracked source files outside a4/, plugins/, .claude*/, research/
git -C "$ROOT" ls-files | grep -Ev '^(a4/|plugins/|\.claude|research/)' | grep -E '\.(ts|tsx|js|jsx|py|rs|go|java|kt|rb|php|cpp|c|swift|m|md)$' | head -1
```

If either signal fires **and** `a4/` is empty (or absent), the project is **brownfield** — existing code with no a4 workspace. The user must pick one of three pipeline shapes (full taxonomy: [`pipeline-shapes.md`](${CLAUDE_PLUGIN_ROOT}/dev/pipeline-shapes.md)).

When no implementation code is detected, skip this step and proceed straight to the Step 2.1 catalog.

## Three-way shape choice

Ask **one** question before showing the catalog:

> This project has existing code but no a4 workspace. What are you trying to do?
> - **(a) Reverse-engineer** (Reverse shape) — extract use cases and supporting wiki pages (`context.md`, `actors.md`, `domain.md`) from the existing code.
> - **(b) Single change** (Minimal shape) — make one small change without the full pipeline (`bootstrap.md` only, then `/a4:task` or `/a4:bug` → `/a4:run`).
> - **(c) New feature** (Full shape) — start the formal pipeline (`/a4:usecase` → `/a4:domain` → `/a4:arch` → `/a4:auto-bootstrap` → `/a4:roadmap` → `/a4:run`) for a new feature on top.

A user with no implementation goal yet (just recording a spec via `/a4:spec`, capturing research, or sketching ideas) is in a **No-shape** state — none of (a)/(b)/(c) applies. Compass does not prompt for that explicitly; the catalog's Ideation and Standalone sections cover those cases as fall-throughs.

## Routing per choice

### (a) Reverse-engineer

Invoke `/a4:auto-usecase` with the project root as the default argument (or a user-specified subdirectory if they name one). The skill autonomously runs code analysis (its Step 2b) and produces `context.md` / `actors.md` / `nfr.md` / per-UC files at `status: draft`; `domain.md` is **not** authored by `auto-usecase` (per [`wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/dev/wiki-authorship.md), `domain` owns it). Suggest `/a4:usecase iterate` to review the drafts and `/a4:domain` to extract concepts as the Reverse-then-forward continuation.

```
Skill({ skill: "a4:auto-usecase", args: "<project-root or subdirectory>" })
```

### (b) Single change

Invoke `/a4:auto-bootstrap` (which already supports incremental mode against an existing codebase per its Step 1 "Codebase Assessment"; in this entry path it runs in Minimal-shape scope, producing `bootstrap.md` without requiring `architecture.md`); follow with `/a4:task` (or `/a4:bug`) for the change itself.

### (c) New feature

Full pipeline: `/a4:usecase → /a4:domain → /a4:arch → /a4:auto-bootstrap → /a4:roadmap → /a4:run` (per [`pipeline-shapes.md`](${CLAUDE_PLUGIN_ROOT}/dev/pipeline-shapes.md) Shape 1 Full forward). Fall through to the Step 2.1 catalog; the user typically picks `/a4:usecase` first.
