# Testing

## Test Pyramid

The test suite is organised into three tiers:

- **unit/** — Pure unit tests. No external services, no real adapters. Fast (milliseconds). Test individual functions, model logic, and service orchestration with fake/mock dependencies.
- **integration/** — Tests that exercise real adapters (MarkItDown, semchunk, OpenRouter, Qdrant client) or the full HTTP/MCP stack with fake backends. May need configuration/env vars but no running Docker containers.
- **e2e/** — Full end-to-end tests that require a running compose stack (real Postgres + Qdrant). Not run in CI by default.

## Conventions

- **Shared fakes** live in `tests/_fakes.py` (module) or `tests/_fakes/` (package if they grow).
- **No `__init__.py` imports** — each test file imports exactly what it needs.
- **Pytest marks** — integration tests MUST be marked `@pytest.mark.integration`. e2e tests MUST be marked `@pytest.mark.e2e`.
- **Coverage** — `make test` runs all unit and integration tests under coverage with a minimum threshold of 85%.
- **No real network in unit tests** — any test that calls an external API belongs in integration or e2e.

## Fixtures & Mocking

- **Prefer fixtures over setup/teardown** — Use `@pytest.fixture` for shared state. Scope `function` (default) for state isolation; `session` only for expensive immutable objects (e.g. a FastAPI app instance).
- **Parametrize, don't duplicate** — Use `@pytest.mark.parametrize` to test multiple inputs/outputs for pure functions. Avoid inline loops and duplicated test functions.
- **Mock at system boundaries** — Use `unittest.mock` for external boundaries (e.g. real HTTP, real DB connections). Our Protocol-based dependency injection already handles internal fakes — don't add mocking there.
- **Test behaviour, not implementation** — Assert on return values and observable state (document status, error messages, search results). Only inspect internal call counts or argument lists when the spec requires proving something DID or DID NOT happen (e.g. dedup hit must not run expensive work).
