# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-07-01

### Added

- **Data models + repositories**: `Document` model with parsed content, SHA-256 content-hash dedup, status lifecycle, and tags as a Postgres `text[]` column; async `DocumentRepository` behind a `Protocol` with SQLModel and in-memory implementations.
- **Ingestion pipeline**: two-phase (`prepare`/`finalize`) orchestrator wiring parser, chunker, and embedder adapters behind Protocols. Stack: `markitdown` (PDF/Office/plain text → Markdown), `semchunk` (token-budgeted semantic chunking), and an OpenRouter embedder (Qwen3-Embedding-8B, 1536 dims, asymmetric `input_type`). Qdrant collection auto-provisioned on startup with cosine distance and payload indexes on `document_id`/`tags`.
- **Document management REST API**: upload (triggers async ingestion, dedup via content hash), list, get-by-id, delete (cascades to Qdrant), tags endpoint.
- **MCP server**: five knowledge-base tools — `list_documents`, `list_tags`, `search`, `search_by_tag`, `search_by_document` — mounted at `/mcp` over Streamable HTTP with static Bearer token auth, query-time embeddings, and FastMCP dependency injection.
- **Document management UI**: minimal React SPA — upload with tagging, document list with status/size/chunk-count, delete, polling while processing.
- **Example data & scripts**: 7 example documents across 5 formats (md, pdf, html, docx, txt) plus `scripts/convert_data.sh` (regenerate PDF/DOCX from source markdown) and `scripts/ingest_data.sh` (load example data into a running stack).
- Docker Compose stack (frontend, backend, PostgreSQL 17, Qdrant), CI, linting, and end-to-end test coverage across REST API and MCP tools.

[Unreleased]: https://github.com/apiraccini/dis/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/apiraccini/dis/releases/tag/v0.1.0
