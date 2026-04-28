# Phase 2: External Dependencies

Populate `<external-dependencies>` in `architecture.md` when the system uses external services.

## Procedure

1. **Scan UCs for external interactions.** Any UC whose Flow or Outcome references third-party authentication, notifications, file storage, external data sources, etc.

2. **Present the list** with `Used By` (UC markdown links), `Purpose`, and ask the user for confirmation.

3. **For each confirmed dependency, clarify:**
   - What the system sends/receives (Access Pattern)
   - Constraints (rate limits, pricing tiers, specific provider)
   - Fallback behavior when unavailable

4. **Record in `architecture.md`'s `<external-dependencies>` section.** Append `<change-logs>` bullets keyed by the causing UCs.

## When to skip

Skip Phase 2 entirely when no UC references external interactions. The `<external-dependencies>` section is optional; do not write an empty stub.
