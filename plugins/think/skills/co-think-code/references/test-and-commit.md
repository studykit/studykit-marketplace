# Test and Commit

Procedure for test execution and committing. This reference is read by the `code-executor` agent.

## 1. Test Framework Context

Use the test framework, runner command, and report format provided by the orchestrator (identified during Step 0: Codebase Exploration). Common setups:

| Project Type | Runner Command | Path Filter Example |
|-------------|---------------|-------------------|
| Node (Jest) | `npm test` | `npm test -- --testPathPattern=auth` |
| Node (Vitest) | `npx vitest run` | `npx vitest run tests/auth` |
| Python (pytest) | `pytest` | `pytest tests/test_auth.py` |
| Python (unittest) | `python -m pytest` | `python -m pytest tests/test_auth.py` |
| Java (Gradle) | `./gradlew test` | `./gradlew test --tests "*.AuthServiceTest"` |
| Java (Maven) | `mvn test` | `mvn test -Dtest=AuthServiceTest` |
| Go | `go test` | `go test ./services/auth/...` |

If the orchestrator didn't specify a runner command, discover it from the project:
1. Check `package.json` scripts for `test`
2. Check for `Makefile` with a `test` target
3. Check for `pyproject.toml` or `setup.cfg` with test configuration
4. Check for `build.gradle` or `pom.xml`

## 2. IU-Level Test Requirement

Every IU must produce its own unit tests. Writing tests is part of implementation, not a separate step.

- Follow the IU's **test strategy** for type, scenarios, and isolation
- Place test files at the paths specified in the IU's test strategy
- If no test file path is specified, follow the project's test file conventions (e.g., `__tests__/`, `tests/`, co-located `.test.ts` files)

## 3. Test Execution

Run the IU's specific tests using the project's test runner with a path filter. Do not run the full test suite — focus on the IU's tests only.

```bash
# Examples — use the actual runner from the project
npm test -- --testPathPattern=auth.service
pytest tests/services/test_auth.py
./gradlew test --tests "*.AuthServiceTest"
```

Run the **full suite** only in these cases:
- After parallel unit merges (orchestrator's responsibility, not yours)
- When the IU's test strategy explicitly requires it (e.g., E2E tests)

## 4. Build and Test Pass — Your Baseline

Build pass and test pass are your responsibility. You wrote both the code and the tests — you control both sides.

- If the build fails, fix it. This is not a reportable failure.
- If tests fail, fix them. This is not a reportable failure.
- The only reason to stop is a **major deviation** — the plan assumes something that doesn't hold in the actual codebase. See `execution-procedure.md` for the distinction between minor and major deviations.

## 5. Commit Convention

After tests pass, commit with an IU-tagged message:

```
feat(IU-N): <short description>

Implements IU-N from <plan-file-name>
```

**Prefix selection:**
- `feat` — new functionality (most common for IU implementation)
- `fix` — correcting existing behavior
- `refactor` — restructuring without behavior change

**Rules:**
- One commit per IU — atomic and revertable
- Include both implementation code and test code in the same commit
- Do not commit changes to the plan file — that's the orchestrator's responsibility

> **Note:** Plan file status and completion note updates are the orchestrator's sole responsibility. This reference covers only the agent's test and commit behavior.
