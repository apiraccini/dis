# Backend — Document Intelligence Server

## Stack
- FastAPI (async), SQLModel, pydantic-settings, PostgreSQL via asyncpg
- Qdrant for vectors + payload filtering (qdrant-client)
- FastMCP (`fastmcp` package) for the MCP server, mounted at `/mcp` (Streamable HTTP)
- uv for Python management, ruff + ty for lint/types, pytest for tests
- Clean architecture: endpoints → services → repositories (Protocol)
- Ingestion pipeline stages are Protocols (`services/protocols.py`): parser=liteparse, chunker=semchunk, embedder=TBD
- No Alembic: schema via SQLModel.metadata.create_all on startup (documented limitation)
- Auth trimmed: no JWT/login. MCP endpoint gated by a static Bearer token (FastMCP StaticTokenVerifier); REST API is internal to the compose network

## Quick commands
- `cd backend && uv sync --dev`: install deps including dev tools
- `uv run uvicorn src.main:app --reload`: dev server
- `uv run pytest`: tests
- `uv run ruff check src/ tests/`: lint
- `uv run ruff format --check src/ tests/`: format check
- `uv run ty check`: type check

## Rules
- Async everywhere, no sync DB access.
- No business logic in endpoints; call services.
- Repositories expose `typing.Protocol` interfaces for mocking.
- MCP tools are registered on the `mcp` instance in `src/mcp_server.py` with `@mcp.tool`.
- `stateless_http` and `json_response` go on `mcp.http_app(...)`, NOT the FastMCP constructor (PrefectHQ/fastmcp#3618).
- The mounted MCP app needs its lifespan composed into the FastAPI app via `combine_lifespans` (see `src/main.py`).
