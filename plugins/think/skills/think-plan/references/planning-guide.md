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

## Launch & Verify Derivation

After codebase exploration, fill the **Launch & Verify** section. This information is used during Phase 2 for build verification and integration/smoke testing.

### Auto-detection procedure

1. **App type** — derive from arch's Technology Stack and codebase structure:

   | Detection Signal | App Type |
   |-----------------|----------|
   | `engines.vscode` in package.json | VS Code Extension |
   | `next`, `vite`, `react-scripts` in dependencies | Web app |
   | `electron` in dependencies | Electron app |
   | `express`, `fastify`, `koa`, `hono` in dependencies | API service |
   | `bin` field in package.json | CLI tool |
   | `flask`, `django`, `fastapi` in requirements | Python web app |
   | `main.go` with `http.ListenAndServe` | Go API service |

2. **Build command** — check `package.json` scripts (`build`, `compile`), `Makefile`, `pyproject.toml`, `Cargo.toml`, `build.gradle`.

3. **Launch command** — check `package.json` scripts (`dev`, `start`, `serve`), `.vscode/launch.json`, framework conventions:

   | App Type | Typical Launch |
   |----------|---------------|
   | VS Code Extension | `code --extensionDevelopmentPath=${workspaceFolder}` (from launch.json) |
   | Next.js / Vite | `npm run dev` |
   | Express / Fastify | `npm start` or `node dist/index.js` |
   | Electron | `npm start` or `electron .` |
   | CLI | `node dist/cli.js` or `./target/release/<name>` |
   | Django | `python manage.py runserver` |
   | FastAPI | `uvicorn main:app --reload` |

4. **Launch URL/view** — derive from app type (web → `http://localhost:<port>`, extension → panel/view name, CLI → N/A).

5. **Verify tool** — select based on app type:

   | App Type | Primary Tool | Fallback |
   |----------|-------------|----------|
   | Web app | Playwright CLI (`@playwright/cli`) | chrome MCP |
   | VS Code Extension | WebdriverIO + wdio-vscode-service | computer-use MCP |
   | Electron | Playwright `electron.launch()` | computer-use MCP |
   | API service | Playwright CLI or curl | direct HTTP requests |
   | CLI | Bash execution | — |
   | Native desktop | computer-use MCP | — |

6. **Smoke scenario** — identify the single most basic user interaction from the source UCs. This is the minimum bar for "the app works":
   - Chat app → "type a message and see a response"
   - CRUD app → "create an item and see it in the list"
   - API → "call the health endpoint and get 200"
   - CLI → "run `<tool> --help` and see usage info"

7. **Test isolation** — determine flags or configuration to run the app in a clean environment, free from interference by other installed plugins, extensions, or user state. Start from the defaults below, then **search the platform's official documentation** (e.g., VS Code CLI reference, Electron command-line switches) for the current project's exact flags:

   | App Type | Default Isolation | Docs to Search |
   |----------|------------------|----------------|
   | VS Code Extension | `--disable-extensions` (loads only the dev extension) | VS Code CLI reference |
   | Electron | `--user-data-dir=<tmpdir>` (clean profile, no leftover state) | Electron command-line switches |
   | Web app | Browser incognito / clean profile (no browser extensions) | Verify tool docs (Playwright, etc.) |
   | API service | Dedicated test port + `NODE_ENV=test` (or equivalent) | Framework docs |
   | CLI | Already isolated per invocation | — |

   The defaults above are starting points. Search the official docs to confirm the flags are current and to discover project-specific options (e.g., `--extensions-dir` for VS Code, `--no-sandbox` for Electron on CI). Record the final isolation value in the plan.

## Foundation Unit Validation

After defining the first unit(s) in Phase 1, verify they produce a **minimally interactive system**, not just project scaffolding.

**Check:** Can a user perform the most basic interaction after the foundation unit is complete?

| Application Type | Minimum Viable Interaction |
|-----------------|---------------------------|
| Chat / conversation app | User can type a message, send it, and see a response |
| CRUD application | User can create one entity and see it listed |
| Dashboard | User can see at least one real data point displayed |
| CLI tool | User can invoke the tool and see meaningful output |
| API service | A client can call one endpoint and get a valid response |

If the foundation unit only produces empty scaffolding (boilerplate files, placeholder HTML, wired-up message types with no UI, "Ready" status text with no input mechanism), it is **incomplete**. Expand it to include the minimal interaction loop, or create a dedicated IU for it.

A scaffold that cannot be used is not a testable increment — it is dead code until later units bring it to life. The foundation unit's acceptance criteria must include at least one end-to-end interaction scenario, not just "extension activates without error" or "project compiles."

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

When the file mapping shows 3+ IUs modifying the same file, that file is a **shared integration point**. Without explicit coordination, each IU's coder agent adds its piece in isolation — message handlers get registered but components never get mounted, routes get defined but never wired to the app.

After completing all unit file mappings, scan for shared integration points:

1. **Identify shared files** — any file appearing in 3+ IUs' file mapping tables.
2. **Define the integration pattern** — for each shared file, describe how the contributions from different IUs compose into a working whole.
3. **Add a Shared Integration Points table** to the plan (see output template).

Example:

| File | Integration Pattern | Contributing IUs |
|------|-------------------|-----------------|
| `src/webview/main.ts` | Message handler registration + DOM component mounting | IU-1: scaffold + ready handler, IU-2: ConversationView mount + render handlers, IU-7: Sidebar mount + spawn handlers |
| `src/webview/index.html` | Container divs for UI regions + script wiring | IU-1: app shell with `#app`, IU-2: `#conversation` container, IU-7: `#sidebar` container |
| `src/extension.ts` | Component registration + message handler dispatch | IU-1: activation + panel, IU-2: RenderingEngine, IU-6: PersonaStore |

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
