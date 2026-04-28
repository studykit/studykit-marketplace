# Phase 2: Relationship Mapping

Populate `<relationships>` in `a4/domain.md` once two or more concepts interact in non-trivial ways.

## Procedure

1. **Identify pairs** of concepts that interact across UCs — ownership, references, composition, association.

2. **Confirm cardinality** with the user (1, 0..1, 1..*, 0..*).

3. **Confirm direction** of dependency where it matters (which side cannot exist without the other).

4. **Write the PlantUML class diagram** to `a4/domain.md` showing only concept names and key attributes — no methods, no implementation types.

5. **Add text explanation** of each relationship under the diagram. Diagrams alone are not self-documenting.

## Missing-concept loopback

If a relationship surfaces a **missing concept** that wasn't caught in Phase 1, return to Phase 1 (mark its task `in_progress` again) before continuing.
