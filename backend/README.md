# Backend

FastAPI app serving the REST API, ingestion pipeline, and MCP server (the core of the project).

## Stack
- FastAPI (async), SQLModel, pydantic-settings, asyncpg, PostgreSQL 17
- Qdrant (qdrant-client) for vectors + payload filtering
- FastMCP (`fastmcp`) for the MCP server, mounted at `/mcp`
- markitdown (parser), semchunk (chunker), OpenRouter via `openai` SDK (Qwen3-embedding-8b dense embedder), FastEmbed (BM25 sparse embedder, local), Qdrant (vector store, hybrid dense+sparse via RRF)
- Optional VLM-assisted parsing (`markitdown-ocr` plugin, `google/gemini-3.1-flash-lite` via OpenRouter) gated by `USE_VLM` (default off), model configurable via `VLM_MODEL`
- uv, ruff, ty, pytest

## Tree
```
src/
├── main.py              FastAPI app: CORS, /health, mounts /mcp, combines lifespans
├── mcp_server.py        FastMCP instance + http_app() (path=/, stateless, json) + 5 knowledge-base tools
├── db.py                async engine + session factory + init_db (create_all)
├── core/
│   ├── config.py        Settings (env vars, dev defaults)
│   ├── dependencies.py  DI: get_db, get_adapters/set_adapters, get_document_repo(sitory), get_ingestion_service
│   └── security.py      build_mcp_auth() → StaticTokenVerifier
├── models/              SQLModel tables (Document w/ parsed content + content hash + tags as a Postgres text[] column; no Tag/DocumentTag link, no Chunk table)
├── schemas/             Pydantic request/response schemas
├── endpoints/           FastAPI routers
├── services/            Business logic + ingestion orchestrator + adapters
│   ├── protocols.py     Parser / Chunker / Embedder / SparseEmbedder Protocols
│   ├── ingestion.py     IngestionService (two-phase prepare/finalize, dedup, lifecycle)
│   ├── factory.py       build_adapters() + build_ingestion_service() (wiring)
│   └── adapters/        Concrete impls behind the Protocols
│       ├── markitdown_parser.py   MarkItDown → Markdown (asyncio.to_thread)
│       ├── semchunk_chunker.py    token-budgeted semantic chunking (tiktoken)
│       ├── openrouter_embedder.py Qwen3-embedding-8b, batched, asymmetric input_type
│       ├── fastembed_sparse.py    FastEmbed BM25 sparse embedder (local, off-thread)
│       └── qdrant_vector_store.py Qdrant (named dense+sparse vectors, RRF fusion, payload indexes, filter pushdown)
└── repositories/        Data access (Protocol + SQLModel + in-memory impls)
    ├── protocols.py     DocumentRepository + VectorStore Protocols, ChunkPayload, SearchHit, SparseVector
    ├── document_repo.py async SQLModel DocumentRepository
    └── in_memory.py     dict-backed DocumentRepository + VectorStore (test doubles, RRF-approximated hybrid ranking)
tests/                   shared fakes at the root; tiered by the test pyramid (see sdd/specs/testing.md)
├── unit/                pure unit tests (no external services, no real adapters)
└── integration/         real adapters or full HTTP/MCP stack (need config/env)
```

## Development
```bash
uv sync --dev
uv run uvicorn src.main:app --reload
```

## Backlog

See `../CHANGELOG.md` for v0.1.0.
