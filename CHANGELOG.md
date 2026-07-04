# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **`get_document` MCP tool**: read a document by ID — full parsed text or specific chunk indices (fetched from Qdrant by deterministic point ID, matching `search` hits exactly). Full reads are refused above a configured token limit (`MAX_DOCUMENT_READ_TOKENS`, default 20000) with a hint to use `chunks` or `search`.
- **Per-document token count**: computed at ingestion with the chunker's tokenizer, persisted, and exposed in REST responses, `list_documents` MCP output, and the frontend table — lets agents judge full-read cost up front.

## [0.1.1] - 2026-07-04

### Added

- **Hybrid search**: dense (Qwen3) + sparse (FastEmbed BM25, local) named vectors in Qdrant, fused server-side via Reciprocal Rank Fusion — exact keyword/domain-term matches now complement semantic similarity.
- **VLM-assisted parsing**: optional `markitdown-ocr` plugin with a vision LLM via OpenRouter (`USE_VLM`, default off) so scanned/image-only PDFs extract text; added a scanned example document.

### Changed

- **MCP tools consolidated from five to three**: `search_by_tag` / `search_by_document` folded into `search`'s `tags` / `document_ids` filters to avoid tool-choice ambiguity; richer tool descriptions, LLM-readable plain-text output, and Pydantic-validated parameter bounds (`ge`/`le` caps on `top_k`, `limit`, `offset`; non-empty `query`).
- Duplicate uploads now return a structured error (409) instead of the existing document.

### Fixed

- Deterministic document list ordering (`created_at` desc, `id` tie-break) for stable pagination; Qdrant image pinned.
- Document delete removes vectors before the SQL row so a partial failure stays retryable; backend/frontend healthchecks hardened.
- Background ingestion (`finalize`) now opens its own DB session instead of reusing the request-scoped one that FastAPI tears down before background tasks run.

## [0.1.0] - 2026-07-01

### Added

- **Data models + repositories**: `Document` model with parsed content, SHA-256 content-hash dedup, status lifecycle, and tags as a Postgres `text[]` column; async `DocumentRepository` behind a `Protocol` with SQLModel and in-memory implementations.
- **Ingestion pipeline**: two-phase (`prepare`/`finalize`) orchestrator wiring parser, chunker, and embedder adapters behind Protocols. Stack: `markitdown` (PDF/Office/plain text → Markdown), `semchunk` (token-budgeted semantic chunking), and an OpenRouter embedder (Qwen3-Embedding-8B, 1536 dims, asymmetric `input_type`). Qdrant collection auto-provisioned on startup with cosine distance and payload indexes on `document_id`/`tags`.
- **Document management REST API**: upload (triggers async ingestion, dedup via content hash), list, get-by-id, delete (cascades to Qdrant), tags endpoint.
- **MCP server**: five knowledge-base tools — `list_documents`, `list_tags`, `search`, `search_by_tag`, `search_by_document` — mounted at `/mcp` over Streamable HTTP with static Bearer token auth, query-time embeddings, and FastMCP dependency injection.
- **Document management UI**: minimal React SPA — upload with tagging, document list with status/size/chunk-count, delete, polling while processing.
- **Example data & scripts**: 7 example documents across 5 formats (md, pdf, html, docx, txt) plus `scripts/convert_data.sh` (regenerate PDF/DOCX from source markdown) and `scripts/ingest_data.sh` (load example data into a running stack).
- Docker Compose stack (frontend, backend, PostgreSQL 17, Qdrant), CI, linting, and end-to-end test coverage across REST API and MCP tools.

[Unreleased]: https://github.com/apiraccini/dis/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/apiraccini/dis/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/apiraccini/dis/releases/tag/v0.1.0
