# Project-State Assessment

Single axis — project state. Run the right scaffold mode based on what is already present.

- **No existing code (fresh)** — run all subsequent scaffold steps from scratch.
- **Existing code (incremental)** — identify what is already present (project structure, dependencies, build config). Only set up what is missing. Do not overwrite working configuration without cause.

When `architecture.md` exists, treat its Technology Stack / Component structure / External Dependencies as the canonical input. When absent, derive the minimum from the observed repo state plus the user's running prompt.
