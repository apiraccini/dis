# Backend

FastAPI app serving the REST API, ingestion pipeline, and MCP server (the core of the project).

## Stack
- FastAPI (async), SQLModel, pydantic-settings, asyncpg, PostgreSQL 17
- Qdrant (qdrant-client) for vectors + payload filtering
- FastMCP (`fastmcp`) for the MCP server, mounted at `/mcp`
- liteparse (parser), semchunk (chunker); embedder model TBD
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
├── models/              SQLModel tables (Document, Tag, Chunk — backlog)
├── schemas/             Pydantic request/response schemas (backlog)
├── endpoints/           FastAPI routers (backlog)
├── services/            Business logic + ingestion orchestrator (backlog)
│   └── protocols.py     Parser / Chunker / Embedder Protocols
└── repositories/        Data access (Protocol + SQLModel impls — backlog)
tests/
└── test_health.py       /health smoke test
```

## Development
```bash
uv sync --dev
uv run uvicorn src.main:app --reload
```

## Backlog
- [ ] Data models + repositories
  - `models/document.py`, `models/tag.py`, `models/chunk.py` (SQLModel tables)
  - register imports in `db.py` `init_db()` so `create_all` sees them
  - `repositories/` Protocol per domain + async SQLModel impl
- [ ] Document management REST API
  - `schemas/document.py` (upload, list, delete payloads)
  - `endpoints/documents.py` (router under `/api`)
  - upload dedup: re-uploading a document does not create duplicates
- [ ] Ingestion pipeline
  - `services/parser.py` (liteparse: PDF + plain text)
  - `services/chunker.py` (semchunk: semantic chunking with overlap)
  - `services/embedder.py` (OpenAI; decide model in the SDD session, set `EMBEDDING_MODEL`)
  - `services/ingestion.py` (orchestrator: parse → chunk → embed → store in Qdrant + persist metadata in Postgres)
  - Qdrant collection setup (dimension from embedder, payload = document id/name + tags)
- [ ] MCP tools (`src/mcp_server.py`)
  - `list_documents`, `list_tags`, `search`, `search_by_tag`, `search_by_document`
  - remove the `ping` smoke-test tool once real tools land
