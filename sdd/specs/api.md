# REST API

## Endpoints

### POST /api/documents/upload

Upload a file for ingestion. Accepts multipart form data (file + optional tags).

- **Requirement: Upload accepts file + tags** — `POST /api/documents/upload` SHALL accept a multipart form with a `file` field (required) and an optional `tags` field (comma-separated string)
  - Scenario: upload with tags — GIVEN a multipart request with file `report.pdf` and `tags=compliance,audit`, WHEN uploaded, THEN the document is created with tags `["compliance", "audit"]`
  - Scenario: dedup hit returns 409 — GIVEN a file whose content matches an existing document, WHEN uploaded, THEN the endpoint returns 409 with an error detail and no background task is scheduled
- **Requirement: Upload returns 202 with document** — When `prepare` creates a new `processing` document, the endpoint SHALL return 202 with the full document body (including its id) and SHALL schedule `finalize` as a background task
- **Requirement: Upload validates file type** — The endpoint SHALL reject files with unsupported extensions (not in a configured allowlist) with a 422 response before any parsing occurs

### GET /api/documents

List documents, paginated.

- **Requirement: List returns paginated documents** — `GET /api/documents` SHALL accept `offset` (int, default 0) and `limit` (int, default 100, max 500) query parameters and return `{items: [...], total: int}`
- **Requirement: List omits parsed_text** — List responses SHALL exclude `parsed_text` to reduce payload size; if the full document is needed the client fetches by id
- **Requirement: List filters by tag** — `GET /api/documents?tag=compliance` SHALL return only documents whose tag list contains `compliance` (case-insensitive, exact match after normalization)
  - Scenario: tag filter intersection — GIVEN three documents tagged `["compliance"]`, `["audit"]`, and `["compliance", "audit"]`, WHEN `?tag=compliance`, THEN two documents are returned

### GET /api/documents/{id}

Get a single document by id.

- **Requirement: Get by id returns full document** — `GET /api/documents/{id}` SHALL return the full document including `parsed_text`
  - Scenario: not found — GIVEN a non-existent id, WHEN fetched, THEN the endpoint returns 404
- **Requirement: Get by id is used for polling** — The upload endpoint schedules `finalize` as a background task; the client polls `GET /api/documents/{id}` until `status` is `ready` or `failed`

### DELETE /api/documents/{id}

Delete a document and its vectors.

- **Requirement: Delete cascades to vector store** — `DELETE /api/documents/{id}` SHALL remove the document from Postgres and all its associated vectors from Qdrant
  - Scenario: not found — GIVEN a non-existent id, WHEN deleted, THEN the endpoint returns 404

### GET /api/tags

List all unique tags.

- **Requirement: List tags returns distinct sorted tags** — `GET /api/tags` SHALL return `{tags: ["audit", "compliance", ...]}` (sorted alphabetically, no duplicates)
  - Scenario: no documents — GIVEN an empty database, WHEN listing tags, THEN the endpoint returns `{tags: []}`
