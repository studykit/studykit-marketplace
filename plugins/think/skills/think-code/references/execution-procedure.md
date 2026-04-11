# Execution Procedure

Step-by-step procedure for implementing a single implementation unit (IU). This reference is read by the `coder` agent at the start of each IU.

## 1. Read the IU

Parse the IU section from the plan:

- **Description** — what to implement and why. This is the primary guide for business logic.
- **File mappings** — the table of files to create or modify:
  - `Create` — write a new file at the specified path
  - `Modify` — change an existing file as described in the Change column
- **Test strategy** — what kind of tests, which scenarios, isolation approach, test file paths
- **Acceptance criteria** — the checkboxes that define "done." Each criterion is a concrete, measurable outcome.

Read all of these before writing any code.

## 2. Align with the Codebase

Before creating or modifying files, check the surrounding codebase:

- **Directory structure** — does the target path exist? What's the naming pattern in that directory?
- **Import conventions** — how do existing files import modules? Absolute or relative paths? Index files?
- **Code style** — tabs or spaces? Semicolons? Naming conventions (camelCase, snake_case)?
- **Existing patterns** — if you're creating a service, how are other services structured? If you're adding a route, how are other routes registered?
- **External library APIs** — when using a third-party library, read its actual type definitions or API docs (e.g., `.d.ts` files in `node_modules/`, docstrings, official documentation) before writing code. Never guess an API shape from memory. Mocks and stubs must also match the real API — a mock that diverges from the actual types creates a false-green test suite.

Follow the project's conventions even if the plan suggests something slightly different. Record any deviation in the completion note.

## 3. Implement

Work through the file mapping table in order:

1. For **Create** actions:
   - Check the directory exists (create it if not)
   - Write the file following project conventions
   - Implement the business logic from the IU description

2. For **Modify** actions:
   - Read the existing file first
   - Understand the current structure before making changes
   - Apply the change described in the Change column
   - Preserve existing style, formatting, and patterns

Use the acceptance criteria as implementation checkpoints. After writing code for each criterion, mentally verify: "does my code satisfy this?"

### UI Render Reachability Check

For IUs that create or modify UI components (webview components, React components, HTML views, page templates, etc.), verify after implementation:

1. **Mount point exists** — is there a container element in the entry HTML/view where this component renders? If the IU creates a `ConversationView` class, there must be a `<div id="conversation">` (or equivalent) in the HTML where it mounts.
2. **Component is instantiated** — is the component actually created and mounted in the application's runtime code, not just exported as a module? A module that exists but is never imported and called is dead code.
3. **Entry point references it** — does the application's main entry file (`main.ts`, `App.tsx`, `index.html`, etc.) import and use this component?

If any check fails, fix it before proceeding. A UI component that passes unit tests but is never rendered is not a working increment.

When the IU's file mapping says "Modify main.ts — Wire up X," this means **both** message/event handler registration **AND** DOM rendering/mounting. If a Shared Integration Points table was provided in the prompt, follow its integration pattern for each shared file.

## 4. Handle Plan Deviations

During implementation, you may discover things the plan didn't anticipate.

### Minor Deviations — Proceed

These are normal and expected. Proceed with implementation and record in the completion note:

- Import path is different from what the plan assumed
- API shape is slightly different (extra parameter, different return type)
- A utility function the plan expected doesn't exist — write it or use an alternative
- Naming differs from plan but matches project conventions

### Major Deviations — Stop

These indicate the plan's assumptions don't hold. Stop immediately and return a deviation report:

- A dependency the plan relies on doesn't exist or behaves fundamentally differently
- The existing architecture conflicts with what the plan prescribes (e.g., plan says REST but project uses GraphQL)
- Requirements contradict each other or contradict existing behavior
- A required external service or API is unavailable or has a different interface

The distinction: a minor deviation is something you can work around without changing the plan's intent. A major deviation means the plan needs revision before the IU can be implemented.

## 5. Write the Completion Note

After successful implementation, prepare a completion note for the orchestrator. Include:

- **Deviations from the plan and why** — "used `argon2` instead of `bcrypt` because the project already depends on it"
- **Additional dependencies installed** — "added `jsonwebtoken@9.0.0` to package.json"
- **Edge cases discovered and handled** — "added null check for optional `middleName` field"
- **Decisions made that weren't specified** — "chose to use a factory pattern for token generation to match existing auth code"

Be concise but specific. The completion note serves two audiences:
1. The orchestrator, which writes it to the plan file
2. Future agents, which read it for context on prior decisions
