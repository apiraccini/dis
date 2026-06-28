# Backend

FastAPI app serving the REST API, ingestion pipeline, and MCP server (the core of the project).

## Stack
- FastAPI (async), SQLModel, pydantic-settings, asyncpg, PostgreSQL 17
- Qdrant (qdrant-client) for vectors + payload filtering
- FastMCP (`fastmcp`) for the MCP server, mounted at `/mcp`
- markitdown (parser), semchunk (chunker), OpenRouter via `openai` SDK (Qwen3-embedding-8b embedder), Qdrant (vector store)
- uv, ruff, ty, pytest

## Tree
```
src/
├── main.py              FastAPI app: CORS, /health, mounts /mcp, combines lifespans
├── mcp_server.py        FastMCP instance + http_app() (path=/, stateless, json) + ping tool
├── db.py                async engine + session factory + init_db (create_all)
├── core/
│   ├── config.py        Settings (env vars, dev defaults)
│   ├── dependencies.py  get_db session dependency
│   └── security.py      build_mcp_auth() → StaticTokenVerifier
├── models/              SQLModel tables (Document w/ parsed content + content hash, Tag, DocumentTag link — backlog; no Chunk table)
├── schemas/             Pydantic request/response schemas (backlog)
├── endpoints/           FastAPI routers (backlog)
├── services/            Business logic + ingestion orchestrator + adapters
│   ├── protocols.py     Parser / Chunker / Embedder Protocols
│   ├── ingestion.py     IngestionService (two-phase prepare/finalize, dedup, lifecycle)
│   ├── factory.py       build_adapters() + build_ingestion_service() (wiring)
│   └── adapters/        Concrete impls behind the Protocols
│       ├── markitdown_parser.py   MarkItDown → Markdown (asyncio.to_thread)
│       ├── semchunk_chunker.py    token-budgeted semantic chunking (tiktoken)
│       ├── openrouter_embedder.py Qwen3-embedding-8b, batched, asymmetric input_type
│       └── qdrant_vector_store.py Qdrant (cosine, payload indexes, filter pushdown)
└── repositories/        Data access (Protocol + SQLModel + in-memory impls)
    ├── protocols.py     DocumentRepository + VectorStore Protocols, ChunkRecord, SearchHit
    ├── document_repo.py async SQLModel DocumentRepository
    └── in_memory.py     dict-backed DocumentRepository + VectorStore (test doubles)
tests/
├── test_health.py / test_document_model.py / test_errors.py
├── test_in_memory_document_repo.py / test_in_memory_vector_store.py
├── test_ingestion_service.py            (orchestration, behind fakes)
├── test_markitdown_parser.py / test_semchunk_chunker.py
├── test_openrouter_embedder.py / test_qdrant_vector_store.py
└── smoke_qdrant_live.py / smoke_ingestion_e2e.py  (run against compose; not in the unit suite)
```

## Development
```bash
uv sync --dev
uv run uvicorn src.main:app --reload
```

## Backlog
- [x] Data models + repositories
  - `models/document.py` (Document: parsed full text + content hash for dedup, status lifecycle, **tags as a Postgres `text[]` column** instead of a Tag/DocumentTag link — see `sdd/specs/documents.md`)
  - registered in `db.py` `init_db()` so `create_all` sees the table
  - `repositories/protocols.py` (`DocumentRepository` async Protocol) + `repositories/in_memory.py` (dict-backed test double) + `repositories/document_repo.py` (async SQLModel impl)
  - no Chunk table — chunk text + embeddings live in Qdrant
  - _deferred to a refinement task: a `db-test` compose service + a thin SQLModel integration suite (the in-memory impl carries the contract tests for now)_
- [x] Ingestion pipeline (standalone services behind Protocols, wired via `services/factory.py` into `IngestionService`)
  - `services/adapters/markitdown_parser.py` (markitdown: born-digital PDF + Office + plain text → Markdown; `asyncio.to_thread`; `ParseError` on unsupported extension / empty output)
  - `services/adapters/semchunk_chunker.py` (semchunk: token-budgeted via `tiktoken` cl100k_base; configurable size/overlap; empty input → `[]`)
  - `services/adapters/openrouter_embedder.py` (`openai` SDK → OpenRouter; Qwen3-embedding-8b, 1536 dims, asymmetric `input_type` switch, batched, `EmbeddingError`)
  - `services/adapters/qdrant_vector_store.py` (cosine; payload indexes on `document_id`+`tags`; atomic delete-then-upsert; native tag/document_id filter pushdown; deterministic point ids)
  - `services/ingestion.py` (orchestrator: prepare → parse+hash+dedup+create-as-processing; finalize → chunk+embed+upsert+set-status)
  - Qdrant collection auto-provisioned on startup in the FastAPI lifespan (`main.py`)
  - verified end-to-end via `tests/smoke_ingestion_e2e.py` against compose (db + qdrant)
  - _deferred refinement: scanned-PDF OCR via `markitdown-ocr` (LLM-vision plugin, OpenRouter key)_
- [ ] Document management REST API
  - `schemas/document.py` (upload, list, delete payloads)
  - `endpoints/documents.py` (router under `/api`; upload triggers ingestion)
  - dedup via content hash (re-upload does not duplicate)
  - delete cascades: remove metadata in Postgres + vectors in Qdrant
- [ ] MCP tools (`src/mcp_server.py`)
  - `list_documents`, `list_tags`, `search`, `search_by_tag`, `search_by_document`
  - query-time embeddings use `input_type=search_query` (the embedder switch is already wired)
  - remove the `ping` smoke-test tool once real tools land

## Next steps
1. **Document management REST API** — `schemas/document.py` + `endpoints/documents.py`; upload triggers `IngestionService.ingest` (via `build_ingestion_service` from `app.state.adapters`), list/delete with Qdrant cascade. Dedup via content hash is already handled by `prepare`.
2. **MCP tools** — the five knowledge-base tools over the now-functional ingestion + search. Design input schemas/output shapes from the agent's perspective (documented in the top-level README when they land).
3. **Frontend UI** — upload + tag, list, delete against the REST API.
4. _Refinement_ — scanned-PDF OCR (`markitdown-ocr`), Alembic migrations, REST auth, deployment + demo video.
