# Planning Guide

Detailed procedures for deriving implementation units from an architecture document.

## Unit Derivation Strategy

There are three common approaches. Choose based on the architecture's characteristics:

### 1. Component-First (Bottom-Up)

Best when the architecture has well-defined components and DB schemas.

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
- Cover 1-5 related UCs (or UC subsets — e.g., validation + error handling from a single UC)
- Touch 1-3 components
- Be independently testable
- Result in a meaningful, working increment
- Require roughly under ~500 lines of new or changed code

### Splitting Large Units

Split when a unit:
- Covers more than 5 UCs across unrelated areas
- Touches more than 3 components with no clear theme
- Mixes schema creation with complex business logic
- Would require both backend and frontend work that can be separated

### Merging Small Units

Merge when a unit:
- Contains only a single config file change
- Is a trivial setup step always done alongside another unit
- Has no independent test value

## Launch & Verify

`bootstrap.md` is the single source of truth for Launch & Verify (build / launch / test commands, smoke scenario, test isolation flags). Per [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md), `roadmap.md` does not author L&V content — it links to bootstrap with a one-line pointer. Roadmap planning therefore does **not** auto-detect app type, build commands, smoke scenarios, or test isolation; that work happened in `/a4:auto-bootstrap` and was already verified there.

If `bootstrap.md` is absent or out of date, stop and re-run `/a4:auto-bootstrap` rather than authoring or auto-detecting commands here. The drift detector and `roadmap-reviewer` flag authored L&V content on `roadmap.md` as a `CONFLICT` against the workspace authorship policy.

## Foundation Unit Validation

auto-bootstrap has already set up the project structure, dependencies, build configuration, and test infrastructure. The foundation unit builds on that base to produce the **first minimally interactive system**.

**Check:** Can a user perform the most basic interaction after the foundation unit is complete?

| Application Type | Minimum Viable Interaction |
|-----------------|---------------------------|
| Chat / conversation app | User can type a message, send it, and see a response |
| CRUD application | User can create one entity and see it listed |
| Dashboard | User can see at least one real data point displayed |
| CLI tool | User can invoke the tool and see meaningful output |
| API service | A client can call one endpoint and get a valid response |

If the foundation unit only produces boilerplate on top of the existing base (placeholder HTML, wired-up message types with no UI, "Ready" status text with no input mechanism), it is **incomplete**. Expand it to include the minimal interaction loop, or create a dedicated task for it.

A foundation unit that cannot be used is not a testable increment — it is dead code until later units bring it to life. The acceptance criteria must include at least one end-to-end interaction scenario, not just "extension activates without error" or "project compiles."

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

For each UC assigned to a unit:
1. **Happy path** — derive from UC's Flow steps and Expected Outcome
2. **Error cases** — derive from UC's Error handling field
3. **Boundary cases** — derive from UC's Validation field
4. **State transitions** — derive from Domain Model's state diagrams (if the UC involves stateful entities)

## Shared File Integration

When the file mapping shows 3+ tasks modifying the same file, that file is a **shared integration point**. Without explicit coordination, each task's coder agent adds its piece in isolation — message handlers get registered but components never get mounted, routes get defined but never wired to the app.

After completing all unit file mappings, scan for shared integration points:

1. **Identify shared files** — any file appearing in 3+ tasks' file mapping tables.
2. **Define the integration pattern** — for each shared file, describe how the contributions from different tasks compose into a working whole.
3. **Add a Shared Integration Points table** to the plan (see output template).

Example:

| File | Integration Pattern | Contributing tasks |
|------|-------------------|--------------------|
| `src/webview/main.ts` | Message handler registration + DOM component mounting | task 1: initial setup + ready handler, task 2: ConversationView mount + render handlers, task 7: Sidebar mount + spawn handlers |
| `src/webview/index.html` | Container divs for UI regions + script wiring | task 1: app shell with `#app`, task 2: `#conversation` container, task 7: `#sidebar` container |
| `src/extension.ts` | Component registration + message handler dispatch | task 1: activation + panel, task 2: RenderingEngine, task 6: PersonaStore |

This table is included in the prompt for every coder agent that touches the file, so each agent knows both its contribution AND the overall integration pattern.

## File Mapping

### Deriving File Paths

Use the arch's Technology Stack and codebase conventions to determine paths:

1. **Explore the existing codebase** — check directory structure, naming conventions, existing patterns.
2. **Follow framework conventions** — e.g., Next.js uses `app/` for routes, Django uses `<app>/models.py`.
3. **Be explicit** — `src/services/auth.service.ts` not "a service file."

### Change Scope for Existing Files

When modifying existing files, specify:
- **What is added** — new fields, methods, routes, imports
- **What is modified** — changed function signatures, updated schemas
- **What is removed** — deprecated code, replaced implementations
