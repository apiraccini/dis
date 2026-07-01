# Testing

## Test Pyramid

The test suite is organised into two tiers:

- **unit/** — Pure unit tests. No external services, no real adapters. Fast (milliseconds). Test individual functions, model logic, and service orchestration with fake/mock dependencies.
- **integration/** — Tests that exercise real adapters (MarkItDown, semchunk, OpenRouter, Qdrant client) or the full HTTP/MCP stack with fake backends. May need configuration/env vars but no running Docker containers.

## Conventions

- **Shared fakes** live in `tests/_fakes.py` (module) or `tests/_fakes/` (package if they grow).
- **No `__init__.py` imports** — each test file imports exactly what it needs.
- **Pytest marks** — integration tests MUST be marked `@pytest.mark.integration`.
- **Coverage** — `make test` runs all unit and integration tests under coverage with a minimum threshold of 85%.
- **No real network in unit tests** — any test that calls an external API belongs in integration.

## Fixtures & Mocking

- **Prefer fixtures over setup/teardown** — Use `@pytest.fixture` for shared state. Scope `function` (default) for state isolation; `session` only for expensive immutable objects (e.g. a FastAPI app instance).
- **Parametrize, don't duplicate** — Use `@pytest.mark.parametrize` to test multiple inputs/outputs for pure functions. Avoid inline loops and duplicated test functions.
- **Mock at system boundaries** — Use `unittest.mock` for external boundaries (e.g. real HTTP, real DB connections). Our Protocol-based dependency injection already handles internal fakes — don't add mocking there.
- **Test behaviour, not implementation** — Assert on return values and observable state (document status, error messages, search results). Only inspect internal call counts or argument lists when the spec requires proving something DID or DID NOT happen (e.g. dedup hit must not run expensive work).

## Example Data

- **Requirement: Directory layout** — `data/` SHALL have two subdirectories: `data/raw/` (source markdown files, one per topic) and `data/final/` (ready-to-ingest documents in their target formats).
- **Requirement: Example data directory** — `data/final/` SHALL contain 5–10 example documents in mixed formats (markdown, PDF, HTML, DOCX, plain text) covering varied tags, suitable for ingestion into a running DIS stack.
- **Requirement: Format coverage** — The example set SHALL include at least one document in each format that the parser (MarkItDown) supports: markdown, PDF, HTML, DOCX, and plain text.
- **Requirement: Tag mapping** — `data/mapping.yaml` SHALL map each example filename (relative to `data/final/`) to a list of tags. At least some tags SHALL be shared across two or more documents to enable meaningful cross-document search.
- **Requirement: Ingestion script** — `scripts/ingest_data.sh` SHALL read `data/mapping.yaml`, iterate entries, and POST each file to `POST /api/documents/upload` on `http://localhost:8000`, with tags as form data. It SHALL exit with a non-zero code if any upload fails.
- **Requirement: Conversion script** — `scripts/convert_data.sh` SHALL use pandoc to generate PDF and DOCX variants from source markdown files in `data/raw/`, writing the output to `data/final/`. It SHALL be idempotent (overwrites existing outputs).
