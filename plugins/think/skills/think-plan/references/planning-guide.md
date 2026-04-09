# Planning Guide

Detailed procedures for deriving implementation units from a specification.

## Unit Derivation Strategy

There are three common approaches. Choose based on the spec's characteristics:

### 1. Component-First (Bottom-Up)

Best when the spec has a clear Architecture section with well-defined components and DB schemas.

1. Start with components that have no dependencies on other components (leaf nodes).
2. Build up layer by layer — data models first, then services, then API/UI layers.
3. Each component becomes one or more units depending on complexity.

**When to use:** Data-heavy applications, backend services, systems with clear layered architecture.

### 2. Feature-First (Vertical Slices)

Best when FRs represent independent user-facing features that cut across multiple components.

1. Group FRs into coherent features (e.g., "user authentication", "project management").
2. Each feature becomes a unit that implements all layers for that feature.
3. Order by dependency: features that other features depend on come first.

**When to use:** Full-stack applications, feature-driven development, when users want incremental demos.

### 3. Hybrid

Mix both approaches: foundation units (schemas, shared services) first, then vertical feature slices.

**When to use:** Most real-world projects. Start with shared infrastructure, then slice by feature.

## Unit Sizing Guidelines

A well-sized unit should:
- Cover 1-5 related FRs
- Touch 1-3 components
- Be independently testable
- Result in a meaningful, working increment
- Require roughly under ~500 lines of new or changed code

### Splitting Large Units

Split when a unit:
- Covers more than 5 FRs across unrelated areas
- Touches more than 3 components with no clear theme
- Mixes schema creation with complex business logic
- Would require both backend and frontend work that can be separated

### Merging Small Units

Merge when a unit:
- Contains only a single config file change
- Is a trivial setup step always done alongside another unit
- Has no independent test value

## Dependency Analysis

### Finding Dependencies

For each unit, check:
1. **Schema dependencies** — does this unit use tables/entities created in another unit?
2. **Service dependencies** — does this unit call functions/APIs implemented in another unit?
3. **Interface dependencies** — does this unit implement one side of an interface contract defined in another unit?
4. **Data dependencies** — does this unit need seed data or migration from another unit?

### Ordering Rules

1. **No forward references** — a unit must not depend on anything built in a later unit.
2. **Minimize depth** — prefer wider, flatter dependency trees over deep chains.
3. **Identify parallel opportunities** — units with no mutual dependencies can be implemented simultaneously.
4. **Foundation first** — shared schemas, utility functions, and configuration always come first.

## Test Strategy Selection

| Unit Type | Recommended Test Approach |
|-----------|--------------------------|
| Data model / schema | Integration tests against real DB (or in-memory DB) |
| Service / business logic | Unit tests with mocked dependencies |
| API endpoint | Integration tests with test client |
| UI component | Component tests (e.g., React Testing Library) |
| Cross-cutting flow | E2E tests |
| External service integration | Unit tests with mocked/stubbed external calls |

### Test Scenario Derivation

For each FR assigned to a unit:
1. **Happy path** — derive from FR's "System behavior" steps
2. **Error cases** — derive from FR's "Error handling" section
3. **Boundary cases** — derive from FR's "Validation" section
4. **State transitions** — derive from Domain Model's state diagrams (if the FR involves stateful entities)

## File Mapping

### Deriving File Paths

Use the spec's Technology Stack and codebase conventions to determine paths:

1. **Explore the existing codebase** — check directory structure, naming conventions, existing patterns.
2. **Follow framework conventions** — e.g., Next.js uses `app/` for routes, Django uses `<app>/models.py`.
3. **Be explicit** — `src/services/auth.service.ts` not "a service file."

### Change Scope for Existing Files

When modifying existing files, specify:
- **What is added** — new fields, methods, routes, imports
- **What is modified** — changed function signatures, updated schemas
- **What is removed** — deprecated code, replaced implementations
